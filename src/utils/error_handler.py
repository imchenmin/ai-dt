"""
Centralized error handling for consistent error management across the application
Includes both general error handling and LLM-specific error handling capabilities.
"""

import logging
import sys
import time
from typing import Optional, Callable, Any, Dict
from functools import wraps
from enum import Enum
import requests

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


# ===== LLM-Specific Error Handling =====

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
    """Centralized error handling with configurable strategies.
    
    Supports both general error handling and LLM-specific error handling with
    advanced error classification and retry mechanisms.
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 backoff_factor: float = 2.0,
                 max_delay: float = 60.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        
        # For LLM compatibility
        self.initial_delay = retry_delay
    
    def handle_error(self, error: Exception, context: str = "", 
                    should_retry: bool = False, retry_count: int = 0) -> bool:
        """Handle an error with configurable strategy"""
        logger.error(f"Error in {context}: {error}")
        
        if should_retry and retry_count < self.max_retries:
            delay = min(self.retry_delay * (self.backoff_factor ** retry_count), self.max_delay)
            logger.info(f"Retrying in {delay:.1f}s (attempt {retry_count + 1}/{self.max_retries})")
            return True
        
        return False
    
    def retry_on_failure(self, func: Callable) -> Callable:
        """Decorator to automatically retry a function on failure"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count <= self.max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    should_continue = self.handle_error(
                        e, f"{func.__name__}", 
                        should_retry=True, retry_count=retry_count
                    )
                    if not should_continue:
                        raise
            return None
        return wrapper

    def with_retry(self, 
                  func: Callable,
                  operation_name: str,
                  provider: str,
                  **kwargs) -> Any:
        """
        Execute a function with retry logic and LLM-specific error handling.
        
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
                    
                # Calculate delay with exponential backoff
                delay = min(
                    self.retry_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed for {operation_name} "
                    f"with {provider}: {error_info['message']}. Retrying in {delay:.1f}s"
                )
                
                time.sleep(delay)
        
        # If we get here, all retries failed
        if last_error is None:
            # This should not happen, but handle it gracefully
            raise LLMError(
                message=f"Failed {operation_name} after {self.max_retries + 1} attempts: Unknown error",
                category=ErrorCategory.UNKNOWN,
                provider=provider,
                original_error=None,
                retryable=False
            )
        
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


def handle_critical_error(error: Exception, message: str = "Critical error occurred") -> None:
    """Handle critical errors that should terminate the application"""
    logger.critical(f"{message}: {error}")
    sys.exit(1)


def handle_graceful_shutdown(error: Exception, message: str = "Graceful shutdown") -> None:
    """Handle errors that allow graceful shutdown"""
    logger.error(f"{message}: {error}")
    sys.exit(0)


def log_and_continue(error: Exception, context: str = "") -> None:
    """Log error but continue execution"""
    logger.warning(f"Non-critical error in {context}: {error}")


# Global error handler instance
error_handler = ErrorHandler()


def with_error_handling(func: Optional[Callable] = None, *, 
                       context: str = "", 
                       critical: bool = False,
                       graceful: bool = False) -> Callable:
    """
    Decorator for consistent error handling
    
    Args:
        context: Context description for error messages
        critical: Whether this error should terminate the application
        graceful: Whether to perform graceful shutdown on error
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                error_context = context or f.__name__
                
                if critical:
                    handle_critical_error(e, f"Critical error in {error_context}")
                elif graceful:
                    handle_graceful_shutdown(e, f"Graceful shutdown from {error_context}")
                else:
                    log_and_continue(e, error_context)
                    raise
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


# ===== LLM Helper Functions =====

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