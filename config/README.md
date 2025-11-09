# 配置文件说明

本目录包含项目的配置文件模板。请根据需要复制并配置相应的文件。

## 配置文件

### 环境变量配置 (.env)

在项目根目录创建 `.env` 文件，配置 API 密钥：

```bash
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Dify API 配置
DIFY_API_KEY=your_dify_api_key_here
DIFY_BASE_URL=your_dify_base_url_here

# 其他配置
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

### API Provider 配置

项目支持多种 LLM API Provider：

#### 1. OpenAI
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

#### 2. DeepSeek
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

#### 3. Dify Web API

Dify 是一个基于 Web 界面的 AI 服务提供商。配置方式：

1. 访问 Dify 平台（如：https://dify.ai）
2. 创建应用并获取 API Key
3. 在 `.env` 文件中配置：
```bash
DIFY_API_KEY=app-xxxxxxxxxxxxxxxx
DIFY_BASE_URL=https://api.dify.ai/v1
```

4. 或者使用应用配置：
```bash
# 在 test_generation.yaml 中配置
providers:
  dify_web:
    type: web
    app_url: "https://your-dify-app-url"
    api_key: "app-xxxxxxxxxxxxxxxx"
```

### 测试生成配置 (test_generation.yaml)

主配置文件 `config/test_generation.yaml` 已预设默认值。如需自定义，可复制并修改：

```yaml
# LLM Provider 配置
llm_provider: "openai"  # 可选: openai, deepseek, dify

# API 配置
api:
  openai:
    base_url: "https://api.openai.com/v1"
    model: "gpt-4"
    max_tokens: 16000
    temperature: 0.7
  deepseek:
    base_url: "https://api.deepseek.com"
    model: "deepseek-coder"
    max_tokens: 16000
    temperature: 0.7
  dify:
    base_url: "your_dify_base_url"
    app_id: "your_app_id"

# 其他配置...
```

## 使用说明

1. **首次使用**：
   ```bash
   # 复制环境变量模板
   cp .env.example .env

   # 编辑 .env 文件，填入你的 API 密钥
   ```

2. **运行测试生成**：
   ```bash
   # 使用 OpenAI
   python -m src.main --config simple_c

   # 使用 DeepSeek
   DEEPSEEK_API_KEY=your_key python -m src.main --config simple_c

   # 使用 Dify
   DIFY_API_KEY=your_key python -m src.main --config simple_c
   ```

## 注意事项

- **安全性**：`.env` 文件已添加到 `.gitignore`，不会提交到仓库
- **备份**：请妥善保管你的 API 密钥
- **共享配置**：如需团队共享配置，请创建示例文件（如 `config.example.yaml`）

## 故障排除

1. **API 密钥错误**：
   - 检查 `.env` 文件中的密钥是否正确
   - 确认 API 密钥有足够的权限和余额

2. **连接超时**：
   - 检查网络连接
   - 考虑使用代理（设置 `HTTPS_PROXY` 环境变量）

3. **配置文件找不到**：
   - 确保在项目根目录运行命令
   - 检查配置文件路径是否正确

### 编译修复配置 (compile_fix.yaml)

用于 `src.debug_tool.cli.compile_fix` 的全量可配置选项，支持通过 YAML 配置复用所有参数，CLI 参数优先级最高。

示例：

```yaml
debug_tool:
  compile_fix:
    # IO 路径
    input_text: "experiment/deepseek_generated_tests/3_pure_tests/combined.txt"
    target_file: "test_projects/fix_bugs_project/tests/generated_suite.cpp"
    project_root: "test_projects/fix_bugs_project"
    build_dir: "test_projects/fix_bugs_project/build"
    audit_dir: "experiment/compile_fix_logs"

    # 构建与运行
    error_prefix: "generated_suite.cpp"
    cmake_target: "generated_suite"
    run_tests: true
    max_iterations: 10

    # 命令自定义（可选）——支持变种指令与过滤指令
    cmake_command: null              # 覆盖 cmake 可执行文件（路径或包装脚本）
    cmake_configure_args: null       # 自定义 configure 阶段参数
    cmake_build_args: null           # 自定义 build 阶段参数（如使用非标准构建流程时必须提供）

    ctest_command: null              # 覆盖 ctest 可执行文件（路径或包装脚本）
    ctest_args: ["--output-on-failure"]
    ctest_regex: null                # 包含过滤，传递给 ctest '-R'
    ctest_exclude_regex: null        # 排除过滤，传递给 ctest '-E'
    ctest_workdir: null              # 运行 ctest 的工作目录（默认使用 build_dir）

    # 黑名单来源（可选）
    blacklist_file: null
    blacklist:
      - "MOCKER("
      - "mock_variadic"
      - "ON_CALL("
      - "EXPECT_CALL("
