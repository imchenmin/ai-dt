"""
Test LLM provider implementations
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.llm.providers import LLMProvider, OpenAIProvider, DeepSeekProvider, DifyProvider
from src.llm.models import GenerationRequest, GenerationResponse, TokenUsage


class TestLLMProvider:
    """Test abstract LLM provider base class"""

    def test_abstract_class(self):
        """Test that LLMProvider cannot be instantiated directly"""
        with pytest.raises(TypeError):
            LLMProvider()


class TestOpenAIProvider:
    """Test OpenAI provider implementation"""

    def test_init(self):
        """Test provider initialization"""
        provider = OpenAIProvider("test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.timeout == 300.0

    def test_init_with_custom_values(self):
        """Test provider initialization with custom values"""
        provider = OpenAIProvider(
            api_key="custom-key",
            base_url="https://custom.api.com/v1",
            model="gpt-4",
            timeout=600.0
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.api.com/v1"
        assert provider.model == "gpt-4"
        assert provider.timeout == 600.0

    def test_provider_name(self):
        """Test provider name property"""
        provider = OpenAIProvider("test-key")
        assert provider.provider_name == "openai"

    @patch('src.llm.providers.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful generation"""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Generated test code"
                }
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_post.return_value = mock_response

        # Create provider and request
        provider = OpenAIProvider("test-key")
        request = GenerationRequest(
            prompt="Write unit tests",
            max_tokens=1000,
            temperature=0.7,
            language="python",
            system_prompt="You are a test assistant"
        )

        # Generate response
        response = provider.generate(request)

        assert response.success is True
        assert response.content == "Generated test code"
        assert response.model == "gpt-3.5-turbo"
        assert response.provider == "openai"
        assert response.usage.prompt_tokens == 100
        assert response.usage.completion_tokens == 50
        assert response.usage.total_tokens == 150

    @patch('src.llm.providers.requests.post')
    def test_generate_network_error(self, mock_post):
        """Test generation with network error"""
        # Mock network error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        provider = OpenAIProvider("test-key")
        request = GenerationRequest(prompt="Test")

        response = provider.generate(request)

        assert response.success is False
        assert "Network error" in response.error
        assert response.model == "gpt-3.5-turbo"
        assert response.provider == "openai"

    @patch('src.llm.providers.requests.post')
    def test_generate_timeout_error(self, mock_post):
        """Test generation with timeout error"""
        # Mock timeout error
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        provider = OpenAIProvider("test-key")
        request = GenerationRequest(prompt="Test")

        response = provider.generate(request)

        assert response.success is False
        assert "Network error" in response.error
        assert response.provider == "openai"

    @patch('src.llm.providers.requests.post')
    def test_generate_http_error(self, mock_post):
        """Test generation with HTTP error"""
        # Mock HTTP error
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-key")
        request = GenerationRequest(prompt="Test")

        response = provider.generate(request)

        assert response.success is False
        assert "Network error" in response.error

    @patch('src.llm.providers.requests.post')
    def test_generate_invalid_response_format(self, mock_post):
        """Test generation with invalid response format"""
        # Mock invalid response (no choices)
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"usage": {}}
        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-key")
        request = GenerationRequest(prompt="Test", system_prompt="System")

        response = provider.generate(request)

        assert response.success is False
        assert "No choices" in response.error

    @patch('src.llm.providers.requests.post')
    def test_generate_empty_content(self, mock_post):
        """Test generation with empty content"""
        # Mock response with empty content
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": ""
                }
            }],
            "usage": {}
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-key")
        request = GenerationRequest(prompt="Test", system_prompt="System")

        response = provider.generate(request)

        assert response.success is False
        assert "Empty content" in response.error

    @patch('src.llm.providers.requests.post')
    def test_generate_json_decode_error(self, mock_post):
        """Test generation with invalid JSON response"""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-key")
        request = GenerationRequest(prompt="Test", system_prompt="System")

        response = provider.generate(request)

        assert response.success is False
        assert "Invalid response" in response.error

    @patch('src.llm.providers.requests.post')
    def test_make_request_headers_and_data(self, mock_post):
        """Test that request is made with correct headers and data"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {}
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-key", model="gpt-4")
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=500,
            temperature=0.5,
            language="c",
            system_prompt="System prompt"
        )

        provider.generate(request)

        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL
        assert call_args[0][0] == "https://api.openai.com/v1/chat/completions"

        # Check headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-key'
        assert headers['Content-Type'] == 'application/json'

        # Check data
        data = call_args[1]['json']
        assert data['model'] == 'gpt-4'
        assert data['max_tokens'] == 500
        assert data['temperature'] == 0.5
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'system'
        assert data['messages'][1]['role'] == 'user'
        assert data['messages'][1]['content'] == 'Test prompt'


class TestDeepSeekProvider:
    """Test DeepSeek provider implementation"""

    def test_init(self):
        """Test provider initialization"""
        provider = DeepSeekProvider("test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.deepseek.com/v1"
        assert provider.model == "deepseek-chat"
        assert provider.timeout == 300.0

    def test_init_with_custom_values(self):
        """Test provider initialization with custom values"""
        provider = DeepSeekProvider(
            api_key="custom-key",
            base_url="https://custom.deepseek.com/v1",
            model="deepseek-coder",
            timeout=400.0
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.deepseek.com/v1"
        assert provider.model == "deepseek-coder"
        assert provider.timeout == 400.0

    def test_provider_name(self):
        """Test provider name property"""
        provider = DeepSeekProvider("test-key")
        assert provider.provider_name == "deepseek"

    @patch('src.llm.providers.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful generation"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "DeepSeek generated code"
                }
            }],
            "usage": {
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "total_tokens": 300
            }
        }
        mock_post.return_value = mock_response

        provider = DeepSeekProvider("test-key")
        request = GenerationRequest(
            prompt="Write C++ code",
            max_tokens=2000,
            temperature=0.3,
            language="cpp",
            system_prompt="You are a coding assistant"
        )

        response = provider.generate(request)

        assert response.success is True
        assert response.content == "DeepSeek generated code"
        assert response.model == "deepseek-chat"
        assert response.provider == "deepseek"
        assert response.usage.prompt_tokens == 200
        assert response.usage.completion_tokens == 100
        assert response.usage.total_tokens == 300

    @patch('src.llm.providers.requests.post')
    def test_generate_network_error(self, mock_post):
        """Test generation with network error"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        provider = DeepSeekProvider("test-key")
        request = GenerationRequest(prompt="Test")

        response = provider.generate(request)

        assert response.success is False
        assert "Network error" in response.error
        assert response.provider == "deepseek"

    @patch('src.llm.providers.requests.post')
    def test_make_request_url(self, mock_post):
        """Test that request is made to correct URL"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {}
        }
        mock_post.return_value = mock_response

        provider = DeepSeekProvider("test-key")
        request = GenerationRequest(prompt="Test", system_prompt="System")

        provider.generate(request)

        call_args = mock_post.call_args
        url = call_args[0][0]
        assert url == "https://api.deepseek.com/v1/chat/completions"


class TestDifyProvider:
    """Test Dify provider implementation"""

    def test_init(self):
        """Test provider initialization"""
        provider = DifyProvider("test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.dify.ai/v1/chat-messages"
        assert provider.model == "dify_model"
        assert provider.timeout == 300.0

    def test_init_with_custom_values(self):
        """Test provider initialization with custom values"""
        provider = DifyProvider(
            api_key="custom-key",
            base_url="https://custom.dify.com/v1",
            model="custom_model",
            timeout=500.0
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.dify.com/v1"
        assert provider.model == "custom_model"
        assert provider.timeout == 500.0

    def test_provider_name(self):
        """Test provider name property"""
        provider = DifyProvider("test-key")
        assert provider.provider_name == "dify"

    @patch('src.llm.providers.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful generation"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "answer": "Dify generated response",
            "model": "dify-model",
            "metadata": {
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 75,
                    "total_tokens": 225
                }
            }
        }
        mock_post.return_value = mock_response

        provider = DifyProvider("test-key")
        request = GenerationRequest(prompt="Test prompt")

        response = provider.generate(request)

        assert response.success is True
        assert response.content == "Dify generated response"
        assert response.model == "dify-model"
        assert response.provider == "dify"
        assert response.usage.prompt_tokens == 150
        assert response.usage.completion_tokens == 75
        assert response.usage.total_tokens == 225

    @patch('src.llm.providers.requests.post')
    def test_generate_network_error(self, mock_post):
        """Test generation with network error"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        provider = DifyProvider("test-key")
        request = GenerationRequest(prompt="Test")

        response = provider.generate(request)

        assert response.success is False
        assert "Network error" in response.error
        assert response.provider == "dify"

    @patch('src.llm.providers.requests.post')
    def test_generate_missing_answer(self, mock_post):
        """Test generation with missing answer in response"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        provider = DifyProvider("test-key")
        request = GenerationRequest(prompt="Test")

        response = provider.generate(request)

        assert response.success is False
        assert "missing 'answer' key" in response.error

    @patch('src.llm.providers.requests.post')
    def test_make_request_correct_data(self, mock_post):
        """Test that request is made with correct data structure"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "answer": "Response",
            "metadata": {"usage": {}}
        }
        mock_post.return_value = mock_response

        provider = DifyProvider("test-key", base_url="https://custom.dify.com/v1")
        request = GenerationRequest(prompt="Test prompt")

        provider.generate(request)

        call_args = mock_post.call_args

        # Check URL
        assert call_args[0][0] == "https://custom.dify.com/v1"

        # Check headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-key'
        assert headers['Content-Type'] == 'application/json'

        # Check data structure
        data = call_args[1]['json']
        assert data['inputs'] == {}
        assert data['query'] == "Test prompt"
        assert data['response_mode'] == "blocking"
        assert data['user'] == "ai-dt-user"


