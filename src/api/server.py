"""
FastAPI server for exposing LLM client functionality
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.llm.client import LLMClient
from src.llm.models import GenerationRequest, LLMConfig
from src.utils.config_manager import config_manager
from src.utils.logging_utils import get_logger
from .models import (
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    Message, 
    MessageRole, 
    Choice, 
    Usage, 
    ErrorResponse
)

logger = get_logger(__name__)


class APIServer:
    """FastAPI server for LLM client API"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, 
                 default_provider: str = "openai"):
        self.host = host
        self.port = port
        self.default_provider = default_provider
        self.app = FastAPI(
            title="AI-DT LLM API",
            description="OpenAI-compatible API for AI-Driven Test Generator LLM Client",
            version="1.0.0"
        )
        
        # Add CORS middleware with secure configuration
        # Load allowed origins from environment or use secure defaults
        import os
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
        allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],  # Explicitly allowed methods
            allow_headers=[
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Accept",
                "Origin"
            ],  # Explicitly allowed headers
        )
        
        # LLM client cache
        self._clients: Dict[str, LLMClient] = {}
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "AI-DT LLM API Server", "version": "1.0.0"}
        
        @self.app.get("/v1/models")
        async def list_models():
            """List available models"""
            try:
                # Get available providers from config
                providers = config_manager.get_available_providers()
                models = []
                
                for provider in providers:
                    try:
                        llm_config = config_manager.get_llm_config(provider)
                        model_name = llm_config.get('model', f'{provider}-default')
                        models.append({
                            "id": model_name,
                            "object": "model",
                            "created": 1677610602,
                            "owned_by": provider,
                            "permission": [],
                            "root": model_name,
                            "parent": None
                        })
                    except Exception as e:
                        logger.warning(f"Failed to get config for provider {provider}: {e}")
                
                return {"object": "list", "data": models}
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return ErrorResponse.create(f"Failed to list models: {str(e)}").to_dict()
        
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: Request):
            """OpenAI-compatible chat completions endpoint"""
            try:
                # Parse request
                body = await request.json()
                chat_request = ChatCompletionRequest.from_dict(body)
                
                # Get or create LLM client
                client = self._get_llm_client(chat_request.model)
                
                # Convert messages to prompt
                prompt = self._messages_to_prompt(chat_request.messages)
                
                # Create generation request
                gen_request = GenerationRequest(
                    prompt=prompt,
                    max_tokens=chat_request.max_tokens or 2000,
                    temperature=chat_request.temperature or 0.3,
                    language="text"  # Default to text for chat
                )
                
                # Generate response
                gen_response = client.generate(gen_request)
                
                if not gen_response.success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Generation failed: {gen_response.error}"
                    )
                
                # Convert to OpenAI format
                response_message = Message(
                    role=MessageRole.ASSISTANT,
                    content=gen_response.content
                )
                
                choice = Choice(
                    index=0,
                    message=response_message,
                    finish_reason="stop"
                )
                
                usage = None
                if gen_response.usage:
                    usage = Usage(
                        prompt_tokens=gen_response.usage.prompt_tokens,
                        completion_tokens=gen_response.usage.completion_tokens,
                        total_tokens=gen_response.usage.total_tokens
                    )
                
                chat_response = ChatCompletionResponse(
                    id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    model=gen_response.model or chat_request.model,
                    choices=[choice],
                    usage=usage
                )
                
                return JSONResponse(content=chat_response.to_dict())
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in chat completions: {e}")
                error_response = ErrorResponse.create(
                    f"Internal server error: {str(e)}",
                    type="internal_error"
                )
                return JSONResponse(
                    status_code=500,
                    content=error_response.to_dict()
                )
        
        @self.app.post("/v1/completions")
        async def completions(request: Request):
            """OpenAI-compatible completions endpoint"""
            try:
                body = await request.json()
                
                prompt = body.get("prompt", "")
                model = body.get("model", self.default_provider)
                max_tokens = body.get("max_tokens", 2000)
                temperature = body.get("temperature", 0.3)
                
                # Get or create LLM client
                client = self._get_llm_client(model)
                
                # Create generation request
                gen_request = GenerationRequest(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    language="text"
                )
                
                # Generate response
                gen_response = client.generate(gen_request)
                
                if not gen_response.success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Generation failed: {gen_response.error}"
                    )
                
                # Convert to OpenAI format
                usage = None
                if gen_response.usage:
                    usage = {
                        "prompt_tokens": gen_response.usage.prompt_tokens,
                        "completion_tokens": gen_response.usage.completion_tokens,
                        "total_tokens": gen_response.usage.total_tokens
                    }
                
                response = {
                    "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                    "object": "text_completion",
                    "created": int(__import__('time').time()),
                    "model": gen_response.model or model,
                    "choices": [{
                        "text": gen_response.content,
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": "stop"
                    }],
                    "usage": usage
                }
                
                return JSONResponse(content=response)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in completions: {e}")
                error_response = ErrorResponse.create(
                    f"Internal server error: {str(e)}",
                    type="internal_error"
                )
                return JSONResponse(
                    status_code=500,
                    content=error_response.to_dict()
                )
    
    def _get_llm_client(self, model: str) -> LLMClient:
        """Get or create LLM client for the specified model"""
        if model in self._clients:
            return self._clients[model]
        
        # Try to determine provider from model name
        provider = self._get_provider_from_model(model)
        
        try:
            # Get provider configuration
            llm_config_dict = config_manager.get_llm_config(provider)
            
            # For dify_web provider, get curl_file_path from environment
            curl_file_path = None
            if provider == "dify_web":
                import os
                curl_file_path = os.environ.get('DIFY_CURL_FILE_PATH')
            
            # Create LLM config with all necessary parameters
            from src.llm.models import LLMConfig
            config = LLMConfig(
                provider_name=provider,
                api_key=config_manager.get_api_key(provider),
                base_url=llm_config_dict.get('base_url'),
                model=llm_config_dict.get('model', model),
                max_retries=llm_config_dict.get('max_retries', 3),
                retry_delay=llm_config_dict.get('retry_delay', 1.0),
                curl_file_path=curl_file_path
            )
            
            # Create LLM client using the config
            client = LLMClient.create_from_config(config)
            
            self._clients[model] = client
            return client
            
        except Exception as e:
            logger.error(f"Failed to create LLM client for model {model}: {e}")
            # Fallback to default provider
            if provider != self.default_provider:
                return self._get_llm_client(self.default_provider)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create client for model {model}: {str(e)}"
            )
    
    def _get_provider_from_model(self, model: str) -> str:
        """Determine provider from model name"""
        model_lower = model.lower()
        
        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "deepseek" in model_lower:
            return "deepseek"
        elif "dify_web" in model_lower:
            return "dify_web"
        elif "dify" in model_lower:
            return "dify"
        else:
            # Try to find provider in available providers
            try:
                providers = config_manager.get_available_providers()
                for provider in providers:
                    try:
                        config = config_manager.get_llm_config(provider)
                        if config.get('model') == model:
                            return provider
                    except:
                        continue
            except:
                pass
            
            # Default fallback
            return self.default_provider
    
    def _messages_to_prompt(self, messages: List[Message]) -> str:
        """Convert chat messages to a single prompt"""
        prompt_parts = []
        
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                prompt_parts.append(f"System: {message.content}")
            elif message.role == MessageRole.USER:
                prompt_parts.append(f"User: {message.content}")
            elif message.role == MessageRole.ASSISTANT:
                prompt_parts.append(f"Assistant: {message.content}")
        
        return "\n\n".join(prompt_parts)
    
    def run(self, **kwargs):
        """Run the API server"""
        logger.info(f"Starting API server on {self.host}:{self.port}")
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            **kwargs
        )


def create_app(default_provider: str = "openai") -> FastAPI:
    """Create FastAPI app instance"""
    server = APIServer(default_provider=default_provider)
    return server.app