"""
Factory for creating configured LLM providers
"""

from typing import Dict, Type

from .providers import LLMProvider, OpenAIProvider, DeepSeekProvider, DifyProvider, MockProvider
from .decorators import RetryDecorator, RateLimitDecorator, LoggingDecorator, ValidationDecorator
from .models import LLMConfig
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LLMProviderFactory:
    """Factory for creating and configuring LLM providers"""
    
    # Registry of available providers
    _PROVIDERS: Dict[str, Type[LLMProvider]] = {
        'openai': OpenAIProvider,
        'deepseek': DeepSeekProvider,
        'dify': DifyProvider,
        'mock': MockProvider
    }
    
    @staticmethod
    def create_provider(config: LLMConfig) -> LLMProvider:
        """Create a configured LLM provider with decorators"""
        # Create base provider
        base_provider = LLMProviderFactory._create_base_provider(config)
        
        # Apply decorators in order
        provider = base_provider
        
        # Always add validation
        provider = ValidationDecorator(provider)
        
        # Add logging if enabled
        if config.logging_enabled:
            provider = LoggingDecorator(provider)
        
        # Add retry if enabled
        if config.retry_enabled and config.max_retries > 0:
            provider = RetryDecorator(
                provider, 
                max_retries=config.max_retries,
                retry_delay=config.retry_delay
            )
        
        # Add rate limiting if enabled
        if config.rate_limit_enabled and config.rate_limit:
            provider = RateLimitDecorator(provider, config.rate_limit)
        
        logger.info(f"Created {config.provider_name} provider with decorators: "
                   f"validation={True}, logging={config.logging_enabled}, "
                   f"retry={config.retry_enabled}, rate_limit={config.rate_limit_enabled}")
        
        return provider
    
    @staticmethod
    def _create_base_provider(config: LLMConfig) -> LLMProvider:
        """Create the base provider instance"""
        provider_class = LLMProviderFactory._PROVIDERS.get(config.provider_name.lower())
        
        if not provider_class:
            available = ', '.join(LLMProviderFactory._PROVIDERS.keys())
            raise ValueError(f"Unknown provider: {config.provider_name}. "
                           f"Available providers: {available}")
        
        # Handle mock provider (no API key needed)
        if config.provider_name.lower() == 'mock':
            return provider_class(model=config.model)
        
        # Validate API key for real providers
        if not config.api_key:
            raise ValueError(f"API key required for provider: {config.provider_name}")
        
        # Create provider with configuration
        return provider_class(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            timeout=config.timeout
        )
    
    @staticmethod
    def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
        """Register a new provider type"""
        if not issubclass(provider_class, LLMProvider):
            raise ValueError("Provider class must inherit from LLMProvider")
        
        LLMProviderFactory._PROVIDERS[name.lower()] = provider_class
        logger.info(f"Registered new provider: {name}")
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider names"""
        return list(LLMProviderFactory._PROVIDERS.keys())
    
    @staticmethod
    def create_from_dict(config_dict: Dict) -> LLMProvider:
        """Create provider from dictionary configuration"""
        config = LLMConfig(
            provider_name=config_dict['provider_name'],
            api_key=config_dict.get('api_key'),
            base_url=config_dict.get('base_url'),
            model=config_dict.get('model', 'gpt-3.5-turbo'),
            max_retries=config_dict.get('max_retries', 3),
            retry_delay=config_dict.get('retry_delay', 1.0),
            timeout=config_dict.get('timeout', 300.0),
            rate_limit=config_dict.get('rate_limit'),
            retry_enabled=config_dict.get('retry_enabled', True),
            rate_limit_enabled=config_dict.get('rate_limit_enabled', False),
            logging_enabled=config_dict.get('logging_enabled', True)
        )
        
        return LLMProviderFactory.create_provider(config)