class TestProviderCommonPatterns:
    """Test common patterns across providers"""

    def test_provider_inheritance(self):
        """Test that all providers inherit from LLMProvider"""
        assert issubclass(OpenAIProvider, LLMProvider)
        assert issubclass(DeepSeekProvider, LLMProvider)
        assert issubclass(DifyProvider, LLMProvider)

    def test_provider_interface(self):
        """Test that all providers implement required interface"""
        for provider_class in [OpenAIProvider, DeepSeekProvider, DifyProvider]:
            provider = provider_class("test-key")

            # Must have provider_name property
            assert hasattr(provider, 'provider_name')
            assert isinstance(provider.provider_name, str)

            # Must have generate method
            assert hasattr(provider, 'generate')
            assert callable(getattr(provider, 'generate'))

    @patch('src.llm.providers.requests.post')
    def test_provider_timeout_configuration(self, mock_post):
        """Test that timeout is properly configured"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {}
        }
        mock_post.return_value = mock_response

        # Test with custom timeout
        provider = OpenAIProvider("test-key", timeout=120.0)
        request = GenerationRequest(prompt="Test", system_prompt="")

        provider.generate(request)

        # Verify timeout was passed to requests
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == 120.0

    @patch('src.llm.providers.requests.post')
    def test_provider_with_custom_base_url(self, mock_post):
        """Test provider with custom base URL"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {}
        }
        mock_post.return_value = mock_response

        custom_url = "https://custom.proxy.com/v1"
        provider = OpenAIProvider("test-key", base_url=custom_url)
        request = GenerationRequest(prompt="Test", system_prompt="")

        provider.generate(request)

        # Verify custom URL was used
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert url == f"{custom_url}/chat/completions"