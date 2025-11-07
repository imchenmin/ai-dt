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