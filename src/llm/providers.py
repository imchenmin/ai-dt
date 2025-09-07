"""
LLM provider implementations following the provider pattern
"""

import json
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from .models import GenerationRequest, GenerationResponse, TokenUsage
from src.utils.logging_utils import get_logger
# from src.utils.prompt_templates import PromptTemplates  # Removed to avoid circular import

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
            # Use delayed import to avoid circular import
            from src.utils.prompt_templates import PromptTemplates
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
            # Use delayed import to avoid circular import
            from src.utils.prompt_templates import PromptTemplates
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


class DifyWebProvider(LLMProvider):
    """Dify Web provider that simulates browser behavior using curl commands"""
    
    def __init__(self, curl_file_path: str, model: str = "dify_web_model", timeout: float = 300.0):
        self.curl_file_path = curl_file_path
        self.model = model
        self.timeout = timeout
        self._session = None
        self._parsed_config = None
        self._parse_curl_file()
    
    @property
    def provider_name(self) -> str:
        return "dify_web"
    
    def _parse_curl_file(self):
        """Parse curl command from file"""
        import os
        import re
        
        if not os.path.exists(self.curl_file_path):
            raise ValueError(f"Curl file not found: {self.curl_file_path}")
        
        with open(self.curl_file_path, 'r', encoding='utf-8') as f:
            curl_content = f.read().strip()
        
        # Parse curl command
        self._parsed_config = self._extract_curl_info(curl_content)
    
    def _extract_curl_info(self, curl_command: str) -> dict:
        """Extract information from curl command"""
        import re
        import json
        
        config = {
            'url': None,
            'headers': {},
            'data': None,
            'method': 'POST'
        }
        
        # Extract URL
        url_match = re.search(r"curl\s+['\"]?([^'\"\s]+)['\"]?", curl_command)
        if url_match:
            config['url'] = url_match.group(1)
        
        # Extract headers
        header_pattern = r"-H\s+['\"]([^'\"]+)['\"]?"
        headers = re.findall(header_pattern, curl_command)
        for header in headers:
            if ':' in header:
                key, value = header.split(':', 1)
                config['headers'][key.strip()] = value.strip()
        
        # Extract data - improved regex to handle JSON with special characters
        data_match = re.search(r"--data-raw\s+['\"](.+?)['\"](?:\s|$)", curl_command, re.DOTALL)
        if not data_match:
            data_match = re.search(r"-d\s+['\"](.+?)['\"](?:\s|$)", curl_command, re.DOTALL)
        
        if data_match:
            data_str = data_match.group(1)
            # Handle escaped quotes in JSON
            data_str = data_str.replace('\\"', '"')
            try:
                config['data'] = json.loads(data_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON data: {e}, using as string")
                config['data'] = data_str
        
        return config
    
    def _create_session(self):
        """Create requests session with browser-like headers"""
        if self._session is None:
            import requests
            import uuid
            
            self._session = requests.Session()
            
            # Set browser-like headers
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/event-stream',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sentry-Trace': f"{uuid.uuid4().hex[:32]}-{uuid.uuid4().hex[:16]}-1",
                'Baggage': 'sentry-environment=production,sentry-release=1.0.0,sentry-public_key=public_key_placeholder'
            }
            
            # Update with parsed headers
            default_headers.update(self._parsed_config.get('headers', {}))
            self._session.headers.update(default_headers)
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Dify Web API with browser simulation"""
        try:
            self._create_session()
            
            if not self._parsed_config or not self._parsed_config.get('url'):
                raise ValueError("Invalid curl configuration")
            
            # Prepare request data
            data = self._parsed_config.get('data', {})
            if isinstance(data, dict):
                # Update query with user prompt
                data['query'] = request.prompt
                if 'response_mode' not in data:
                    data['response_mode'] = 'streaming'
                if 'user' not in data:
                    data['user'] = 'ai-dt-user'
            
            # Make request
            response = self._session.post(
                self._parsed_config['url'],
                json=data,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Process streaming response
            content = self._process_streaming_response(response)
            
            return GenerationResponse(
                success=True,
                content=content,
                usage=TokenUsage(
                    prompt_tokens=len(request.prompt.split()),
                    completion_tokens=len(content.split()),
                    total_tokens=len(request.prompt.split()) + len(content.split())
                ),
                model=self.model,
                provider=self.provider_name
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Dify Web API request failed: {e}")
            return GenerationResponse(
                success=False,
                error=f"Network error calling Dify Web API: {e}",
                model=self.model,
                provider=self.provider_name
            )
        except Exception as e:
            logger.error(f"Dify Web generation failed: {e}")
            return GenerationResponse(
                success=False,
                error=str(e),
                model=self.model,
                provider=self.provider_name
            )
    
    def _process_streaming_response(self, response) -> str:
        """Process streaming response from Dify API"""
        import json
        
        content_parts = []
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        # Handle different event types
                        if data.get('event') == 'message':
                            answer = data.get('answer', '')
                            if answer:
                                content_parts.append(answer)
                        elif data.get('event') == 'message_end':
                            # Final message, might contain complete answer
                            answer = data.get('answer', '')
                            if answer and not content_parts:
                                content_parts.append(answer)
                            break
                        elif data.get('event') == 'error':
                            error_msg = data.get('message', 'Unknown error')
                            raise ValueError(f"Dify API error: {error_msg}")
                            
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
        
        except Exception as e:
            logger.error(f"Error processing streaming response: {e}")
            raise
        
        return ''.join(content_parts).strip() or "No response received"