## 自动运行与自愈功能需求与设计

### 背景与目标
- 在生成 C/C++ 单元测试后，需要立即验证其可编译与可运行性，减少人工介入成本。
- 尤其针对编译失败的测试用例，引入有限次数的自动修复机制，提高生成成功率。
- 保证失败时能够恢复工作区到生成前的状态，避免污染已有测试工程与版本库。

### 功能需求概述
- **自动运行**：在 `TestGenerationOrchestrator.generate_tests` 成功生成测试代码后立即触发编译/运行脚本。
- **自愈重试**：对于失败的编译或测试运行，允许配置的重试次数（默认 3 次），每次通过 LLM 生成补丁并自动应用。
- **安全回滚**：若所有尝试均失败，需要恢复测试文件到生成前状态，确保工作区一致性。
- **审计记录**：完整记录自动运行、修复尝试、回滚信息，便于后续分析。

### 配置项扩展（`config/test_generation.yaml`）
- `auto_run_enabled`：布尔值，控制是否开启自动运行。默认 `false`。
- `test_command`：字符串，指向编译并执行单元测试的脚本（如 `bash scripts/run_generated_tests.sh`）。
- `max_fix_attempts`：整数，最大自愈次数，默认 `2`。
- `rollback_strategy`：枚举，`restore_snapshot`（默认）/`git_checkout`/`manual`。
- `log_dir`：字符串，自动运行日志输出目录（默认 `test_output/auto_run_logs`）。
- `fix_prompt_template`：字符串，可选，LLM 自愈提示词模板路径。

### 模块设计

```mermaid
flowchart TD
    A[GenerationResult (success)] --> B{auto_run_enabled?}
    B -- 否 --> C[直接返回结果]
    B -- 是 --> D[WorkspaceSnapshotter 备份]
    D --> E[TestRunner 执行 test_command]
    E -->|成功| F[记录 PASS, 清理快照]
    E -->|失败| G[FailureAnalyzer 解析错误]
    G --> H{FixAttempt 次数 < max?}
    H -- 否 --> I[RollbackManager 恢复文件]
    H -- 是 --> J[FixAttemptManager 触发 LLM 修复]
    J --> K[PatchApplier 更新测试文件]
    K --> L[重新运行 test_command]
```

- **AutoTestCoordinator**：对外协调接口，贯穿快照、执行、自愈与回滚，返回结构化的 `AutoRunReport`。
- **WorkspaceSnapshotter**：保存目标测试文件及相关输出，用于失败后的恢复。
- **TestRunner**：执行 `test_command`，捕获退出码、stdout/stderr，并判断编译/运行是否成功。
- **FailureAnalyzer**：解析编译或运行日志，提取错误类型、文件、行号等信息。
- **FixAttemptManager**：构建自愈提示词，调用 `LLMClient` 生成补丁，并应用到生成的测试文件。
- **RollbackManager**：根据策略恢复文件，默认使用快照覆盖，还可扩展 git 回滚。
- **AutoRunReporter**：将自动运行结果写入 JSON/Markdown，位于 `log_dir`。

### 集成方案
- 在 `TestGenerationOrchestrator._execute_generation` (`src/test_generation/orchestrator.py:166`) 的 `process_task` 中，成功生成测试并持久化后调用：
  ```python
  if config.auto_run_enabled and result.success:
      report = self.auto_runner.run_with_fix(result, config)
      result.metadata['auto_run'] = report.to_dict()
  ```
- `TestGenerationOrchestrator.__init__` 支持注入自定义 `auto_runner` 以便测试。
- `TestResultAggregator` 追加 auto-run 成功/失败统计字段。

### 伪代码
```python
class AutoTestCoordinator:
    def run_with_fix(self, result, config):
        snapshot = self.snapshotter.create_snapshot(result.task.target_filepath)
        attempts = 0
        reports = []
        while attempts <= config.max_fix_attempts:
            run_report = self.test_runner.run(config.test_command)
            reports.append(run_report)
            if run_report.success:
                snapshot.cleanup()
                return AutoRunReport(success=True, attempts=attempts, runs=reports)

            if attempts == config.max_fix_attempts:
                self.rollback(snapshot)
                return AutoRunReport(success=False, attempts=attempts, runs=reports, rolled_back=True)

            fix_input = FixContext(result, run_report, snapshot)
            patch = self.fix_manager.generate_patch(fix_input)
            if not patch or patch.is_noop():
                break

            self.patch_applier.apply(patch, result.task.target_filepath)
            attempts += 1

        self.rollback(snapshot)
        return AutoRunReport(success=False, attempts=attempts, runs=reports, rolled_back=True)
```

### 自愈策略
- 提示词包括：目标函数摘要（`GenerationTask.function_info`）、测试代码全文、编译/运行日志（截断至最近 200 行）。
- 强制限制修改范围：仅允许编辑当前测试文件。
- 若连续两次出现相同的错误摘要，提前终止自愈循环。
- 补丁应用使用统一 `PatchApplier`，失败时立即回滚。

### 日志与回滚
- `AutoRunReport` 字段：
  - `status`、`attempts`、`runs`（含 `command`、`exit_code`、`stdout_tail`、`stderr_tail`）
  - `fixes`（补丁摘要、LLM 模型、token 消耗）
  - `rollback`
  - `timestamp`
- 以 JSON + Markdown 形式写入 `log_dir/<function_name>.{json,md}`。
- 回滚优先使用快照覆盖；若选择 git 策略，需要确保工作区干净。

### 测试计划
- **单元测试**：
  - `WorkspaceSnapshotter` 快照/恢复
  - `FailureAnalyzer` 日志解析
  - `FixAttemptManager` 提示词构建与 patch 应用
- **集成测试**：
  - 模拟编译失败→一次修复成功
  - 模拟修复失败→回滚
  - 验证 `AutoRunReport` 日志输出与统计字段

### 后续扩展
- 支持并发环境下的队列化 auto-run，防止同时调用编译脚本。
- 结合历史失败日志，实现相似错误的快速绕过或提示人工处理。
- 引入 metrics 上报（如 Prometheus）监控自动修复成功率。
