"""
Centralized error handling for consistent error management across the application
"""

import logging
import sys
from typing import Optional, Callable, Any
from functools import wraps

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """Centralized error handling with configurable strategies"""
    
    def __init__(self, 
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 backoff_factor: float = 2.0,
                 max_delay: float = 60.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
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