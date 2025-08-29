"""
Legacy LLM client - backward compatibility wrapper

This module provides a wrapper around the new LLM architecture to maintain
backward compatibility with existing code.
"""

from typing import Dict, Any

from src.llm import LLMClient as NewLLMClient
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Legacy LLM client that maintains backward compatibility
    
    This class wraps the new LLMClient to provide the same API as the original
    while using the improved architecture internally.
    """
    
    def __init__(self, provider: str = "openai", api_key: str = None, 
                 base_url: str = None, model: str = "gpt-3.5-turbo",
                 max_retries: int = 3, retry_delay: float = 1.0):
        
        # Create new client using improved architecture
        self.client = NewLLMClient(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # Store attributes for compatibility
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def generate_test(self, prompt: str, max_tokens: int = 2000, 
                     temperature: float = 0.3, language: str = "c") -> Dict[str, Any]:
        """Generate test code using LLM (backward compatible API)"""
        return self.client.generate_test(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            language=language
        )
    
    def _setup_client(self):
        """Setup client - no longer needed but kept for compatibility"""
        pass
    
    def _generate_with_openai(self, prompt: str, max_tokens: int, 
                             temperature: float, language: str = "c") -> Dict[str, Any]:
        """Legacy method - redirects to new implementation"""
        return self.generate_test(prompt, max_tokens, temperature, language)
    
    def _generate_with_deepseek(self, prompt: str, max_tokens: int, 
                               temperature: float, language: str = "c") -> Dict[str, Any]:
        """Legacy method - redirects to new implementation"""
        return self.generate_test(prompt, max_tokens, temperature, language)
    
    def _generate_with_dify(self, prompt: str, max_tokens: int, 
                           temperature: float) -> Dict[str, Any]:
        """Legacy method - redirects to new implementation"""
        return self.generate_test(prompt, max_tokens, temperature)
    
    def _generate_with_anthropic(self, prompt: str, max_tokens: int, 
                                temperature: float, language: str = "c") -> Dict[str, Any]:
        """Legacy method - redirects to new implementation"""
        return self.generate_test(prompt, max_tokens, temperature, language)
    
    def _generate_with_local(self, prompt: str, max_tokens: int, 
                            temperature: float, language: str = "c") -> Dict[str, Any]:
        """Legacy method - redirects to new implementation"""
        return self.generate_test(prompt, max_tokens, temperature, language)