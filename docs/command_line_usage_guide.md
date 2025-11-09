# AI-DT 命令行使用指南

## 概述

AI-DT 提供了多种运行模式，支持不同的使用场景：从快速测试单个文件到大规模项目的并发测试生成。

## 运行模式

### 1. Simple 模式（`--simple`）
适用于快速测试，无需配置文件。

```bash
# 基本用法
python -m src.main --simple --project /path/to/your/project

# 指定输出目录
python -m src.main --simple --project /path/to/project -o ./output

# 使用文件过滤
python -m src.main --simple --project /path/to/project --include src/core/ --include src/utils/
```

**特点：**
- 无需配置文件
- 直接指定项目路径
- 适合快速原型和测试

### 2. Config 模式（`--config`）
使用预定义的项目配置，采用标准架构。

```bash
# 列出所有可用项目
python -m src.main --list-projects

# 使用配置文件中的项目
python -m src.main --config complex_c_project

# 使用不同的执行profile
python -m src.main --config complex_c_project --profile quick
python -m src.main --config complex_c_project --profile comprehensive

# 自定义配置文件路径
python -m src.main --config my_project --config-file ./my_config.yaml
```

**特点：**
- 使用 config/test_generation.yaml 中的预定义配置
- 项目配置可以复用
- 支持不同的执行策略（profile）

### 3. Streaming 模式（`--streaming`）
高性能流式架构，适用于大型项目。

```bash
# 使用配置文件中的项目（推荐）
python -m src.main --streaming complex_c_project

# 启用进度报告
python -m src.main --streaming complex_c_project --progress

# 自定义并发数
python -m src.main --streaming complex_c_project --max-concurrent 5

# 组合使用
python -m src.main --streaming large_project --progress --max-concurrent 10

# 传统方式（向后兼容）
python -m src.main --streaming --project /path/to/project
```

**特点：**
- 流水线架构，高并发处理
- 实时进度报告
- 内存优化，适合大型项目
- 自动错误隔离和恢复

### 4. Single File 模式（`--single-file`）
专注于单个文件的测试生成。

```bash
# 测试单个文件
python -m src.main --single-file src/core/main.c --project /path/to/project

# 只生成提示词（不调用LLM）
python -m src.main --single-file src/core/main.c --project /path/to/project --prompt-only
```

### 5. API Server 模式（`--api-server`）
将LLM客户端暴露为OpenAI兼容的API服务。

```bash
# 启动API服务器
python -m src.main --api-server

# 自定义主机和端口
python -m src.main --api-server --host 0.0.0.0 --port 8080

# 使用不同的LLM提供商
python -m src.main --api-server --provider deepseek

# 开发模式（自动重载）
python -m src.main --api-server --reload
```

## 通用参数

所有模式都支持以下参数（在适用时）：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config-file` | 配置文件路径 | `config/test_generation.yaml` |
| `--profile` | 执行策略 | `comprehensive` |
| `--prompt-only` | 只生成提示词 | False |

### Streaming 模式专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max-concurrent` | 最大并发LLM调用数 | 3 |
| `--progress` | 启用实时进度报告 | False |
| `--force-streaming` | 强制使用流式架构 | False |

## 执行策略（Profiles）

### Quick
- `max_functions`: 3
- `test_cases_per_function`: 3
- `max_workers`: 1
- 适合快速验证和小规模测试

### Comprehensive
- `max_functions`: 20
- `test_cases_per_function`: 10
- `max_workers`: 3
- 平衡覆盖率和性能

### Streaming
- 专为流式架构优化
- 支持无限函数数量
- 高并发处理
- 适合大型项目

### Custom
- 完全自定义配置
- 无限制
- 最高并发数

## 配置文件结构

```yaml
# config/test_generation.yaml
projects:
  my_project:
    path: "/path/to/project"
    comp_db: "compile_commands.json"
    description: "My project"
    llm_provider: "deepseek"
    model: "deepseek-chat"
    output_dir: "./generated_tests"

profiles:
  quick:
    description: "Quick test generation"
    max_functions: 3
    timeout: 300

  streaming:
    description: "Streaming architecture profile"
    use_streaming: true
    streaming:
      pipeline:
        max_concurrent_llm_calls: 5
        timeout_seconds: 600
```

## 使用建议

### 小型项目（< 10个函数）
```bash
python -m src.main --config your_project --profile quick
```

### 中型项目（10-50个函数）
```bash
python -m src.main --config your_project --profile comprehensive
```

### 大型项目（> 50个函数）
```bash
python -m src.main --streaming your_project --progress --max-concurrent 5
```

### 超大型项目（> 200个函数）
```bash
python -m src.main --streaming your_project --progress --max-concurrent 10 --profile streaming
```

### 调试和开发
```bash
# 快速验证
python -m src.main --single-file src/utils.c --project . --prompt-only

# 查看可用项目
python -m src.main --list-projects

# 测试配置
python -m src.main --simple --project ./test_project
```

## 常见问题

### Q: 什么时候使用 streaming 模式？
A: 项目包含超过50个函数，或者需要快速生成大量测试用例时。

### Q: config 和 streaming 模式有什么区别？
A:
- `--config` 使用标准架构，适合中小型项目
- `--streaming` 使用流式架构，专为大型项目优化

### Q: 如何选择合适的 profile？
A:
- `quick`: 快速验证，CI/CD集成
- `comprehensive`: 日常开发，平衡性能
- `streaming`: 大型项目，高性能
- `custom`: 完全自定义需求

### Q: 如何提高测试生成速度？
A:
1. 使用 `--streaming` 模式
2. 增加 `--max-concurrent` 值（不超过API限制）
3. 选择合适的 `--profile`
4. 使用 `--include` 过滤不需要的文件

## 示例工作流

### 1. 新项目设置
```bash
# 1. 查看现有项目
python -m src.main --list-projects

# 2. 快速测试
python -m src.main --simple --project ./new_project --max-concurrent 1

# 3. 添加到配置文件
# 编辑 config/test_generation.yaml，添加新项目配置

# 4. 使用配置文件运行
python -m src.main --config new_project
```

### 2. 大型项目迁移
```bash
# 1. 先用 small 测试
python -m src.main --streaming large_project --max-concurrent 2 --progress

# 2. 查看结果，调整参数
python -m src.main --streaming large_project --max-concurrent 5 --progress

# 3. 正式运行
python -m src.main --streaming large_project --profile streaming --progress
```

### 3. CI/CD 集成
```bash
# 使用 quick profile 进行快速检查
python -m src.main --config project --profile quick

# 或使用 prompt-only 验证配置
python -m src.main --config project --prompt-only
```