# Dify API 客户端

这是一个模拟浏览器行为的Dify API客户端，用于绕过网络网关限制直接访问Dify服务。

## 功能特性

- 🌐 **模拟真实浏览器**: 完全模拟Chrome浏览器的请求头和行为
- 🔐 **Bearer Token认证**: 支持使用Bearer token进行身份验证
- 📡 **流式响应**: 支持实时流式响应处理
- 💬 **会话管理**: 支持多轮对话和会话历史
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 🎯 **简单易用**: 提供简单和高级两种使用方式

## 安装依赖

```bash
pip install requests
```

## 快速开始

### 1. 基本使用

```python
from src.dify_client import DifyClient

# 初始化客户端
token = "your_bearer_token_here"
client = DifyClient(bearer_token=token)

# 发送简单消息
response = client.send_simple_message("你好")
print(response)

# 关闭客户端
client.close()
```

### 2. 流式响应

```python
from src.dify_client import DifyClient

token = "your_bearer_token_here"
client = DifyClient(bearer_token=token)

# 流式接收响应
for chunk in client.send_chat_message("请介绍一下Python"):
    if 'answer' in chunk:
        print(chunk['answer'], end='', flush=True)

client.close()
```

### 3. 会话管理

```python
from src.dify_client import DifyClient

token = "your_bearer_token_here"
client = DifyClient(bearer_token=token)

conversation_id = ""

# 第一条消息
for chunk in client.send_chat_message("我的名字是张三", conversation_id=conversation_id):
    if 'conversation_id' in chunk:
        conversation_id = chunk['conversation_id']
    if 'answer' in chunk:
        print(chunk['answer'], end='', flush=True)

# 第二条消息，使用相同的conversation_id
for chunk in client.send_chat_message("你还记得我的名字吗？", conversation_id=conversation_id):
    if 'answer' in chunk:
        print(chunk['answer'], end='', flush=True)

client.close()
```

## 获取Bearer Token

1. 在浏览器中打开Dify应用
2. 打开开发者工具 (F12)
3. 切换到Network标签
4. 发送一条消息
5. 在请求中找到`chat-messages`请求
6. 复制Authorization头中的Bearer token

## 运行示例

```bash
# 运行完整示例
python examples/dify_example.py

# 或者直接运行客户端
python src/dify_client.py
```

## API参考

### DifyClient类

#### 初始化

```python
client = DifyClient(base_url="https://udify.app", bearer_token="your_token")
```

**参数:**
- `base_url` (str): Dify服务的基础URL，默认为"https://udify.app"
- `bearer_token` (str): Bearer认证令牌

#### 主要方法

##### send_chat_message()

发送聊天消息并返回流式响应。

```python
for chunk in client.send_chat_message(
    query="你好",
    conversation_id="",
    app_code="mOzK5CWRQurTSSTJ",
    files=[],
    inputs={},
    parent_message_id=None,
    response_mode="streaming"
):
    # 处理响应块
    pass
```

**参数:**
- `query` (str): 用户查询内容
- `conversation_id` (str): 会话ID，空字符串表示新会话
- `app_code` (str): 应用代码
- `files` (list): 附件文件列表
- `inputs` (dict): 输入参数
- `parent_message_id` (str): 父消息ID
- `response_mode` (str): 响应模式，"streaming"或"blocking"

##### send_simple_message()

发送简单消息并返回完整响应文本。

```python
response = client.send_simple_message("你好", app_code="mOzK5CWRQurTSSTJ")
```

##### set_bearer_token()

设置或更新Bearer认证令牌。

```python
client.set_bearer_token("new_token")
```

##### get_conversation_history()

获取指定会话的历史记录。

```python
history = client.get_conversation_history(conversation_id)
```

##### close()

关闭客户端会话。

```python
client.close()
```

## 错误处理

客户端包含完善的错误处理机制：

```python
try:
    response = client.send_simple_message("你好")
    print(response)
except Exception as e:
    print(f"请求失败: {e}")
finally:
    client.close()
```

## 注意事项

1. **Token有效性**: Bearer token有时效性，需要定期更新
2. **网络限制**: 确保网络可以访问Dify服务
3. **请求频率**: 避免过于频繁的请求，以免被限流
4. **资源清理**: 使用完毕后记得调用`close()`方法

## 故障排除

### 常见问题

1. **401 Unauthorized**: Bearer token无效或过期
   - 解决方案: 重新获取token

2. **403 Forbidden**: 权限不足
   - 解决方案: 检查token权限和应用访问权限

3. **网络连接错误**: 无法连接到Dify服务
   - 解决方案: 检查网络连接和防火墙设置

4. **响应格式错误**: 无法解析响应
   - 解决方案: 检查API版本兼容性

### 调试模式

可以通过修改代码启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 许可证

本项目采用MIT许可证。