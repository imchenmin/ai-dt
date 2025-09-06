"""
LLM provider implementations following the provider pattern
"""

import json
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from .models import GenerationRequest, GenerationResponse, TokenUsage
from src.utils.logging_utils import get_logger
from src.utils.prompt_templates import PromptTemplates

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using the LLM provider"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation using requests"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, 
                 model: str = "gpt-3.5-turbo", timeout: float = 300.0):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self.timeout = timeout
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using OpenAI API"""
        try:
            system_prompt = request.system_prompt or PromptTemplates.get_system_prompt(request.language)
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            
            response_data = self._make_request(data)
            
            # Extract usage information
            usage_data = response_data.get('usage', {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
            
            # Extract content from response
            choices = response_data.get('choices', [])
            if not choices:
                raise ValueError("No choices in OpenAI API response")
            
            content = choices[0].get('message', {}).get('content', '')
            if not content:
                raise ValueError("Empty content in OpenAI API response")
            
            return GenerationResponse(
                success=True,
                content=content.strip(),
                usage=usage,
                model=self.model,
                provider=self.provider_name
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Network error calling OpenAI API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"OpenAI API response parsing failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Invalid response from OpenAI API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return GenerationResponse(
                success=False,
                error=str(e),
                model=self.model,
                provider=self.provider_name
            )


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider implementation using requests"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None,
                 model: str = "deepseek-chat", timeout: float = 300.0):
        self.api_key = api_key
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.model = model
        self.timeout = timeout
    
    @property
    def provider_name(self) -> str:
        return "deepseek"
    
    def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to DeepSeek API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using DeepSeek API"""
        try:
            system_prompt = request.system_prompt or PromptTemplates.get_system_prompt(request.language)
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            
            response_data = self._make_request(data)
            
            # Extract usage information
            usage_data = response_data.get('usage', {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
            
            # Extract content from response
            choices = response_data.get('choices', [])
            if not choices:
                raise ValueError("No choices in DeepSeek API response")
            
            content = choices[0].get('message', {}).get('content', '')
            if not content:
                raise ValueError("Empty content in DeepSeek API response")
            
            return GenerationResponse(
                success=True,
                content=content.strip(),
                usage=usage,
                model=self.model,
                provider=self.provider_name
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Network error calling DeepSeek API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"DeepSeek API response parsing failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Invalid response from DeepSeek API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except Exception as e:
            logger.error(f"DeepSeek generation failed: {e}")
            return GenerationResponse(
                success=False,
                error=str(e),
                model=self.model,
                provider=self.provider_name
            )


class DifyProvider(LLMProvider):
    """Dify API provider implementation"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None,
                 model: str = "dify_model", timeout: float = 300.0):
        self.api_key = api_key
        self.base_url = base_url or "https://api.dify.ai/v1/chat-messages"
        self.model = model
        self.timeout = timeout
    
    @property
    def provider_name(self) -> str:
        return "dify"
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Dify API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "inputs": {},
                "query": request.prompt,
                "response_mode": "blocking",
                "user": "ai-dt-user"
            }
            
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=data, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            if 'answer' not in response_data:
                raise ValueError(f"Dify API response missing 'answer' key. Response: {response_data}")
            
            # Extract usage information if available
            usage_data = response_data.get('metadata', {}).get('usage', {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
            
            return GenerationResponse(
                success=True,
                content=response_data['answer'].strip(),
                usage=usage,
                model=response_data.get('model', self.model),
                provider=self.provider_name
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API request failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Network error calling Dify API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Dify API response parsing failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Invalid response from Dify API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except Exception as e:
            logger.error(f"Dify generation failed: {e}")
            return GenerationResponse(
                success=False,
                error=str(e),
                model=self.model,
                provider=self.provider_name
            )


class MockProvider(LLMProvider):
    """Mock provider for testing and development"""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate mock test response"""
        mock_test_code = f"""// Mock test for prompt: {request.prompt[:50]}...
#include <gtest/gtest.h>
#include <MockCpp/MockCpp.h>

TEST(MockTest, TestGenerated) {{
    // This is a mock test generated for development/testing
    EXPECT_TRUE(true);
}}"""
        
        usage = TokenUsage(
            prompt_tokens=len(request.prompt) // 4,  # Rough estimation
            completion_tokens=len(mock_test_code) // 4,
            total_tokens=(len(request.prompt) + len(mock_test_code)) // 4
        )
        
        return GenerationResponse(
            success=True,
            content=mock_test_code,
            usage=usage,
            model=self.model,
            provider=self.provider_name
        )