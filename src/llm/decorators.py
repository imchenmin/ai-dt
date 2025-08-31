"""
Decorator classes for enhancing LLM provider functionality
"""

import time
from typing import Optional

from .providers import LLMProvider
from .models import GenerationRequest, GenerationResponse
from src.utils.logging_utils import get_logger
from src.utils.error_handler import ErrorHandler, LLMError

logger = get_logger(__name__)


class RetryDecorator(LLMProvider):
    """Decorator that adds retry functionality to LLM providers"""
    
    def __init__(self, provider: LLMProvider, max_retries: int = 3, 
                 retry_delay: float = 1.0):
        self.provider = provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_handler = ErrorHandler(
            max_retries=max_retries,
            retry_delay=retry_delay
        )
    
    @property
    def provider_name(self) -> str:
        return f"{self.provider.provider_name}_with_retry"
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate with retry logic"""
        try:
            # Use the error handler with retry
            result = self.error_handler.with_retry(
                lambda: self.provider.generate(request),
                "test generation",
                self.provider.provider_name
            )
            return result
        except Exception as e:
            logger.error(f"Retry failed after {self.max_retries} attempts: {e}")
            return GenerationResponse(
                success=False,
                error=f"Failed test generation after {self.max_retries + 1} attempts: {e}",
                provider=self.provider_name
            )


class RateLimitDecorator(LLMProvider):
    """Decorator that adds rate limiting to LLM providers"""
    
    def __init__(self, provider: LLMProvider, rate_limit: float):
        self.provider = provider
        self.rate_limit = rate_limit  # requests per second
        self.last_request_time: Optional[float] = None
    
    @property
    def provider_name(self) -> str:
        return f"{self.provider.provider_name}_rate_limited"
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate with rate limiting"""
        # Implement rate limiting
        if self.last_request_time is not None:
            time_since_last = time.time() - self.last_request_time
            min_interval = 1.0 / self.rate_limit
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        return self.provider.generate(request)


class LoggingDecorator(LLMProvider):
    """Decorator that adds detailed logging to LLM providers"""
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    @property
    def provider_name(self) -> str:
        return f"{self.provider.provider_name}_logged"
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate with detailed logging"""
        start_time = time.time()
        
        logger.info(f"Starting generation with {self.provider.provider_name}")
        logger.debug(f"Request: max_tokens={request.max_tokens}, "
                    f"temperature={request.temperature}, language={request.language}")
        logger.debug(f"Prompt length: {len(request.prompt)} characters")
        
        try:
            response = self.provider.generate(request)
            
            duration = time.time() - start_time
            
            if response.success:
                logger.info(f"Generation successful in {duration:.2f}s")
                logger.info(f"Generated {len(response.content)} characters")
                if response.usage:
                    logger.info(f"Token usage: {response.usage.total_tokens} total "
                               f"({response.usage.prompt_tokens} prompt, "
                               f"{response.usage.completion_tokens} completion)")
            else:
                logger.error(f"Generation failed in {duration:.2f}s: {response.error}")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Generation error in {duration:.2f}s: {e}")
            raise


class ValidationDecorator(LLMProvider):
    """Decorator that validates requests and responses"""
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    @property
    def provider_name(self) -> str:
        return f"{self.provider.provider_name}_validated"
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate with request/response validation"""
        # Validate request
        self._validate_request(request)
        
        # Generate response
        response = self.provider.generate(request)
        
        # Validate response
        self._validate_response(response)
        
        return response
    
    def _validate_request(self, request: GenerationRequest) -> None:
        """Validate generation request"""
        if not request.prompt.strip():
            raise ValueError("Request prompt cannot be empty")
        
        if request.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if not (0 <= request.temperature <= 2):
            raise ValueError("temperature must be between 0 and 2")
    
    def _validate_response(self, response: GenerationResponse) -> None:
        """Validate generation response"""
        if response.success and not response.content:
            logger.warning("Successful response has empty content")
        
        if not response.success and not response.error:
            logger.warning("Failed response has no error message")