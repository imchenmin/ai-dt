"""
LLM client for generating test cases using various AI providers
"""

import json
import requests
import openai
from typing import Dict, Any, Optional
import time
from pathlib import Path
from openai import OpenAI
from src.utils.logging_utils import get_logger
from src.utils.error_handling import ErrorHandler, handle_llm_error, LLMError

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with various LLM providers"""
    
    def __init__(self, provider: str = "openai", api_key: str = None, 
                 base_url: str = None, model: str = "gpt-3.5-turbo",
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_handler = ErrorHandler(
            max_retries=max_retries,
            initial_delay=retry_delay
        )
        self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate client based on provider"""
        if self.provider == "openai":
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else "https://api.openai.com/v1"
            )
        
        elif self.provider == "deepseek":
            # DeepSeek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else "https://api.deepseek.com/v1"
            )
        
        elif self.provider == "dify":
            # Dify uses a custom REST API, no specific client library needed
            if not self.api_key:
                raise ValueError("API key is required for Dify provider.")
            self.client = None # Using requests directly
            self.dify_api_url = self.base_url if self.base_url else "https://api.dify.ai/v1/chat-messages"

        elif self.provider == "anthropic":
            # Anthropic client setup would go here
            self.client = None
        
        elif self.provider == "local":
            # Local model setup
            self.client = None
    
    def generate_test(self, prompt: str, max_tokens: int = 2000, 
                     temperature: float = 0.3, language: str = "c") -> Dict[str, Any]:
        """Generate test code using LLM with retry mechanism"""
        try:
            if self.provider == "openai":
                return self.error_handler.with_retry(
                    self._generate_with_openai,
                    "test generation",
                    self.provider,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    language=language
                )
            elif self.provider == "deepseek":
                return self.error_handler.with_retry(
                    self._generate_with_deepseek,
                    "test generation", 
                    self.provider,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    language=language
                )
            elif self.provider == "dify":
                return self.error_handler.with_retry(
                    self._generate_with_dify,
                    "test generation",
                    self.provider,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif self.provider == "anthropic":
                return self._generate_with_anthropic(prompt, max_tokens, temperature, language)
            elif self.provider == "local":
                return self._generate_with_local(prompt, max_tokens, temperature, language)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        
        except LLMError as e:
            return e.to_dict()
        except Exception as e:
            return handle_llm_error(e, self.provider, "test generation")
    
    def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float, language: str = "c") -> Dict[str, Any]:
        """Generate test using OpenAI API"""
        from src.utils.prompt_templates import PromptTemplates
        system_prompt = PromptTemplates.get_system_prompt(language)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            'success': True,
            'test_code': response.choices[0].message.content.strip(),
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'model': self.model
        }
    
    def _generate_with_deepseek(self, prompt: str, max_tokens: int, temperature: float, language: str = "c") -> Dict[str, Any]:
        """Generate test using DeepSeek API"""
        from src.utils.prompt_templates import PromptTemplates
        system_prompt = PromptTemplates.get_system_prompt(language)
        
        # DeepSeek uses OpenAI-compatible API format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            'success': True,
            'test_code': response.choices[0].message.content.strip(),
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'model': self.model
        }

    def _generate_with_dify(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate test using Dify API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Note: Dify's API has different parameters.
        # `max_tokens` and `temperature` are not directly supported in the standard chat-messages endpoint.
        # These would typically be configured in the Dify application settings for the agent.
        # We include them in the call signature for consistency but they are not used here.
        data = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",  # Use "blocking" to get the full response at once
            "user": "ai-dt-user" # A unique identifier for the user
        }

        try:
            response = requests.post(self.dify_api_url, headers=headers, json=data, timeout=300)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            response_data = response.json()
            
            # Defensive checks for response format
            if 'answer' not in response_data:
                raise LLMError(f"Dify API response missing 'answer' key. Response: {response_data}", provider="dify")

            # Dify response may not include token usage details in the same way as OpenAI.
            # We'll provide default values if they are not present.
            usage = response_data.get('metadata', {}).get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)

            return {
                'success': True,
                'test_code': response_data['answer'].strip(),
                'usage': {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                },
                'model': response_data.get('model', 'dify_model') # Extract model if available
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API request failed: {e}")
            raise LLMError(f"Network error calling Dify API: {e}", provider="dify") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Dify API JSON response: {response.text}")
            raise LLMError(f"Invalid JSON response from Dify API.", provider="dify") from e

    def _generate_with_anthropic(self, prompt: str, max_tokens: int, temperature: float, language: str = "c") -> Dict[str, Any]:
        """Generate test using Anthropic API (placeholder)"""
        # This would be implemented when Anthropic API is available
        return {
            'success': False,
            'error': "Anthropic API not implemented yet",
            'test_code': '',
            'usage': {}
        }
    
    def _generate_with_local(self, prompt: str, max_tokens: int, temperature: float, language: str = "c") -> Dict[str, Any]:
        """Generate test using local model (placeholder)"""
        # This would be implemented for local model inference
        return {
            'success': False,
            'error': "Local model inference not implemented yet",
            'test_code': '',
            'usage': {}
        }
    
    # File saving functionality has been moved to TestFileOrganizer
    # in src/utils/file_organizer.py for better separation of concerns