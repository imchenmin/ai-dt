"""
Unit tests for TokenCounter utility
"""

import pytest
from unittest.mock import patch, MagicMock
from src.utils.token_counter import TokenCounter, TIKTOKEN_AVAILABLE


def test_token_counter_initialization():
    """Test TokenCounter initialization with different providers"""
    # Test with OpenAI
    counter = TokenCounter("openai", "gpt-3.5-turbo")
    assert counter.provider == "openai"
    assert counter.model == "gpt-3.5-turbo"
    
    # Test with DeepSeek
    counter = TokenCounter("deepseek", "deepseek-chat")
    assert counter.provider == "deepseek"
    assert counter.model == "deepseek-chat"
    
    # Test with mock
    counter = TokenCounter("mock", "mock")
    assert counter.provider == "mock"
    assert counter.model == "mock"


def test_count_tokens_with_tiktoken():
    """Test token counting when tiktoken is available"""
    if not TIKTOKEN_AVAILABLE:
        pytest.skip("tiktoken not available")
    
    counter = TokenCounter("openai", "gpt-3.5-turbo")
    
    # Test basic text
    text = "Hello world"
    token_count = counter.count_tokens(text)
    assert isinstance(token_count, int)
    assert token_count > 0
    
    # Test empty text
    assert counter.count_tokens("") == 0
    
    # Test longer text
    long_text = " " * 100
    assert counter.count_tokens(long_text) > 0


def test_count_tokens_without_tiktoken():
    """Test token counting fallback when tiktoken is not available"""
    with patch('src.utils.token_counter.TIKTOKEN_AVAILABLE', False):
        counter = TokenCounter("openai", "gpt-3.5-turbo")
        
        # Test basic text
        text = "Hello world"  # 11 characters
        token_count = counter.count_tokens(text)
        assert token_count == 2  # 11 // 4 = 2 (integer division)
        
        # Test empty text
        assert counter.count_tokens("") == 0
        
        # Test exact multiple
        text = "x" * 8  # 8 characters
        assert counter.count_tokens(text) == 2  # 8 // 4 = 2


def test_count_tokens_from_dict():
    """Test token counting from dictionary"""
    counter = TokenCounter("openai", "gpt-3.5-turbo")
    
    test_data = {
        "name": "test_function",
        "params": [{"name": "x", "type": "int"}],
        "return_type": "int"
    }
    
    token_count = counter.count_tokens_from_dict(test_data)
    assert isinstance(token_count, int)
    assert token_count > 0


def test_get_model_limit():
    """Test getting model token limits"""
    # Test known models
    counter = TokenCounter("openai", "gpt-3.5-turbo")
    assert counter.get_model_limit() == 4096
    
    counter = TokenCounter("openai", "gpt-4")
    assert counter.get_model_limit() == 8192
    
    counter = TokenCounter("deepseek", "deepseek-chat")
    assert counter.get_model_limit() == 128000
    
    # Test unknown model fallback
    counter = TokenCounter("unknown", "unknown")
    assert counter.get_model_limit() == 4000


def test_get_available_tokens():
    """Test calculating available tokens"""
    counter = TokenCounter("openai", "gpt-3.5-turbo")
    
    # Test with no base prompt
    available = counter.get_available_tokens()
    expected = int(4096 * 0.8)  # 80% of limit
    assert available == expected
    
    # Test with base prompt
    available_with_base = counter.get_available_tokens(1000)
    assert available_with_base == available - 1000
    
    # Test minimum context size
    counter = TokenCounter("openai", "gpt-3.5-turbo")
    # Force very small available tokens
    available = counter.get_available_tokens(4000)
    assert available >= 500  # Should respect minimum


def test_estimate_tokens_static():
    """Test static token estimation method"""
    # Test basic estimation
    assert TokenCounter.estimate_tokens("Hello") == 1  # 5 // 4 = 1
    assert TokenCounter.estimate_tokens("Hello world") == 2  # 11 // 4 = 2
    assert TokenCounter.estimate_tokens("") == 0
    
    # Test exact multiples
    assert TokenCounter.estimate_tokens("x" * 4) == 1
    assert TokenCounter.estimate_tokens("x" * 8) == 2


def test_create_token_counter_factory():
    """Test token counter factory function"""
    from src.utils.token_counter import create_token_counter
    
    counter = create_token_counter("openai", "gpt-3.5-turbo")
    assert isinstance(counter, TokenCounter)
    assert counter.provider == "openai"
    assert counter.model == "gpt-3.5-turbo"
    
    counter = create_token_counter("deepseek", "deepseek-coder")
    assert counter.provider == "deepseek"
    assert counter.model == "deepseek-coder"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])