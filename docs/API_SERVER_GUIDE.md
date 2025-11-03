# AI-DT LLM API 服务器使用指南

## 概述

AI-DT LLM API 服务器提供了一个 OpenAI 兼容的 REST API 接口，支持多种 LLM 提供者，包括 OpenAI、DeepSeek、Anthropic、Dify 和 Dify Web 等。

## 目录

- [快速开始](#快速开始)
- [服务器启动方式](#服务器启动方式)
- [支持的提供者](#支持的提供者)
- [API 端点详细说明](#api-端点详细说明)
- [API 调用测试](#api-调用测试)
- [配置说明](#配置说明)
- [错误处理](#错误处理)
- [故障排除](#故障排除)
- [集成到其他应用](#集成到其他应用)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
# 使用默认配置启动（OpenAI 提供者）
python -m src.main --api-server

# 指定提供者启动
python -m src.main --api-server --provider dify_web
```

### 3. 测试 API

```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 150
  }'
```

## 服务器启动方式

### 基本启动命令

```bash
python -m src.main --api-server [OPTIONS]
```

### 启动参数

| 参数 | 描述 | 默认值 | 示例 |
|------|------|--------|------|
| `--host` | 服务器绑定的主机地址 | `0.0.0.0` | `--host 127.0.0.1` |
| `--port` | 服务器监听端口 | `8000` | `--port 8080` |
| `--provider` | 默认 LLM 提供者 | `openai` | `--provider dify_web` |
| `--reload` | 开发模式（代码变更自动重载） | `False` | `--reload` |

### 启动示例

#### 1. 开发模式启动
```bash
python -m src.main --api-server --host 127.0.0.1 --port 8000 --reload
```

#### 2. 生产模式启动
```bash
python -m src.main --api-server --host 0.0.0.0 --port 8000 --provider openai
```

#### 3. 指定端口启动
```bash
python -m src.main --api-server --port 8080
```

## 支持的提供者

### 1. OpenAI

**环境变量配置：**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**启动命令：**
```bash
python -m src.main --api-server --provider openai
```

**支持的模型：**
- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4-turbo`

### 2. DeepSeek

**环境变量配置：**
```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

**启动命令：**
```bash
python -m src.main --api-server --provider deepseek
```

**支持的模型：**
- `deepseek-chat`
- `deepseek-coder`

### 3. Anthropic

**环境变量配置：**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**启动命令：**
```bash
python -m src.main --api-server --provider anthropic
```

**支持的模型：**
- `claude-3-opus`
- `claude-3-sonnet`
- `claude-3-haiku`

### 4. Dify

**环境变量配置：**
```bash
export DIFY_API_KEY="your-dify-api-key"
```

**启动命令：**
```bash
python -m src.main --api-server --provider dify
```

**支持的模型：**
- `dify-model`

### 5. Dify Web

**环境变量配置：**
```bash
export DIFY_CURL_FILE_PATH="/path/to/your/dify.curl"
```

**启动命令：**
```bash
DIFY_CURL_FILE_PATH="/Users/chenmin/Develop/ai-dt/config/sample_dify.curl" \
python -m src.main --api-server --provider dify_web --host 127.0.0.1 --port 8000
```

**支持的模型：**
- `dify_web_model`

**curl 文件示例：**
```bash
# config/sample_dify.curl
curl 'https://your-dify-instance.com/v1/chat-messages' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-token' \
  --data-raw '{
    "inputs": {},
    "query": "{{QUERY}}",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "user-123"
  }'
```

## API 端点详细说明

### 1. 根端点

```bash
GET /
```

返回服务器基本信息和状态。

### 2. 列出可用模型

```bash
GET /v1/models
```

返回所有可用的模型列表。

### 3. 聊天完成 (Chat Completions)

```bash
POST /v1/chat/completions
```

OpenAI 兼容的聊天完成接口。

**请求示例:**

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a simple hello world function in C."}
  ],
  "max_tokens": 150,
  "temperature": 0.3
}
```

**响应示例:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677610602,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 25,
    "total_tokens": 45
  }
}
```

### 4. 文本完成 (Text Completions)

```bash
POST /v1/completions
```

OpenAI 兼容的文本完成接口。

**请求示例:**

```json
{
  "model": "gpt-3.5-turbo",
  "prompt": "Write a simple C function that adds two numbers:",
  "max_tokens": 100,
  "temperature": 0.3
}
```

## API 调用测试

### 1. 使用 curl 测试

#### 聊天完成接口
```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "你好，请介绍一下你自己"
      }
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

#### 文本完成接口
```bash
curl -X POST "http://127.0.0.1:8000/v1/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "写一个 Python 函数来计算斐波那契数列",
    "max_tokens": 200,
    "temperature": 0.5
  }'
```

#### 获取模型列表
```bash
curl -X GET "http://127.0.0.1:8000/v1/models" \
  -H "Authorization: Bearer test-key"
```

#### 健康检查
```bash
curl -X GET "http://127.0.0.1:8000/"
```

### 2. 使用 Python requests 测试

```python
import requests
import json

# API 基础配置
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-key"
}

# 聊天完成测试
def test_chat_completion():
    url = f"{BASE_URL}/v1/chat/completions"
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

# 文本完成测试
def test_text_completion():
    url = f"{BASE_URL}/v1/completions"
    data = {
        "model": "gpt-3.5-turbo",
        "prompt": "写一个 Python 函数来计算斐波那契数列",
        "max_tokens": 200,
        "temperature": 0.5
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

# 获取模型列表测试
def test_list_models():
    url = f"{BASE_URL}/v1/models"
    response = requests.get(url, headers=HEADERS)
    print(f"状态码: {response.status_code}")
    print(f"可用模型: {response.json()}")

if __name__ == "__main__":
    test_chat_completion()
    test_text_completion()
    test_list_models()
```

### 3. 使用 OpenAI Python 客户端测试

```python
from openai import OpenAI

# 创建客户端
client = OpenAI(
    api_key="test-key",
    base_url="http://127.0.0.1:8000/v1"
)

# 聊天完成测试
def test_openai_chat():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "你好，请介绍一下你自己"}
            ],
            max_tokens=150,
            temperature=0.7
        )
        print("聊天完成成功:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"聊天完成失败: {e}")

# 文本完成测试
def test_openai_completion():
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo",
            prompt="写一个 Python 函数来计算斐波那契数列",
            max_tokens=200,
            temperature=0.5
        )
        print("文本完成成功:")
        print(response.choices[0].text)
    except Exception as e:
        print(f"文本完成失败: {e}")

if __name__ == "__main__":
    test_openai_chat()
    test_openai_completion()
```

### 4. 使用测试脚本

项目提供了一个测试脚本 `test_api_client.py`：

```bash
# 启动服务器后运行测试脚本
python test_api_client.py

# 指定服务器地址运行测试
python test_api_client.py --url http://localhost:8000
```

### 5. 完整测试脚本示例

创建一个完整的测试脚本来验证所有 API 功能：

```python
#!/usr/bin/env python3
"""
AI-DT LLM API 测试脚本
"""
import requests
import json
from openai import OpenAI

# API 基础配置
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-key"
}

def test_health_check():
    """测试健康检查端点"""
    print("=== 测试健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_list_models():
    """测试获取模型列表"""
    print("\n=== 测试模型列表 ===")
    try:
        response = requests.get(f"{BASE_URL}/v1/models", headers=HEADERS)
        print(f"状态码: {response.status_code}")
        models = response.json()
        print(f"可用模型: {json.dumps(models, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        return False

def test_chat_completion():
    """测试聊天完成接口"""
    print("\n=== 测试聊天完成 ===")
    try:
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "你好，请介绍一下你自己"}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(f"{BASE_URL}/v1/chat/completions", 
                               headers=HEADERS, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"聊天完成测试失败: {e}")
        return False

def test_text_completion():
    """测试文本完成接口"""
    print("\n=== 测试文本完成 ===")
    try:
        data = {
            "model": "gpt-3.5-turbo",
            "prompt": "写一个 Python 函数来计算斐波那契数列",
            "max_tokens": 200,
            "temperature": 0.5
        }
        
        response = requests.post(f"{BASE_URL}/v1/completions", 
                               headers=HEADERS, json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"文本完成测试失败: {e}")
        return False

def test_openai_client():
    """测试 OpenAI 客户端兼容性"""
    print("\n=== 测试 OpenAI 客户端兼容性 ===")
    try:
        client = OpenAI(
            api_key="test-key",
            base_url=f"{BASE_URL}/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, world!"}
            ],
            max_tokens=50
        )
        
        print("OpenAI 客户端测试成功:")
        print(f"响应: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"OpenAI 客户端测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始 AI-DT LLM API 测试...")
    
    tests = [
        test_health_check,
        test_list_models,
        test_chat_completion,
        test_text_completion,
        test_openai_client
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查服务器配置")

if __name__ == "__main__":
    main()
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-...` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | `sk-ant-...` |
| `DIFY_API_KEY` | Dify API 密钥 | `app-...` |
| `DIFY_CURL_FILE_PATH` | Dify Web curl 文件路径 | `/path/to/dify.curl` |

### 配置文件

配置文件位于 `config/test_generation.yaml`，包含所有提供者的详细配置。

## 错误处理

API 返回标准的 HTTP 状态码和错误信息：

- `400`: 请求参数错误
- `401`: 认证失败
- `404`: 资源不存在
- `500`: 服务器内部错误

错误响应格式：

```json
{
  "error": {
    "message": "错误描述",
    "type": "error_type",
    "code": "error_code"
  }
}
```

## 集成到其他应用

由于 API 完全兼容 OpenAI 格式，可以轻松集成到任何支持 OpenAI API 的应用中，只需要修改 `base_url` 指向本地服务器即可。

### 集成示例

#### 1. 替换现有 OpenAI 客户端

```python
from openai import OpenAI

# 原来的配置
# client = OpenAI(api_key="sk-...")

# 新的配置（指向本地服务器）
client = OpenAI(
    api_key="dummy-key",  # 本地服务器不需要真实密钥
    base_url="http://localhost:8000/v1"
)
```

#### 2. 在配置文件中设置

```yaml
# config.yaml
llm:
  provider: "local"
  api_key: "dummy-key"
  base_url: "http://localhost:8000/v1"
  model: "gpt-3.5-turbo"
```

#### 3. 环境变量配置

```bash
export OPENAI_API_KEY="dummy-key"
export OPENAI_BASE_URL="http://localhost:8000/v1"
```

### 注意事项

1. 确保安装了必要的依赖：`pip install fastapi uvicorn`
2. 配置正确的 LLM 提供商 API 密钥
3. 在生产环境中，建议使用反向代理 (如 nginx) 和 HTTPS
4. API 服务器支持 CORS，可以从浏览器直接调用
5. 本地服务器通常不需要真实的 API 密钥，可以使用任意字符串

## 故障排除

### 常见问题

#### 1. API 密钥错误
```
错误: API key required for provider: openai
解决: 设置正确的环境变量，如 export OPENAI_API_KEY="your-key"
```

#### 2. 端口被占用
```
错误: [Errno 48] Address already in use
解决: 使用不同端口启动，如 --port 8001
```

#### 3. curl_file_path 错误（dify_web）
```
错误: curl_file_path required for provider: dify_web
解决: 设置 DIFY_CURL_FILE_PATH 环境变量指向有效的 curl 文件
```

#### 4. 模型不支持
```
错误: Model not supported
解决: 检查模型名称是否正确，参考支持的模型列表
```

### 调试技巧

#### 1. 启用详细日志
```bash
# 设置日志级别为 DEBUG
export LOG_LEVEL=DEBUG
python -m src.main --api-server --reload
```

#### 2. 检查服务器状态
```bash
# 检查服务器是否正常运行
curl http://127.0.0.1:8000/
```

#### 3. 验证环境变量
```bash
# 检查环境变量是否设置
echo $OPENAI_API_KEY
echo $DIFY_CURL_FILE_PATH
```

### 性能优化

#### 1. 生产环境配置
```bash
# 使用多个工作进程
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 2. 缓存配置
服务器自动缓存 LLM 客户端实例，减少重复初始化开销。

#### 3. 超时设置
默认请求超时为 300 秒，可在配置文件中调整。

## 更多信息

- 项目主页: [AI-DT GitHub](https://github.com/your-repo/ai-dt)
- 配置参考: 查看 `config/test_generation.yaml` 了解完整配置选项
- 测试脚本: 使用 `test_api_client.py` 进行 API 功能测试

## 许可证

本项目采用 MIT 许可证。