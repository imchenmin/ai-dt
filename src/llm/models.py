"""
Data models for LLM operations
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TokenUsage:
    """Token usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class GenerationRequest:
    """Request for LLM text generation"""
    prompt: str
    max_tokens: int = 2000
    temperature: float = 0.3
    language: str = "c"
    system_prompt: Optional[str] = None
    
    def __post_init__(self):
        # Validate parameters
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not self.prompt.strip():
            raise ValueError("prompt cannot be empty")


@dataclass
class GenerationResponse:
    """Response from LLM text generation"""
    success: bool
    content: str = ""
    usage: Optional[TokenUsage] = None
    model: str = ""
    error: Optional[str] = None
    provider: str = ""
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = TokenUsage()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for backward compatibility"""
        return {
            'success': self.success,
            'test_code': self.content,
            'usage': {
                'prompt_tokens': self.usage.prompt_tokens,
                'completion_tokens': self.usage.completion_tokens,
                'total_tokens': self.usage.total_tokens
            },
            'model': self.model,
            'error': self.error
        }


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 300.0
    rate_limit: Optional[float] = None
    curl_file_path: Optional[str] = None  # For dify_web provider
    
    # Feature flags
    retry_enabled: bool = True
    rate_limit_enabled: bool = False
    logging_enabled: bool = True
    
    def __post_init__(self):
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")