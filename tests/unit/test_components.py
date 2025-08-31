"""
Tests for test_generation.components module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from src.test_generation.components import (
    PromptGenerator,
    CoreTestGenerator,
    TestFileManager,
    TestResultAggregator,
    ComponentFactory
)
from src.test_generation.models import (
    GenerationTask,
    GenerationResult,
    TestGenerationConfig,
    AggregatedResult
)
from src.llm.client import LLMClient


class TestPromptGenerator:
    """Test cases for PromptGenerator component"""
    
    def test_init_with_defaults(self):
        """Test PromptGenerator initialization with default dependencies"""
        generator = PromptGenerator()
        
        assert generator.context_compressor is not None
        assert generator.fixture_finder is not None
    
    def test_init_with_custom_dependencies(self):
        """Test PromptGenerator initialization with custom dependencies"""
        mock_compressor = Mock()
        mock_finder = Mock()
        
        generator = PromptGenerator(
            context_compressor=mock_compressor,
            fixture_finder=mock_finder
        )
        
        assert generator.context_compressor == mock_compressor
        assert generator.fixture_finder == mock_finder
    
    @patch('src.test_generation.components.PromptTemplates')
    def test_generate_prompt(self, mock_templates):
        """Test prompt generation"""
        mock_templates.generate_test_prompt.return_value = "Generated prompt"
        
        generator = PromptGenerator()
        generator.context_compressor = Mock()
        generator.context_compressor.compress_function_context.return_value = "compressed_context"
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={'includes': [], 'macros': []},
            target_filepath='test.cpp',
            suite_name='Test',
            existing_fixture_code='fixture code'
        )
        
        result = generator.generate_prompt(task)
        
        assert result == "Generated prompt"
        generator.context_compressor.compress_function_context.assert_called_once()
        mock_templates.generate_test_prompt.assert_called_once_with(
            "compressed_context",
            existing_fixture_code='fixture code',
            suite_name='Test'
        )
    
    def test_prepare_task(self):
        """Test task preparation"""
        generator = PromptGenerator()
        generator.fixture_finder = Mock()
        generator.fixture_finder.find_fixture_definition.return_value = "fixture code"
        
        function_info = {
            'name': 'test_function',
            'file': '/project/src/math_utils.c'
        }
        context = {'includes': [], 'macros': []}
        
        task = generator.prepare_task(
            function_info,
            context,
            unit_test_directory_path='/project/tests'
        )
        
        assert task.function_info == function_info
        assert task.context == context
        assert task.target_filepath == 'test_math_utils.cpp'
        assert task.suite_name == 'math_utilsTest'
        assert task.existing_fixture_code == 'fixture code'
        
        generator.fixture_finder.find_fixture_definition.assert_called_once_with(
            'math_utilsTest', '/project/tests'
        )
    
    def test_prepare_task_no_fixture_directory(self):
        """Test task preparation without fixture directory"""
        generator = PromptGenerator()
        
        function_info = {
            'name': 'test_function',
            'file': '/project/src/utils.c'
        }
        context = {}
        
        task = generator.prepare_task(function_info, context)
        
        assert task.existing_fixture_code is None
        assert task.target_filepath == 'test_utils.cpp'
        assert task.suite_name == 'utilsTest'


class TestCoreTestGenerator:
    """Test cases for CoreTestGenerator component"""
    
    def test_init(self):
        """Test CoreTestGenerator initialization"""
        mock_client = Mock(spec=LLMClient)
        generator = CoreTestGenerator(mock_client)
        
        assert generator.llm_client == mock_client
    
    def test_generate_test_success(self):
        """Test successful test generation"""
        mock_client = Mock(spec=LLMClient)
        mock_client.generate_test.return_value = {
            'success': True,
            'test_code': 'TEST(Test, test_func) { ASSERT_TRUE(true); }',
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50},
            'model': 'gpt-3.5-turbo'
        }
        
        generator = CoreTestGenerator(mock_client)
        
        task = GenerationTask(
            function_info={'name': 'test_func', 'language': 'c'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = generator.generate_test(task, "test prompt")
        
        assert result.success is True
        assert 'TEST(Test, test_func)' in result.test_code
        assert result.prompt == "test prompt"
        assert result.usage == {'prompt_tokens': 100, 'completion_tokens': 50}
        assert result.model == 'gpt-3.5-turbo'
        
        mock_client.generate_test.assert_called_once_with(
            prompt="test prompt",
            max_tokens=2500,
            temperature=0.3,
            language='c'
        )
    
    def test_generate_test_failure(self):
        """Test failed test generation"""
        mock_client = Mock(spec=LLMClient)
        mock_client.generate_test.return_value = {
            'success': False,
            'error': 'API rate limit exceeded',
            'test_code': '',
            'usage': {}
        }
        
        generator = CoreTestGenerator(mock_client)
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = generator.generate_test(task, "test prompt")
        
        assert result.success is False
        assert result.error == 'API rate limit exceeded'
        assert result.test_code == ''
    
    def test_generate_test_exception(self):
        """Test test generation with exception"""
        mock_client = Mock(spec=LLMClient)
        mock_client.generate_test.side_effect = Exception("Network error")
        
        generator = CoreTestGenerator(mock_client)
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = generator.generate_test(task, "test prompt")
        
        assert result.success is False
        assert "Network error" in result.error
        assert result.prompt == "test prompt"


class TestTestFileManager:
    """Test cases for TestFileManager component"""
    
    def test_init_with_defaults(self):
        """Test TestFileManager initialization with defaults"""
        manager = TestFileManager()
        
        assert manager.file_organizer is None
        assert manager.aggregator is not None
    
    def test_init_with_custom_dependencies(self):
        """Test TestFileManager initialization with custom dependencies"""
        mock_organizer = Mock()
        mock_aggregator = Mock()
        
        manager = TestFileManager(
            file_organizer=mock_organizer,
            aggregator=mock_aggregator
        )
        
        assert manager.file_organizer == mock_organizer
        assert manager.aggregator == mock_aggregator
    
    def test_save_prompt_success(self):
        """Test successful prompt saving"""
        mock_organizer = Mock()
        mock_organizer.save_prompt_only.return_value = '/path/to/prompt.txt'
        
        manager = TestFileManager(file_organizer=mock_organizer)
        
        result = manager.save_prompt('test_func', 'test prompt')
        
        assert result == '/path/to/prompt.txt'
        mock_organizer.save_prompt_only.assert_called_once_with('test_func', 'test prompt')
    
    def test_save_prompt_no_organizer(self):
        """Test prompt saving without file organizer"""
        manager = TestFileManager()
        
        with pytest.raises(ValueError, match="File organizer not configured"):
            manager.save_prompt('test_func', 'test prompt')
    
    def test_save_result_success(self):
        """Test successful result saving"""
        mock_organizer = Mock()
        mock_aggregator = Mock()
        
        manager = TestFileManager(
            file_organizer=mock_organizer,
            aggregator=mock_aggregator
        )
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(
            task=task,
            success=True,
            test_code='TEST(Test, test_func) {}',
            prompt='test prompt'
        )
        
        mock_organizer.organize_test_output.return_value = {'test_file': '/path/test.cpp'}
        
        saved_result = manager.save_result(result)
        
        assert saved_result.output_path == 'test.cpp'
        assert saved_result.file_info == {'test_file': '/path/test.cpp'}
        
        mock_aggregator.aggregate.assert_called_once_with('test.cpp', 'TEST(Test, test_func) {}')
        mock_organizer.organize_test_output.assert_called_once()
    
    def test_save_result_failure(self):
        """Test saving failed result"""
        mock_organizer = Mock()
        
        manager = TestFileManager(file_organizer=mock_organizer)
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(
            task=task,
            success=False,
            error='Generation failed',
            prompt='test prompt'
        )
        
        mock_organizer.organize_test_output.return_value = {'error_file': '/path/error.txt'}
        
        saved_result = manager.save_result(result)
        
        assert saved_result.file_info == {'error_file': '/path/error.txt'}
        
        # Should save prompt and error for debugging
        mock_organizer.organize_test_output.assert_called_once_with(
            test_code="",
            function_name='test_func',
            prompt='test prompt',
            raw_response='Generation failed: Generation failed'
        )
    
    def test_save_result_no_organizer(self):
        """Test saving result without file organizer"""
        manager = TestFileManager()
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(task=task, success=True)
        
        # Should return result unchanged
        saved_result = manager.save_result(result)
        assert saved_result == result


class TestTestResultAggregator:
    """Test cases for TestResultAggregator component"""
    
    def test_init(self):
        """Test TestResultAggregator initialization"""
        aggregator = TestResultAggregator()
        assert aggregator is not None
    
    def test_aggregate_results(self):
        """Test result aggregation"""
        aggregator = TestResultAggregator()
        
        config = TestGenerationConfig(
            project_name='test_project',
            output_dir='/output'
        )
        
        task1 = GenerationTask(
            function_info={'name': 'func1'},
            context={},
            target_filepath='test1.cpp',
            suite_name='Test1'
        )
        
        task2 = GenerationTask(
            function_info={'name': 'func2'},
            context={},
            target_filepath='test2.cpp',
            suite_name='Test2'
        )
        
        results = [
            GenerationResult(task=task1, success=True),
            GenerationResult(task=task2, success=False, error='Failed')
        ]
        
        aggregated = aggregator.aggregate_results(results, config)
        
        assert isinstance(aggregated, AggregatedResult)
        assert aggregated.config == config
        assert aggregated.results == results
        assert aggregated.successful_count == 1
        assert aggregated.failed_count == 1
        assert aggregated.total_count == 2
        assert 'timestamp' in aggregated.generation_info
        assert aggregated.generation_info['project_name'] == 'test_project'
        assert aggregated.generation_info['total_functions'] == 2
        assert aggregated.generation_info['successful'] == 1
        assert aggregated.generation_info['failed'] == 1
    
    def test_generate_summary_report(self):
        """Test summary report generation"""
        aggregator = TestResultAggregator()
        
        config = TestGenerationConfig(
            project_name='test_project',
            output_dir='/output'
        )
        
        task1 = GenerationTask(
            function_info={'name': 'func1'},
            context={},
            target_filepath='test1.cpp',
            suite_name='Test1'
        )
        
        task2 = GenerationTask(
            function_info={'name': 'func2'},
            context={},
            target_filepath='test2.cpp',
            suite_name='Test2'
        )
        
        results = [
            GenerationResult(task=task1, success=True),
            GenerationResult(task=task2, success=False, error='Generation failed')
        ]
        
        aggregated = AggregatedResult(config=config, results=results)
        
        report = aggregator.generate_summary_report(aggregated)
        
        assert 'Test Generation Summary' in report
        assert 'Project: test_project' in report
        assert 'Total functions processed: 2' in report
        assert 'Successful generations: 1' in report
        assert 'Failed generations: 1' in report
        assert 'Success rate: 50.0%' in report
        assert 'Failed functions:' in report
        assert 'func2: Generation failed' in report


class TestComponentFactory:
    """Test cases for ComponentFactory"""
    
    def test_create_prompt_generator(self):
        """Test prompt generator creation"""
        generator = ComponentFactory.create_prompt_generator()
        
        assert isinstance(generator, PromptGenerator)
        assert generator.context_compressor is not None
        assert generator.fixture_finder is not None
    
    def test_create_prompt_generator_with_dependencies(self):
        """Test prompt generator creation with custom dependencies"""
        mock_compressor = Mock()
        mock_finder = Mock()
        
        generator = ComponentFactory.create_prompt_generator(
            context_compressor=mock_compressor,
            fixture_finder=mock_finder
        )
        
        assert generator.context_compressor == mock_compressor
        assert generator.fixture_finder == mock_finder
    
    def test_create_test_generator(self):
        """Test test generator creation"""
        mock_client = Mock(spec=LLMClient)
        
        generator = ComponentFactory.create_test_generator(mock_client)
        
        assert isinstance(generator, CoreTestGenerator)
        assert generator.llm_client == mock_client
    
    def test_create_file_manager(self):
        """Test file manager creation"""
        manager = ComponentFactory.create_file_manager('/output')
        
        assert isinstance(manager, TestFileManager)
        assert manager.file_organizer is not None
        assert manager.aggregator is not None
    
    def test_create_file_manager_no_output_dir(self):
        """Test file manager creation without output directory"""
        manager = ComponentFactory.create_file_manager('')
        
        assert manager.file_organizer is None
        assert manager.aggregator is not None
    
    def test_create_result_aggregator(self):
        """Test result aggregator creation"""
        aggregator = ComponentFactory.create_result_aggregator()
        
        assert isinstance(aggregator, TestResultAggregator)