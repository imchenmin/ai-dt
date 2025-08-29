"""
Tests for the refactored architecture
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.llm.models import GenerationRequest, GenerationResponse, TokenUsage, LLMConfig
from src.llm.providers import MockProvider, OpenAIProvider, DeepSeekProvider
from src.llm.decorators import RetryDecorator, LoggingDecorator
from src.llm.factory import LLMProviderFactory
from src.llm.client import LLMClient

from src.test_generation.models import GenerationTask, TestGenerationConfig
from src.test_generation.strategies import SequentialExecution, ConcurrentExecution
from src.test_generation.components import PromptGenerator, CoreTestGenerator
from src.test_generation.orchestrator import TestGenerationOrchestrator
from src.test_generation.service import TestGenerationService


class TestLLMArchitecture:
    """Test the refactored LLM architecture"""
    
    def test_generation_request_validation(self):
        """Test GenerationRequest validation"""
        # Valid request
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.5
        )
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.temperature == 0.5
        
        # Invalid max_tokens
        with pytest.raises(ValueError):
            GenerationRequest(prompt="Test", max_tokens=-1)
        
        # Invalid temperature
        with pytest.raises(ValueError):
            GenerationRequest(prompt="Test", temperature=3.0)
        
        # Empty prompt
        with pytest.raises(ValueError):
            GenerationRequest(prompt="", max_tokens=100)
    
    def test_generation_response_to_dict(self):
        """Test GenerationResponse to_dict conversion"""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20)
        response = GenerationResponse(
            success=True,
            content="Generated content",
            usage=usage,
            model="test-model",
            provider="test-provider"
        )
        
        result_dict = response.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['test_code'] == "Generated content"
        assert result_dict['model'] == "test-model"
        assert result_dict['usage']['total_tokens'] == 30
    
    def test_mock_provider(self):
        """Test MockProvider functionality"""
        provider = MockProvider("test-model")
        
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.3
        )
        
        response = provider.generate(request)
        
        assert response.success is True
        assert "Mock test" in response.content
        assert response.model == "test-model"
        assert response.provider == "mock"
        assert response.usage.total_tokens > 0
    
    def test_retry_decorator(self):
        """Test RetryDecorator functionality"""
        # Create a mock provider that always succeeds
        mock_provider = Mock()
        mock_provider.provider_name = "test"
        mock_provider.generate.return_value = GenerationResponse(
            success=True, content="Success"
        )
        
        retry_provider = RetryDecorator(mock_provider, max_retries=3, retry_delay=0.1)
        
        request = GenerationRequest(prompt="Test prompt")
        response = retry_provider.generate(request)
        
        # Should succeed
        assert response.success is True
        assert response.content == "Success"
        assert mock_provider.generate.call_count == 1
    
    def test_llm_provider_factory(self):
        """Test LLMProviderFactory functionality"""
        # Test mock provider creation
        config = LLMConfig(
            provider_name="mock",
            model="test-model",
            retry_enabled=True,
            logging_enabled=True
        )
        
        provider = LLMProviderFactory.create_provider(config)
        
        # Should be wrapped with decorators
        assert hasattr(provider, 'provider')  # Wrapped provider
        
        # Test with invalid provider
        invalid_config = LLMConfig(provider_name="invalid")
        
        with pytest.raises(ValueError):
            LLMProviderFactory.create_provider(invalid_config)
    
    def test_llm_client_backward_compatibility(self):
        """Test LLMClient backward compatibility"""
        client = LLMClient.create_mock_client("test-model")
        
        result = client.generate_test(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.3,
            language="c"
        )
        
        # Should return dict in old format
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'test_code' in result
        assert 'usage' in result


class TestTestGenerationArchitecture:
    """Test the refactored test generation architecture"""
    
    def test_generation_task_creation(self):
        """Test GenerationTask creation"""
        function_info = {
            'name': 'test_function',
            'file': 'test.c',
            'language': 'c'
        }
        context = {'dependencies': []}
        
        task = GenerationTask(
            function_info=function_info,
            context=context,
            target_filepath="test_output.cpp",
            suite_name="TestSuite"
        )
        
        assert task.function_name == 'test_function'
        assert task.language == 'c'
        assert task.target_filepath == "test_output.cpp"
    
    def test_test_generation_config(self):
        """Test TestGenerationConfig creation"""
        config = TestGenerationConfig(
            project_name="test_project",
            output_dir="./output",
            max_workers=3,
            execution_strategy="concurrent"
        )
        
        assert config.project_name == "test_project"
        assert config.max_workers == 3
        assert config.execution_strategy == "concurrent"
        assert config.save_prompts is True  # Default
    
    def test_sequential_execution_strategy(self):
        """Test SequentialExecution strategy"""
        strategy = SequentialExecution(delay_between_requests=0.1)
        
        # Create mock tasks
        tasks = [
            GenerationTask(
                function_info={'name': f'func_{i}', 'language': 'c'},
                context={},
                target_filepath=f"test_{i}.cpp",
                suite_name=f"Test{i}"
            )
            for i in range(3)
        ]
        
        # Mock processor
        def mock_processor(task):
            from src.test_generation.models import GenerationResult
            return GenerationResult(
                task=task,
                success=True,
                test_code=f"// Test for {task.function_name}"
            )
        
        results = strategy.execute(tasks, mock_processor)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert strategy.strategy_name == "sequential"
    
    def test_concurrent_execution_strategy(self):
        """Test ConcurrentExecution strategy"""
        strategy = ConcurrentExecution(max_workers=2)
        
        # Create mock tasks
        tasks = [
            GenerationTask(
                function_info={'name': f'func_{i}', 'language': 'c'},
                context={},
                target_filepath=f"test_{i}.cpp",
                suite_name=f"Test{i}"
            )
            for i in range(3)
        ]
        
        # Mock processor
        def mock_processor(task):
            import time
            time.sleep(0.1)  # Simulate some work
            from src.test_generation.models import GenerationResult
            return GenerationResult(
                task=task,
                success=True,
                test_code=f"// Test for {task.function_name}"
            )
        
        results = strategy.execute(tasks, mock_processor)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert strategy.strategy_name == "concurrent_w2"
    
    def test_prompt_generator(self):
        """Test PromptGenerator component"""
        generator = PromptGenerator()
        
        function_info = {
            'name': 'test_function',
            'file': 'test.c',
            'language': 'c',
            'return_type': 'int',
            'parameters': [],
            'body': 'return 42;'
        }
        context = {
            'called_functions': [],
            'macros_used': [],
            'macro_definitions': [],
            'data_structures': []
        }
        
        task = generator.prepare_task(function_info, context)
        
        assert isinstance(task, GenerationTask)
        assert task.function_name == 'test_function'
        assert task.target_filepath == 'test_test.cpp'
    
    def test_core_test_generator(self):
        """Test CoreTestGenerator component"""
        # Create mock LLM client
        mock_client = Mock()
        mock_client.generate_test.return_value = {
            'success': True,
            'test_code': '// Generated test',
            'usage': {'total_tokens': 100},
            'model': 'test-model'
        }
        
        generator = CoreTestGenerator(mock_client)
        
        task = GenerationTask(
            function_info={'name': 'test_function', 'language': 'c'},
            context={},
            target_filepath="test.cpp",
            suite_name="TestSuite"
        )
        
        result = generator.generate_test(task, "Test prompt")
        
        assert result.success is True
        assert result.test_code == '// Generated test'
        assert result.function_name == 'test_function'
    
    def test_test_generation_service_backward_compatibility(self):
        """Test TestGenerationService backward compatibility"""
        # Create mock LLM client
        mock_client = LLMClient.create_mock_client()
        
        service = TestGenerationService(mock_client)
        
        # Test old API
        functions_with_context = [{
            'function': {
                'name': 'test_function',
                'file': 'test.c',
                'language': 'c',
                'return_type': 'int',
                'parameters': [],
                'body': 'return 42;'
            },
            'context': {
                'called_functions': [],
                'macros_used': [],
                'macro_definitions': [],
                'data_structures': []
            }
        }]
        
        project_config = {
            'name': 'test_project',
            'path': './test_project',
            'output_dir': './test_output',
            'llm_provider': 'mock',
            'prompt_only': True
        }
        
        results = service.generate_tests(
            functions_with_context, 
            project_config, 
            max_workers=1
        )
        
        assert len(results) == 1
        assert isinstance(results[0], dict)  # Backward compatible format
        assert 'success' in results[0]
        assert 'function_name' in results[0]


def test_integration_basic_workflow():
    """Test basic integration workflow"""
    # Create mock client
    client = LLMClient.create_mock_client()
    
    # Create service
    service = TestGenerationService(client)
    
    # Create test data
    function_info = {
        'name': 'add_numbers',
        'file': 'math.c',
        'language': 'c',
        'return_type': 'int',
        'parameters': [
            {'name': 'a', 'type': 'int'},
            {'name': 'b', 'type': 'int'}
        ],
        'body': 'return a + b;'
    }
    
    context = {
        'called_functions': [],
        'macros_used': [],
        'macro_definitions': [],
        'data_structures': []
    }
    
    functions_with_context = [{'function': function_info, 'context': context}]
    
    # Create configuration
    config = TestGenerationConfig(
        project_name="test_project",
        output_dir="",  # No output for test
        max_workers=1,
        execution_strategy="sequential",
        save_prompts=False,
        aggregate_tests=False,
        generate_readme=False
    )
    
    # Generate tests
    result = service.generate_tests_new_api(functions_with_context, config)
    
    assert result.total_count == 1
    assert result.successful_count == 1
    assert len(result.results) == 1
    assert result.results[0].success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])