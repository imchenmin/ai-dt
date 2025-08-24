"""
Comprehensive error handling for LLM providers with standardized error types and retry mechanisms.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, Type
from enum import Enum
import openai
import requests

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Standardized error categories for LLM operations."""
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    TIMEOUT = "timeout"
    CONTENT = "content"
    CONFIGURATION = "configuration"
    PROVIDER = "provider"
    UNKNOWN = "unknown"


class LLMError(Exception):
    """Base exception for LLM-related errors with standardized metadata."""
    
    def __init__(self, 
                 message: str, 
                 category: ErrorCategory, 
                 provider: str,
                 original_error: Optional[Exception] = None,
                 retryable: bool = False,
                 retry_after: Optional[int] = None):
        self.message = message
        self.category = category
        self.provider = provider
        self.original_error = original_error
        self.retryable = retryable
        self.retry_after = retry_after
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'message': self.message,
            'category': self.category.value,
            'provider': self.provider,
            'retryable': self.retryable,
            'retry_after': self.retry_after,
            'original_error': str(self.original_error) if self.original_error else None
        }


class ErrorHandler:
    """Handles errors and retries for LLM operations with exponential backoff."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def with_retry(self, 
                  func: Callable,
                  operation_name: str,
                  provider: str,
                  **kwargs) -> Any:
        """
        Execute a function with retry logic and standardized error handling.
        
        Args:
            func: The function to execute
            operation_name: Name of the operation for logging
            provider: LLM provider name
            **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the function if successful
            
        Raises:
            LLMError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(**kwargs)
                
            except Exception as e:
                last_error = e
                error_info = self._classify_error(e, provider)
                
                if not error_info['retryable'] or attempt == self.max_retries:
                    break
                    
                # Calculate delay with exponential backoff and jitter
                delay = min(
                    self.initial_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed for {operation_name} "
                    f"with {provider}: {error_info['message']}. Retrying in {delay:.1f}s"
                )
                
                time.sleep(delay)
        
        # If we get here, all retries failed
        error_info = self._classify_error(last_error, provider)
        raise LLMError(
            message=f"Failed {operation_name} after {self.max_retries + 1} attempts: {error_info['message']}",
            category=error_info['category'],
            provider=provider,
            original_error=last_error,
            retryable=error_info['retryable']
        )
    
    def _classify_error(self, error: Exception, provider: str) -> Dict[str, Any]:
        """Classify an error and determine if it's retryable."""
        
        # Handle HTTP errors first (they have specific status codes)
        if isinstance(error, requests.HTTPError):
            if error.response.status_code >= 500:
                return {
                    'message': f"Server error for {provider}: {error.response.status_code}",
                    'category': ErrorCategory.PROVIDER,
                    'retryable': True
                }
            else:
                return {
                    'message': f"HTTP error for {provider}: {error.response.status_code}",
                    'category': ErrorCategory.PROVIDER,
                    'retryable': False
                }
        
        # Network errors
        elif isinstance(error, requests.ConnectionError):
            return {
                'message': f"Network connection error for {provider}: {str(error)}",
                'category': ErrorCategory.NETWORK,
                'retryable': True
            }
            
        # Timeout errors
        elif isinstance(error, requests.Timeout):
            return {
                'message': f"Request timeout for {provider}: {str(error)}",
                'category': ErrorCategory.TIMEOUT,
                'retryable': True
            }
            
        # OpenAI/DeepSeek errors (OpenAI SDK) - string pattern matching
        error_str = str(error).lower()
        
        # Check for authentication errors
        if any(keyword in error_str for keyword in ['auth', 'authenticat', 'key', 'token', 'invalid']):
            return {
                'message': f"Authentication failed for {provider}: {str(error)}",
                'category': ErrorCategory.AUTHENTICATION,
                'retryable': False
            }
            
        # Check for rate limit errors
        elif any(keyword in error_str for keyword in ['rate', 'limit', 'quota', '429']):
            return {
                'message': f"Rate limit exceeded for {provider}: {str(error)}",
                'category': ErrorCategory.RATE_LIMIT,
                'retryable': True
            }
            
        # Check for timeout errors
        elif any(keyword in error_str for keyword in ['timeout', 'timed out', 'wait', 'long']):
            return {
                'message': f"API timeout for {provider}: {str(error)}",
                'category': ErrorCategory.TIMEOUT,
                'retryable': True
            }
            
        # Check for general API errors
        elif any(keyword in error_str for keyword in ['api', 'server', 'internal', '5']):
            return {
                'message': f"API error for {provider}: {str(error)}",
                'category': ErrorCategory.PROVIDER,
                'retryable': True
            }
        
        # Unknown errors
        else:
            return {
                'message': f"Unknown error for {provider}: {str(error)}",
                'category': ErrorCategory.UNKNOWN,
                'retryable': False
            }


def handle_llm_error(error: Exception, provider: str, operation: str = "LLM operation") -> Dict[str, Any]:
    """
    Handle an LLM error and return a standardized error response.
    
    Args:
        error: The exception that occurred
        provider: LLM provider name
        operation: Description of the operation that failed
        
    Returns:
        Standardized error response dictionary
    """
    handler = ErrorHandler()
    error_info = handler._classify_error(error, provider)
    
    logger.error(
        f"{operation} failed for {provider}: {error_info['message']} "
        f"(Category: {error_info['category'].value}, Retryable: {error_info['retryable']})"
    )
    
    return {
        'success': False,
        'error': error_info['message'],
        'error_category': error_info['category'].value,
        'provider': provider,
        'retryable': error_info['retryable'],
        'test_code': '',
        'usage': {}
    }