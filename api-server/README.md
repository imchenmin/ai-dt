# AI-DT API Server

基于dify-web功能的独立API服务器，提供OpenAI兼容的API接口。

## 功能特性

- 🚀 **OpenAI兼容API**: 完全兼容OpenAI Chat Completions API格式
- 📁 **Curl文件支持**: 支持通过curl文件配置不同的LLM提供商
- 🔄 **动态配置管理**: 支持运行时添加、删除和管理curl配置
- 📊 **流式响应**: 支持流式和非流式两种响应模式
- 🛡️ **健康检查**: 提供健康检查和状态监控端点
- 📖 **自动文档**: 自动生成API文档

## 快速开始

### 1. 启动服务器

**Linux/macOS:**
```bash
./start_server.sh
```

**Windows:**
```cmd
start_server.bat
```

### 2. 访问服务

- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## API端点

### OpenAI兼容端点

#### 聊天完成 (Chat Completions)
```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "model": "sample_dify",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "max_tokens": 2000,
  "temperature": 0.7,
  "stream": false
}
```

#### 列出模型
```http
GET /v1/models
```

### 管理端点

#### 添加Curl配置
```http
POST /admin/curl-configs
Content-Type: application/json

{
  "model_name": "my_model",
  "curl_content": "curl 'https://api.example.com/chat' -H 'Authorization: Bearer token' --data '{\"query\":\"test\"}'",
  "description": "我的自定义模型"
}
```

#### 列出所有配置
```http
GET /admin/curl-configs
```

#### 获取特定配置
```http
GET /admin/curl-configs/{model_name}
```

#### 删除配置
```http
DELETE /admin/curl-configs/{model_name}
```

## 使用示例

### 1. 添加Dify配置

首先，将你的dify curl命令保存为配置：

```bash
curl -X POST http://localhost:8000/admin/curl-configs \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "my_dify_model",
    "curl_content": "curl '"'"'https://udify.app/api/chat-messages'"'"' -H '"'"'authorization: Bearer YOUR_TOKEN'"'"' -H '"'"'content-type: application/json'"'"' --data-raw '"'"'{\"response_mode\":\"streaming\",\"conversation_id\":\"\",\"files\":[],\"query\":\"测试\",\"inputs\":{},\"parent_message_id\":null}'"'"'",
    "description": "我的Dify模型配置"
  }'
```

### 2. 使用OpenAI客户端

```python
import openai

# 配置客户端
client = openai.OpenAI(
    api_key="dummy",  # 可以是任意值
    base_url="http://localhost:8000/v1"
)

# 发送聊天请求
response = client.chat.completions.create(
    model="my_dify_model",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    max_tokens=2000,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### 3. 流式响应

```python
response = client.chat.completions.create(
    model="my_dify_model",
    messages=[
        {"role": "user", "content": "写一首关于春天的诗"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## 配置文件格式

Curl配置文件应该包含完整的curl命令，例如：

```bash
curl 'https://api.example.com/chat' \
  -H 'Authorization: Bearer your-token' \
  -H 'Content-Type: application/json' \
  --data-raw '{"query":"{{QUERY}}","stream":true}'
```

**注意**: 
- 系统会自动替换请求体中的查询内容
- 支持流式和非流式响应
- 配置文件保存在 `config/` 目录下

## 环境要求

- Python 3.8+
- FastAPI
- Uvicorn
- 项目依赖 (自动安装)

## 目录结构

```
api-server/
├── app.py              # 主应用文件
├── requirements.txt    # Python依赖
├── start_server.sh     # Linux/macOS启动脚本
├── start_server.bat    # Windows启动脚本
├── README.md          # 说明文档
└── venv/              # 虚拟环境 (自动创建)
```

## 故障排除

### 1. 端口被占用
如果8000端口被占用，可以修改启动脚本中的端口号：
```bash
python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### 2. 依赖安装失败
确保Python版本为3.8+，并且网络连接正常：
```bash
python3 --version
pip install --upgrade pip
```

### 3. Curl配置不工作
检查curl命令格式是否正确，确保包含必要的请求头和数据格式。

## 开发说明

本API服务器基于项目现有的LLM集成系统构建，重用了以下组件：
- `src.llm.client.LLMClient`: 统一LLM客户端
- `src.llm.providers.DifyWebProvider`: Dify Web提供商
- `src.utils.config_manager.ConfigManager`: 配置管理器

如需扩展功能，可以修改 `app.py` 文件或添加新的提供商实现。