```

键说明：
- `input_text`: 聚合测试文本路径（必需）
- `target_file`: 目标 `.cpp` 文件路径（必需）
- `project_root`: CMake 项目根目录（必需）
- `build_dir`: CMake 构建目录（必需）
- `audit_dir`: 审计日志目录，记录预处理、黑名单删除、编译错误和运行失败解析
- `error_prefix`: 编译错误过滤前缀（通常为目标文件名），只处理相关错误
- `cmake_target`: 可选的构建目标名（如 `generated_suite`）
- `run_tests`: 构建成功后是否运行 `ctest` 并删除失败用例
- `max_iterations`: 编译修复迭代次数上限
- `blacklist_file`: 文本文件，一行一个模式，支持 `#` 与 `//` 注释
- `blacklist`: YAML 列表形式的黑名单模式
\- `cmake_command`: 覆盖默认的 `cmake` 执行器（允许自定义路径或包装器）。默认使用 `cmake`
\- `cmake_configure_args`: 覆盖 `cmake` 配置阶段参数。若未提供，使用 `-S <project_root> -B <build_dir>`
\- `cmake_build_args`: 覆盖构建阶段参数。若未提供，默认执行 `cmake --build <build_dir> [--target <cmake_target>]`
\- `ctest_command`: 覆盖默认的 `ctest` 执行器。默认使用 `ctest`
\- `ctest_args`: 传递给 `ctest` 的附加参数。默认 `--output-on-failure`
\- `ctest_regex`: 测试包含过滤，传递给 `ctest -R`
\- `ctest_exclude_regex`: 测试排除过滤，传递给 `ctest -E`
\- `ctest_workdir`: 运行 `ctest` 的工作目录；不设置时默认使用 `build_dir`

黑名单合并策略：
- 最终黑名单 = CLI `--blacklist` + 文本文件 + YAML 配置，去重后使用
- 文本文件来源优先级：显式 `--blacklist-file` 高于配置中的 `blacklist_file`
- YAML 黑名单来源优先级：显式 `--blacklist-config` 高于主配置 `--config` 路径；若未指定则从 `--config` 中读取

配置加载优先级：
- CLI 参数 > 配置文件值 > 默认值
- 配置文件路径：优先使用 CLI `--config`；若未提供，支持环境变量 `COMPILE_FIX_CONFIG`；否则默认 `config/compile_fix.yaml`

运行示例：
- 使用配置文件：
  - `python -m src.debug_tool.cli.compile_fix --config config/compile_fix.yaml`
  - 自定义构建：`python -m src.debug_tool.cli.compile_fix --config config/compile_fix.yaml --cmake-build-args --build test_projects/fix_bugs_project/build --target generated_suite`
  - 过滤运行：`python -m src.debug_tool.cli.compile_fix --config config/compile_fix.yaml --ctest-regex GeneratedSuite --ctest-exclude-regex Skip.*`
- 使用环境变量指定配置：
  - `COMPILE_FIX_CONFIG=config/compile_fix.yaml python -m src.debug_tool.cli.compile_fix`
- 指定额外黑名单文本文件：
  - `python -m src.debug_tool.cli.compile_fix --config config/compile_fix.yaml --blacklist-file path/to/blacklist.txt`

审计日志：
- 详见 `experiment/compile_fix_logs` 下生成的日志文件，记录：预处理输入/目标路径、黑名单删除、编译错误迭代、运行失败删除等。