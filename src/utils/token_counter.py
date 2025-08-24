"""
Token counting utility for accurate LLM context size management
"""

from typing import Optional, Dict, Any
import json


try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class TokenCounter:
    """Accurate token counting for LLM context management"""
    
    # Default token limits for different LLM providers and models
    DEFAULT_TOKEN_LIMITS = {
        'openai': {
            'gpt-3.5-turbo': 4096,
            'gpt-4': 8192,
            'gpt-4-turbo': 128000,
        },
        'deepseek': {
            'deepseek-chat': 128000,
            'deepseek-coder': 16384,
        },
        'mock': {
            'mock': 8000,  # Character-based fallback
        }
    }
    
    def __init__(self, provider: str = "openai", model: str = "gpt-3.5-turbo"):
        self.provider = provider
        self.model = model
        self.encoder = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.encoding_for_model(model)
            except (KeyError, ValueError):
                # Fallback to cl100k_base for unknown models
                self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using appropriate encoder"""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Fallback: approximate token count (4 chars ≈ 1 token)
            return len(text) // 4
    
    def count_tokens_from_dict(self, data: Dict[str, Any]) -> int:
        """Count tokens from a dictionary by converting to JSON"""
        json_text = json.dumps(data, ensure_ascii=False)
        return self.count_tokens(json_text)
    
    def get_model_limit(self) -> int:
        """Get token limit for current provider and model"""
        provider_limits = self.DEFAULT_TOKEN_LIMITS.get(self.provider, {})
        return provider_limits.get(self.model, 4000)  # Default fallback
    
    def get_available_tokens(self, prompt_base_size: int = 0) -> int:
        """Calculate available tokens for context after accounting for prompt base"""
        total_limit = self.get_model_limit()
        # Reserve 20% for completion and safety margin
        available = int(total_limit * 0.8) - prompt_base_size
        return max(available, 500)  # Minimum context size
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Static method for quick token estimation"""
        # Simple estimation: 4 characters ≈ 1 token
        return len(text) // 4


def create_token_counter(llm_provider: str, llm_model: str) -> TokenCounter:
    """Factory function to create appropriate token counter"""
    return TokenCounter(llm_provider, llm_model)