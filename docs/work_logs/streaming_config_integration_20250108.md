# Streaming Mode与Config配置整合优化

## 2025-01-08 优化记录

### 问题分析

之前的代码中，streaming mode存在以下限制：

1. **无法使用配置文件**：streaming mode只能通过命令行参数指定项目路径，无法使用config/test_generation.yaml中预定义的项目配置
2. **配置隔离**：streaming mode的配置与config系统完全分离，无法利用已有的项目配置
3. **使用不便**：每次运行都需要手动输入完整的路径和参数

### 优化方案

#### 1. 新增命令行参数

在main.py中添加了以下支持：

- `--streaming [PROJECT_NAME]`：支持指定配置文件中的项目名
- `--max-concurrent`：最大并发LLM调用数
- `--progress`：启用进度报告
- `--force-streaming`：强制使用streaming架构

#### 2. 配置整合

streaming mode现在可以：

- 使用config文件中的项目配置（路径、编译数据库等）
- 应用profile配置（quick、comprehensive、streaming等）
- 继承全局streaming配置
- 通过命令行参数覆盖配置文件设置

#### 3. 向后兼容

保留了原有的使用方式：
```bash
python -m src.main --streaming --project /path/to/project
```

### 使用示例

#### 1. 使用配置文件中的项目（推荐）
```bash
# 列出可用项目
python -m src.main --list-projects

# 使用配置文件中的complex_c_project
python -m src.main --streaming complex_c_project

# 使用streaming profile
python -m src.main --streaming complex_c_project --profile streaming

# 自定义并发数和启用进度报告
python -m src.main --streaming complex_c_project --max-concurrent 5 --progress
```

#### 2. 传统方式（向后兼容）
```bash
python -m src.main --streaming --project ./test_projects/c --max-concurrent 3 --progress
```

### 配置文件支持

#### 项目配置示例
```yaml
projects:
  complex_c_project:
    path: "test_projects/complex_c_project"
    comp_db: "test_projects/complex_c_project/compile_commands.json"
    output_dir: "./experiment/generated_tests_complex_c"
    llm_provider: "deepseek"
    model: "deepseek-chat"
```

#### Streaming配置示例
```yaml
streaming:
  enabled: true
  pipeline:
    max_concurrent_llm_calls: 3
    timeout_seconds: 300
    retry_attempts: 3
```

#### Profile配置示例
```yaml
profiles:
  streaming:
    description: "Streaming architecture profile for large projects"
    use_streaming: true
    max_functions: null
    timeout: 7200
    streaming:
      pipeline:
        max_concurrent_llm_calls: 5
        timeout_seconds: 600
```

### 技术实现

1. **参数解析**：通过nargs='?'实现可选的项目名参数
2. **配置合并**：按优先级合并配置（命令行 > profile > project > defaults）
3. **异步调用**：使用asyncio.run调用streaming mode的异步函数
4. **配置传递**：通过**config_overrides将配置传递给streaming service

### 优势

1. **简化使用**：无需记住具体路径，只需项目名
2. **配置复用**：充分利用已有的配置文件
3. **灵活性**：支持配置文件和命令行参数的组合使用
4. **向后兼容**：不破坏现有使用方式