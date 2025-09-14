#!/usr/bin/env python3
"""
Dify-Web功能提取的独立API服务器
提供OpenAI兼容的API接口，支持curl文件输入
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Union
import uvicorn

# 导入项目现有的LLM组件
from src.llm.client import LLMClient
from src.llm.models import GenerationRequest, LLMConfig
from src.llm.providers import DifyWebProvider
from src.utils.config_manager import ConfigManager
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# FastAPI应用实例
app = FastAPI(
    title="AI-DT API Server",
    description="基于dify-web功能的OpenAI兼容API服务器",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化配置管理器和LLM客户端
config_manager = ConfigManager(config_path="../config/test_generation.yaml")
llm_clients: Dict[str, LLMClient] = {}
curl_configs: Dict[str, str] = {}

# OpenAI兼容的数据模型
class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: system, user, assistant")
    content: str = Field(..., description="消息内容")

class ChatCompletionRequest(BaseModel):
    model: str = Field("dify-web", description="模型名称")
    messages: List[ChatMessage] = Field(..., description="对话消息列表")
    max_tokens: Optional[int] = Field(2000, description="最大token数")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    stream: Optional[bool] = Field(False, description="是否流式响应")
    top_p: Optional[float] = Field(1.0, description="top_p参数")
    frequency_penalty: Optional[float] = Field(0.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, description="存在惩罚")
    stop: Optional[List[str]] = Field(None, description="停止词")

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "ai-dt"

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

class CurlConfigRequest(BaseModel):
    model_name: str = Field(..., description="模型名称")
    curl_content: str = Field(..., description="curl命令内容")
    description: Optional[str] = Field("", description="配置描述")

class CurlConfigResponse(BaseModel):
    model_name: str
    file_path: str
    description: str
    created_at: str

class CurlConfigListResponse(BaseModel):
    configs: List[CurlConfigResponse]

# 初始化函数
async def initialize_server():
    """初始化服务器配置"""
    logger.info("正在初始化API服务器...")
    
    # 扫描curl配置文件
    curl_dir = project_root / "config"
    if curl_dir.exists():
        for curl_file in curl_dir.glob("*.curl"):
            model_name = curl_file.stem
            curl_configs[model_name] = str(curl_file)
            logger.info(f"发现curl配置: {model_name} -> {curl_file}")
    
    # 初始化默认LLM客户端
    try:
        default_client = LLMClient(
            provider="openai",
            model="gpt-3.5-turbo"
        )
        llm_clients["default"] = default_client
        logger.info("默认LLM客户端初始化成功")
    except Exception as e:
        logger.warning(f"默认LLM客户端初始化失败: {e}")
    
    logger.info("API服务器初始化完成")

@app.on_event("startup")
async def startup_event():
    await initialize_server()

# API端点实现
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI-DT API Server",
        "version": "1.0.0",
        "description": "基于dify-web功能的OpenAI兼容API服务器",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "available_models": list(curl_configs.keys()),
        "llm_clients": list(llm_clients.keys())
    }

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """列出可用模型"""
    models = []
    
    # 添加curl配置的模型
    for model_name in curl_configs.keys():
        models.append(ModelInfo(
            id=model_name,
            created=int(datetime.now().timestamp()),
            owned_by="ai-dt"
        ))
    
    # 添加默认模型
    if "default" in llm_clients:
        models.append(ModelInfo(
            id="gpt-3.5-turbo",
            created=int(datetime.now().timestamp()),
            owned_by="ai-dt"
        ))
    
    return ModelsResponse(data=models)

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI兼容的聊天完成API"""
    try:
        logger.info(f"收到聊天完成请求: model={request.model}, messages={len(request.messages)}")
        
        # 获取或创建LLM客户端
        client = await get_llm_client(request.model)
        
        # 构建提示词
        prompt = build_prompt_from_messages(request.messages)
        
        # 创建生成请求
        gen_request = GenerationRequest(
            prompt=prompt,
            max_tokens=request.max_tokens or 2000,
            temperature=request.temperature or 0.7,
            language="general"
        )
        
        # 如果是流式响应
        if request.stream:
            return StreamingResponse(
                stream_chat_completion(client, gen_request, request),
                media_type="text/plain"
            )
        
        # 非流式响应
        response = client.generate(gen_request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"生成失败: {response.error}")
        
        # 构建OpenAI格式的响应
        completion_response = ChatCompletionResponse(
            id=f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        )
        
        return completion_response
        
    except Exception as e:
        logger.error(f"聊天完成请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_llm_client(model_name: str) -> LLMClient:
    """获取或创建LLM客户端"""
    # 如果已经存在客户端，直接返回
    if model_name in llm_clients:
        return llm_clients[model_name]
    
    # 检查是否有对应的curl配置
    if model_name in curl_configs:
        try:
            # 使用DifyWebProvider创建客户端
            curl_file = curl_configs[model_name]
            
            # 创建LLM配置，包含curl_file_path
            config = LLMConfig(
                provider_name="dify_web",
                model=model_name,
                curl_file_path=curl_file
            )
            
            # 创建客户端
            client = LLMClient.create_from_config(config)
            
            llm_clients[model_name] = client
            logger.info(f"为模型 {model_name} 创建了DifyWeb客户端")
            return client
            
        except Exception as e:
            logger.error(f"创建DifyWeb客户端失败: {e}")
            # 回退到默认客户端
            if "default" in llm_clients:
                return llm_clients["default"]
            raise HTTPException(status_code=500, detail=f"无法创建模型 {model_name} 的客户端")
    
    # 使用默认客户端
    if "default" in llm_clients:
        return llm_clients["default"]
    
    # 创建新的默认客户端
    try:
        client = LLMClient(provider="openai", model="gpt-3.5-turbo")
        llm_clients["default"] = client
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法创建默认客户端: {e}")

def build_prompt_from_messages(messages: List[ChatMessage]) -> str:
    """从消息列表构建提示词"""
    prompt_parts = []
    
    for message in messages:
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"User: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    return "\n\n".join(prompt_parts)

async def stream_chat_completion(client: LLMClient, gen_request: GenerationRequest, request: ChatCompletionRequest):
    """流式聊天完成响应"""
    try:
        # 注意：当前的LLMClient不支持流式响应，这里模拟流式输出
        response = client.generate(gen_request)
        
        if not response.success:
            yield f"data: {{\"error\": \"{response.error}\"}}\n\n"
            return
        
        # 模拟流式输出，将内容分块发送
        content = response.content
        chunk_size = 10  # 每次发送10个字符
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            
            stream_response = {
                "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": chunk
                        },
                        "finish_reason": None
                    }
                ]
            }
            
            yield f"data: {json.dumps(stream_response, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)  # 模拟延迟
        
        # 发送结束标记
        final_response = {
            "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        
        yield f"data: {json.dumps(final_response, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"流式响应生成失败: {e}")
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

@app.post("/admin/curl-configs", response_model=CurlConfigResponse)
async def add_curl_config(request: CurlConfigRequest):
    """添加新的curl配置"""
    try:
        # 验证模型名称
        if not request.model_name.strip():
            raise HTTPException(status_code=400, detail="模型名称不能为空")
        
        # 验证curl内容
        if not request.curl_content.strip():
            raise HTTPException(status_code=400, detail="curl内容不能为空")
        
        # 创建配置文件路径
        config_dir = project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        curl_file_path = config_dir / f"{request.model_name}.curl"
        
        # 写入curl文件
        with open(curl_file_path, 'w', encoding='utf-8') as f:
            f.write(request.curl_content)
        
        # 更新内存中的配置
        curl_configs[request.model_name] = str(curl_file_path)
        
        # 如果该模型已有客户端，删除以便重新创建
        if request.model_name in llm_clients:
            del llm_clients[request.model_name]
        
        logger.info(f"添加curl配置: {request.model_name} -> {curl_file_path}")
        
        return CurlConfigResponse(
            model_name=request.model_name,
            file_path=str(curl_file_path),
            description=request.description,
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"添加curl配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/curl-configs", response_model=CurlConfigListResponse)
async def list_curl_configs():
    """列出所有curl配置"""
    try:
        configs = []
        
        for model_name, file_path in curl_configs.items():
            # 读取文件创建时间
            try:
                file_stat = os.stat(file_path)
                created_at = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            except:
                created_at = datetime.now().isoformat()
            
            configs.append(CurlConfigResponse(
                model_name=model_name,
                file_path=file_path,
                description=f"Curl配置文件: {model_name}",
                created_at=created_at
            ))
        
        return CurlConfigListResponse(configs=configs)
        
    except Exception as e:
        logger.error(f"列出curl配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/curl-configs/{model_name}")
async def delete_curl_config(model_name: str):
    """删除curl配置"""
    try:
        if model_name not in curl_configs:
            raise HTTPException(status_code=404, detail=f"模型 {model_name} 的配置不存在")
        
        # 删除文件
        file_path = curl_configs[model_name]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 从内存中删除
        del curl_configs[model_name]
        
        # 删除对应的客户端
        if model_name in llm_clients:
            del llm_clients[model_name]
        
        logger.info(f"删除curl配置: {model_name}")
        
        return {"message": f"成功删除模型 {model_name} 的配置"}
        
    except Exception as e:
        logger.error(f"删除curl配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/curl-configs/{model_name}")
async def get_curl_config(model_name: str):
    """获取指定模型的curl配置内容"""
    try:
        if model_name not in curl_configs:
            raise HTTPException(status_code=404, detail=f"模型 {model_name} 的配置不存在")
        
        file_path = curl_configs[model_name]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"配置文件不存在: {file_path}")
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 读取文件信息
        file_stat = os.stat(file_path)
        created_at = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
        
        return {
            "model_name": model_name,
            "file_path": file_path,
            "content": content,
            "created_at": created_at,
            "size": file_stat.st_size
        }
        
    except Exception as e:
        logger.error(f"获取curl配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )