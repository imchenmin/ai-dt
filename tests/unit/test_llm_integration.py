"""
Tests for LLM components (models, factory, client)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.llm.models import (
    TokenUsage,
    GenerationRequest,
    GenerationResponse,
    LLMConfig
)
from src.llm.factory import LLMProviderFactory
from src.llm.client import LLMClient
from src.llm.providers import LLMProvider, MockProvider


class TestTokenUsage:
    """Test cases for TokenUsage model"""
    
    def test_creation_with_all_values(self):
        """Test TokenUsage creation with all values"""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
    
    def test_creation_auto_calculate_total(self):
        """Test TokenUsage auto-calculates total tokens"""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50
        )
        
        assert usage.total_tokens == 150
    
    def test_creation_defaults(self):
        """Test TokenUsage with default values"""
        usage = TokenUsage()
        
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0


class TestGenerationRequest:
    """Test cases for GenerationRequest model"""
    
    def test_creation_with_required_fields(self):
        """Test GenerationRequest creation with required fields"""
        request = GenerationRequest(prompt="Test prompt")
        
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 2000
        assert request.temperature == 0.3
        assert request.language == "c"
        assert request.system_prompt is None
    
    def test_creation_with_all_fields(self):
        """Test GenerationRequest creation with all fields"""
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=1000,
            temperature=0.7,
            language="cpp",
            system_prompt="You are a test generator"
        )
        
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7
        assert request.language == "cpp"
        assert request.system_prompt == "You are a test generator"
    
    def test_validation_max_tokens_positive(self):
        """Test max_tokens validation"""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            GenerationRequest(prompt="Test", max_tokens=0)
        
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            GenerationRequest(prompt="Test", max_tokens=-1)
    
    def test_validation_temperature_range(self):
        """Test temperature validation"""
        with pytest.raises(ValueError, match="temperature must be between 0 and 2"):
            GenerationRequest(prompt="Test", temperature=-0.1)
        
        with pytest.raises(ValueError, match="temperature must be between 0 and 2"):
            GenerationRequest(prompt="Test", temperature=2.1)
    
    def test_validation_empty_prompt(self):
        """Test empty prompt validation"""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            GenerationRequest(prompt="")
        
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            GenerationRequest(prompt="   ")


class TestGenerationResponse:
    """Test cases for GenerationResponse model"""
    
    def test_creation_success(self):
        """Test successful GenerationResponse creation"""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        response = GenerationResponse(
            success=True,
            content="Generated test code",
            usage=usage,
            model="gpt-3.5-turbo",
            provider="openai"
        )
        
        assert response.success is True
        assert response.content == "Generated test code"
        assert response.usage == usage
        assert response.model == "gpt-3.5-turbo"
        assert response.provider == "openai"
        assert response.error is None
    
    def test_creation_failure(self):
        """Test failed GenerationResponse creation"""
        response = GenerationResponse(
            success=False,
            error="API rate limit exceeded",
            provider="openai"
        )
        
        assert response.success is False
        assert response.content == ""
        assert response.error == "API rate limit exceeded"
        assert response.provider == "openai"
        assert isinstance(response.usage, TokenUsage)  # Auto-created
    
    def test_auto_usage_creation(self):
        """Test auto-creation of TokenUsage when None"""
        response = GenerationResponse(success=True)
        
        assert isinstance(response.usage, TokenUsage)
        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0
    
    def test_to_dict_success(self):
        """Test to_dict conversion for successful response"""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        response = GenerationResponse(
            success=True,
            content="TEST(Test, function) {}",
            usage=usage,
            model="gpt-3.5-turbo"
        )
        
        result = response.to_dict()
        
        expected = {
            'success': True,
            'test_code': "TEST(Test, function) {}",
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            },
            'model': "gpt-3.5-turbo",
            'error': None
        }
        
        assert result == expected
    
    def test_to_dict_failure(self):
        """Test to_dict conversion for failed response"""
        response = GenerationResponse(
            success=False,
            error="Generation failed"
        )
        
        result = response.to_dict()
        
        assert result['success'] is False
        assert result['test_code'] == ""
        assert result['error'] == "Generation failed"
        assert result['usage']['prompt_tokens'] == 0


class TestLLMConfig:
    """Test cases for LLMConfig model"""
    
    def test_creation_with_required_fields(self):
        """Test LLMConfig creation with required fields"""
        config = LLMConfig(provider_name="openai")
        
        assert config.provider_name == "openai"
        assert config.api_key is None
        assert config.base_url is None
        assert config.model == "gpt-3.5-turbo"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout == 300.0
        assert config.rate_limit is None
        assert config.curl_file_path is None
        assert config.retry_enabled is True
        assert config.rate_limit_enabled is False
        assert config.logging_enabled is True
    
    def test_creation_with_all_fields(self):
        """Test LLMConfig creation with all fields"""
        config = LLMConfig(
            provider_name="deepseek",
            api_key="test_key",
            base_url="https://api.deepseek.com",
            model="deepseek-coder",
            max_retries=5,
            retry_delay=2.0,
            timeout=600.0,
            rate_limit=10.0,
            curl_file_path="/path/to/curl/file.txt",
            retry_enabled=False,
            rate_limit_enabled=True,
            logging_enabled=False
        )
        
        assert config.provider_name == "deepseek"
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.deepseek.com"
        assert config.model == "deepseek-coder"
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.timeout == 600.0
        assert config.rate_limit == 10.0
        assert config.curl_file_path == "/path/to/curl/file.txt"
        assert config.retry_enabled is False
        assert config.rate_limit_enabled is True
        assert config.logging_enabled is False
    
    def test_validation_max_retries(self):
        """Test max_retries validation"""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            LLMConfig(provider_name="test", max_retries=-1)
    
    def test_validation_retry_delay(self):
        """Test retry_delay validation"""
        with pytest.raises(ValueError, match="retry_delay must be non-negative"):
            LLMConfig(provider_name="test", retry_delay=-1.0)
    
    def test_validation_timeout(self):
        """Test timeout validation"""
        with pytest.raises(ValueError, match="timeout must be positive"):
            LLMConfig(provider_name="test", timeout=0)
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            LLMConfig(provider_name="test", timeout=-10)
    
    def test_curl_file_path_for_dify_web(self):
        """Test curl_file_path field specifically for dify_web provider"""
        # Test with dify_web provider and curl_file_path
        config = LLMConfig(
            provider_name="dify_web",
            curl_file_path="/path/to/dify.curl"
        )
        
        assert config.provider_name == "dify_web"
        assert config.curl_file_path == "/path/to/dify.curl"
        
        # Test with other provider and curl_file_path (should still work)
        config2 = LLMConfig(
            provider_name="openai",
            curl_file_path="/some/curl/file.txt"
        )
        
        assert config2.provider_name == "openai"
        assert config2.curl_file_path == "/some/curl/file.txt"
    
    def test_curl_file_path_none_by_default(self):
        """Test that curl_file_path is None by default"""
        config = LLMConfig(provider_name="test")
        assert config.curl_file_path is None
    
    def test_curl_file_path_empty_string(self):
        """Test curl_file_path with empty string"""
        config = LLMConfig(
            provider_name="dify_web",
            curl_file_path=""
        )
        
        assert config.curl_file_path == ""


class TestLLMProviderFactory:
    """Test cases for LLMProviderFactory"""
    
    def test_get_available_providers(self):
        """Test getting available providers"""
        providers = LLMProviderFactory.get_available_providers()
        
        assert 'openai' in providers
        assert 'deepseek' in providers
        assert 'dify' in providers
        assert 'mock' in providers
    
    def test_create_mock_provider(self):
        """Test creating mock provider"""
        config = LLMConfig(
            provider_name="mock",
            model="test-model"
        )
        
        provider = LLMProviderFactory.create_provider(config)
        
        assert provider is not None
        # Should be wrapped with decorators
        assert hasattr(provider, 'provider')  # Has decorator chain
    
    @patch('src.llm.factory.LLMProviderFactory._PROVIDERS')
    def test_create_openai_provider(self, mock_providers):
        """Test creating OpenAI provider"""
        mock_openai_class = Mock()
        mock_base_provider = Mock(spec=LLMProvider)
        mock_openai_class.return_value = mock_base_provider
        
        # Mock the provider registry
        mock_providers.get.return_value = mock_openai_class
        
        config = LLMConfig(
            provider_name="openai",
            api_key="test_key",
            model="gpt-3.5-turbo"
        )
        
        provider = LLMProviderFactory.create_provider(config)
        
        mock_openai_class.assert_called_once_with(
            api_key="test_key",
            base_url=None,
            model="gpt-3.5-turbo",
            timeout=300.0
        )
        assert provider is not None
    
    def test_create_provider_unknown(self):
        """Test creating unknown provider raises error"""
        config = LLMConfig(provider_name="unknown")
        
        with pytest.raises(ValueError, match="Unknown provider: unknown"):
            LLMProviderFactory.create_provider(config)
    
    def test_create_provider_no_api_key(self):
        """Test creating real provider without API key raises error"""
        config = LLMConfig(provider_name="openai")  # No API key
        
        with pytest.raises(ValueError, match="API key required for provider: openai"):
            LLMProviderFactory.create_provider(config)
    
    def test_create_dify_web_provider_with_curl_file_path(self):
        """Test creating dify_web provider with curl_file_path"""
        import tempfile
        import os
        
        # Create a temporary curl file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.curl', delete=False) as f:
            f.write('curl "https://example.com/api" -H "Content-Type: application/json" --data-raw "{\"query\":\"test\"}"')
            curl_file_path = f.name
        
        try:
            config = LLMConfig(
                provider_name="dify_web",
                curl_file_path=curl_file_path
            )
            
            provider = LLMProviderFactory.create_provider(config)
            assert provider is not None
            assert "dify_web" in provider.provider_name  # Provider name includes decorators
            
            # Access the base provider through the decorator chain
            base_provider = provider
            while hasattr(base_provider, 'provider'):
                base_provider = base_provider.provider
            
            assert base_provider.curl_file_path == curl_file_path
        finally:
            os.unlink(curl_file_path)
    
    def test_create_dify_web_provider_no_curl_file_path(self):
        """Test creating dify_web provider without curl_file_path raises error"""
        config = LLMConfig(provider_name="dify_web")  # No curl_file_path
        
        with pytest.raises(ValueError, match="curl_file_path required for provider: dify_web"):
            LLMProviderFactory.create_provider(config)
    
    def test_create_dify_web_provider_with_api_key_fallback(self):
        """Test creating dify_web provider using api_key as fallback for curl_file_path"""
        import tempfile
        import os
        
        # Create a temporary curl file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.curl', delete=False) as f:
            f.write('curl "https://example.com/api" -H "Content-Type: application/json" --data-raw "{\"query\":\"test\"}"')
            curl_file_path = f.name
        
        try:
            config = LLMConfig(
                provider_name="dify_web",
                api_key=curl_file_path  # Using api_key as fallback
            )
            
            provider = LLMProviderFactory.create_provider(config)
            assert provider is not None
            assert "dify_web" in provider.provider_name  # Provider name includes decorators
            
            # Access the base provider through the decorator chain
            base_provider = provider
            while hasattr(base_provider, 'provider'):
                base_provider = base_provider.provider
            
            assert base_provider.curl_file_path == curl_file_path
        finally:
            os.unlink(curl_file_path)
    
    def test_register_provider(self):
        """Test registering custom provider"""
        class CustomProvider(LLMProvider):
            pass
        
        LLMProviderFactory.register_provider("custom", CustomProvider)
        
        providers = LLMProviderFactory.get_available_providers()
        assert "custom" in providers
    
    def test_register_invalid_provider(self):
        """Test registering invalid provider raises error"""
        class InvalidProvider:
            pass
        
        with pytest.raises(ValueError, match="Provider class must inherit from LLMProvider"):
            LLMProviderFactory.register_provider("invalid", InvalidProvider)
    
    def test_create_from_dict(self):
        """Test creating provider from dictionary"""
        config_dict = {
            'provider_name': 'mock',
            'model': 'test-model',
            'max_retries': 5,
            'retry_enabled': True,
            'logging_enabled': False
        }
        
        provider = LLMProviderFactory.create_from_dict(config_dict)
        
        assert provider is not None


class TestLLMClient:
    """Test cases for LLMClient"""
    
    def test_init_with_defaults(self):
        """Test LLMClient initialization with defaults"""
        # Use mock provider to avoid API key requirement
        client = LLMClient(provider="mock")
        
        assert client.provider_name == "mock"
        assert client.api_key is None
        assert client.base_url is None
        assert client.model == "gpt-3.5-turbo"  # Default model even for mock
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
    
    def test_init_with_custom_values(self):
        """Test LLMClient initialization with custom values"""
        client = LLMClient(
            provider="deepseek",
            api_key="test_key",
            base_url="https://api.deepseek.com",
            model="deepseek-coder",
            max_retries=5,
            retry_delay=2.0
        )
        
        assert client.provider_name == "deepseek"
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.deepseek.com"
        assert client.model == "deepseek-coder"
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
    
    def test_model_default_switching(self):
        """Test automatic model switching based on provider"""
        # DeepSeek provider should keep deepseek-chat
        client_deepseek = LLMClient(provider="deepseek", api_key="test_key", model="gpt-3.5-turbo")
        assert client_deepseek.model == "deepseek-chat"
        
        # Dify provider should switch to dify_model
        client_dify = LLMClient(provider="dify", api_key="test_key", model="gpt-3.5-turbo")
        assert client_dify.model == "dify_model"
    
    @patch('src.llm.client.LLMProviderFactory.create_provider')
    def test_create_provider(self, mock_create_provider):
        """Test provider creation through factory"""
        mock_provider = Mock(spec=LLMProvider)
        mock_create_provider.return_value = mock_provider
        
        client = LLMClient(provider="mock", model="test-model")
        
        assert client.provider == mock_provider
        mock_create_provider.assert_called_once()
    
    def test_generate_test_success(self):
        """Test successful test generation"""
        client = LLMClient(provider="mock")
        
        # Mock the provider
        mock_provider = Mock(spec=LLMProvider)
        mock_response = GenerationResponse(
            success=True,
            content="TEST(Test, function) { ASSERT_TRUE(true); }",
            usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
            model="mock-model"
        )
        mock_provider.generate.return_value = mock_response
        client.provider = mock_provider
        
        result = client.generate_test(
            prompt="Generate test for function",
            max_tokens=2000,
            temperature=0.3,
            language="c"
        )
        
        assert result['success'] is True
        assert 'TEST(Test, function)' in result['test_code']
        assert result['usage']['prompt_tokens'] == 100
        assert result['model'] == 'mock-model'
        assert result['prompt_length'] == len("Generate test for function")
        assert result['test_length'] == len("TEST(Test, function) { ASSERT_TRUE(true); }")
    
    def test_generate_test_failure(self):
        """Test failed test generation"""
        client = LLMClient(provider="mock")
        
        # Mock the provider
        mock_provider = Mock(spec=LLMProvider)
        mock_response = GenerationResponse(
            success=False,
            error="API rate limit exceeded"
        )
        mock_provider.generate.return_value = mock_response
        client.provider = mock_provider
        
        result = client.generate_test(prompt="Generate test")
        
        assert result['success'] is False
        assert result['error'] == "API rate limit exceeded"
        assert result['test_code'] == ''
    
    def test_generate_test_exception(self):
        """Test test generation with exception"""
        client = LLMClient(provider="mock")
        
        # Mock the provider to raise exception
        mock_provider = Mock(spec=LLMProvider)
        mock_provider.generate.side_effect = Exception("Network error")
        client.provider = mock_provider
        
        result = client.generate_test(prompt="Generate test")
        
        assert result['success'] is False
        assert "Network error" in result['error']
        assert result['test_code'] == ''
    
    def test_generate_new_api(self):
        """Test generate method with new API"""
        client = LLMClient(provider="mock")
        
        # Mock the provider
        mock_provider = Mock(spec=LLMProvider)
        mock_response = GenerationResponse(success=True, content="test code")
        mock_provider.generate.return_value = mock_response
        client.provider = mock_provider
        
        request = GenerationRequest(prompt="test prompt")
        response = client.generate(request)
        
        assert response == mock_response
        mock_provider.generate.assert_called_once_with(request)
    
    def test_set_provider(self):
        """Test setting custom provider"""
        client = LLMClient(provider="mock")
        custom_provider = Mock(spec=LLMProvider)
        custom_provider.provider_name = "custom"
        
        client.set_provider(custom_provider)
        
        assert client.provider == custom_provider
    
    def test_create_from_config(self):
        """Test creating client from config"""
        config = LLMConfig(
            provider_name="mock",
            model="test-model",
            max_retries=5
        )
        
        client = LLMClient.create_from_config(config)
        
        assert client.provider_name == "mock"
        assert client.model == "test-model"
        assert client.max_retries == 5
    
    def test_create_from_config_with_curl_file_path(self):
        """Test creating client from config with curl_file_path for dify_web"""
        import tempfile
        import os
        
        # Create a temporary curl file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.curl', delete=False) as f:
            f.write('curl "https://example.com/api" -H "Content-Type: application/json" --data-raw "{\"query\":\"test\"}"')
            curl_file_path = f.name
        
        try:
            config = LLMConfig(
                provider_name="dify_web",
                model="dify_web_model",
                curl_file_path=curl_file_path
            )
            
            client = LLMClient.create_from_config(config)
            
            assert client.provider_name == "dify_web"
            assert client.model == "dify_web_model"
            
            # Access the base provider through the decorator chain
            base_provider = client.provider
            while hasattr(base_provider, 'provider'):
                base_provider = base_provider.provider
            
            assert base_provider.curl_file_path == curl_file_path
        finally:
            os.unlink(curl_file_path)
    
    def test_create_mock_client(self):
        """Test creating mock client"""
        client = LLMClient.create_mock_client("custom-model")
        
        assert client.provider_name == "mock"
        assert client.model == "custom-model"
    
    def test_get_provider_info(self):
        """Test getting provider information"""
        client = LLMClient(provider="mock", model="test-model")
        
        info = client.get_provider_info()
        
        assert info['provider_name'] == "mock"
        assert info['model'] == "test-model"
        assert 'provider_class' in info
        assert 'decorators' in info
    
    def test_get_decorator_chain(self):
        """Test getting decorator chain"""
        client = LLMClient(provider="mock")
        
        decorators = client._get_decorator_chain()
        
        assert isinstance(decorators, list)
        assert len(decorators) > 0  # Should have at least the base provider