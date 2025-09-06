"""
Unified LLM client that provides a simplified interface
"""

from typing import Dict, Any, Optional

from .models import GenerationRequest, GenerationResponse, LLMConfig
from .factory import LLMProviderFactory
from .providers import LLMProvider
from src.utils.logging_utils import get_logger
# from src.utils.prompt_templates import PromptTemplates  # Removed to avoid circular import

logger = get_logger(__name__)


class LLMClient:
    """
    Unified LLM client that provides a simplified interface to various LLM providers
    
    This class maintains backward compatibility with the original API while using
    the new modular architecture internally.
    """
    
    def __init__(self, provider: str = "openai", api_key: str = None, 
                 base_url: str = None, model: str = "gpt-3.5-turbo",
                 max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize LLM client with provider configuration"""
        self.provider_name = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Set default models based on provider
        if model == "gpt-3.5-turbo" and provider != "openai":
            if provider == "deepseek":
                self.model = "deepseek-chat"
            elif provider == "dify":
                self.model = "dify_model"
        
        # Create provider using factory
        self.provider = self._create_provider()
    
    def _create_provider(self) -> LLMProvider:
        """Create provider using the factory"""
        config = LLMConfig(
            provider_name=self.provider_name,
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            retry_enabled=True,
            logging_enabled=True
        )
        
        return LLMProviderFactory.create_provider(config)
    
    def generate_test(self, prompt: str, max_tokens: int = 2000, 
                     temperature: float = 0.3, language: str = "c") -> Dict[str, Any]:
        """
        Generate test code using LLM (backward compatible API)
        
        Args:
            prompt: The generation prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            language: Programming language (c, c++)
            
        Returns:
            Dictionary with generation results for backward compatibility
        """
        try:
            # Create generation request
            request = GenerationRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                language=language
            )
            
            # Generate using provider
            response = self.provider.generate(request)
            
            # Convert to backward compatible format
            result = response.to_dict()
            
            # Add metadata for compatibility
            if response.success:
                result['function_name'] = ""  # Will be filled by caller
                result['prompt_length'] = len(prompt)
                result['test_length'] = len(response.content)
                result['prompt'] = prompt
            else:
                result['prompt'] = prompt
            
            return result
            
        except Exception as e:
            logger.error(f"Error in generate_test: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_code': '',
                'usage': {},
                'prompt': prompt
            }
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate using the new API (direct provider access)
        
        Args:
            request: Generation request object
            
        Returns:
            Generation response object
        """
        return self.provider.generate(request)
    
    @property
    def provider(self) -> LLMProvider:
        """Get the underlying provider"""
        return self._provider
    
    @provider.setter
    def provider(self, value: LLMProvider) -> None:
        """Set the underlying provider"""
        self._provider = value
    
    def set_provider(self, provider: LLMProvider) -> None:
        """Set a custom provider (for dependency injection)"""
        self._provider = provider
        logger.info(f"Set custom provider: {provider.provider_name}")
    
    @classmethod
    def create_from_config(cls, config: LLMConfig) -> 'LLMClient':
        """Create client from configuration object"""
        client = cls.__new__(cls)
        client.provider_name = config.provider_name
        client.api_key = config.api_key
        client.base_url = config.base_url
        client.model = config.model
        client.max_retries = config.max_retries
        client.retry_delay = config.retry_delay
        client._provider = LLMProviderFactory.create_provider(config)
        return client
    
    @classmethod
    def create_mock_client(cls, model: str = "mock-model") -> 'LLMClient':
        """Create a mock client for testing"""
        return cls(provider="mock", model=model)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        return {
            'provider_name': self.provider_name,
            'model': self.model,
            'provider_class': self.provider.__class__.__name__,
            'decorators': self._get_decorator_chain()
        }
    
    def _get_decorator_chain(self) -> list[str]:
        """Get the decorator chain applied to the provider"""
        decorators = []
        current = self.provider
        
        while hasattr(current, 'provider'):
            decorators.append(current.__class__.__name__)
            current = current.provider
        
        decorators.append(current.__class__.__name__)  # Base provider
        return decorators