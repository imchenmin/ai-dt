"""
Tests for test_generation.models module
"""

import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.test_generation.models import (
    GenerationTask,
    GenerationResult,
    TestGenerationConfig,
    AggregatedResult
)


class TestGenerationTask:
    """Test cases for GenerationTask dataclass"""
    
    def test_creation_with_required_fields(self):
        """Test creating GenerationTask with required fields"""
        function_info = {
            'name': 'test_function',
            'return_type': 'int',
            'parameters': [],
            'file': '/path/to/source.c',
            'language': 'c'
        }
        context = {'macros': [], 'includes': []}
        
        task = GenerationTask(
            function_info=function_info,
            context=context,
            target_filepath='test_source.cpp',
            suite_name='SourceTest'
        )
        
        assert task.function_info == function_info
        assert task.context == context
        assert task.target_filepath == 'test_source.cpp'
        assert task.suite_name == 'SourceTest'
        assert task.existing_fixture_code is None
    
    def test_creation_with_all_fields(self):
        """Test creating GenerationTask with all fields"""
        task = GenerationTask(
            function_info={'name': 'func', 'language': 'cpp'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test',
            existing_fixture_code='class TestFixture {};'
        )
        
        assert task.existing_fixture_code == 'class TestFixture {};'
    
    def test_function_name_property(self):
        """Test function_name property"""
        task = GenerationTask(
            function_info={'name': 'my_function'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        assert task.function_name == 'my_function'
    
    def test_function_name_property_missing(self):
        """Test function_name property when name is missing"""
        task = GenerationTask(
            function_info={},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        assert task.function_name == 'unknown'
    
    def test_language_property(self):
        """Test language property"""
        task = GenerationTask(
            function_info={'language': 'cpp'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        assert task.language == 'cpp'
    
    def test_language_property_default(self):
        """Test language property with default value"""
        task = GenerationTask(
            function_info={},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        assert task.language == 'c'


class TestGenerationResult:
    """Test cases for GenerationResult dataclass"""
    
    def test_creation_success_case(self):
        """Test creating successful GenerationResult"""
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(
            task=task,
            success=True,
            test_code='TEST(Test, test_func) { ASSERT_TRUE(true); }',
            prompt='Generate test for test_func',
            usage={'prompt_tokens': 100, 'completion_tokens': 50},
            model='gpt-3.5-turbo'
        )
        
        assert result.task == task
        assert result.success is True
        assert 'TEST(Test, test_func)' in result.test_code
        assert result.prompt == 'Generate test for test_func'
        assert result.error is None
        assert result.usage['prompt_tokens'] == 100
        assert result.model == 'gpt-3.5-turbo'
    
    def test_creation_failure_case(self):
        """Test creating failed GenerationResult"""
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(
            task=task,
            success=False,
            error='API rate limit exceeded'
        )
        
        assert result.success is False
        assert result.error == 'API rate limit exceeded'
        assert result.test_code == ''
        assert result.usage is None
    
    def test_function_name_property(self):
        """Test function_name property delegates to task"""
        task = GenerationTask(
            function_info={'name': 'my_function'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(task=task, success=True)
        assert result.function_name == 'my_function'
    
    def test_to_dict_success(self):
        """Test to_dict method for successful result"""
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(
            task=task,
            success=True,
            test_code='test code',
            prompt='test prompt',
            usage={'tokens': 100},
            model='test-model',
            prompt_length=11,
            test_length=9,
            output_path='/output/test.cpp',
            file_info={'test_file': '/path/test.cpp'}
        )
        
        result_dict = result.to_dict()
        
        expected = {
            'success': True,
            'test_code': 'test code',
            'function_name': 'test_func',
            'prompt': 'test prompt',
            'error': None,
            'usage': {'tokens': 100},
            'model': 'test-model',
            'prompt_length': 11,
            'test_length': 9,
            'output_path': '/output/test.cpp',
            'file_info': {'test_file': '/path/test.cpp'}
        }
        
        assert result_dict == expected
    
    def test_to_dict_failure(self):
        """Test to_dict method for failed result"""
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        result = GenerationResult(
            task=task,
            success=False,
            error='Generation failed'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is False
        assert result_dict['error'] == 'Generation failed'
        assert result_dict['function_name'] == 'test_func'
        assert result_dict['test_code'] == ''
        assert result_dict['usage'] == {}


class TestTestGenerationConfig:
    """Test cases for TestGenerationConfig dataclass"""
    
    def test_creation_with_required_fields(self):
        """Test creating config with required fields"""
        config = TestGenerationConfig(
            project_name='test_project',
            output_dir='/output'
        )
        
        assert config.project_name == 'test_project'
        assert config.output_dir == '/output'
        assert config.unit_test_directory_path is None
        assert config.max_workers == 3
        assert config.save_prompts is True
        assert config.aggregate_tests is True
        assert config.generate_readme is True
        assert config.execution_strategy == 'concurrent'
        assert config.delay_between_requests == 1.0
        assert config.timestamped_output is True
        assert config.separate_debug_files is True
    
    def test_creation_with_all_fields(self):
        """Test creating config with all fields customized"""
        config = TestGenerationConfig(
            project_name='custom_project',
            output_dir='/custom/output',
            unit_test_directory_path='/tests',
            max_workers=5,
            save_prompts=False,
            aggregate_tests=False,
            generate_readme=False,
            execution_strategy='sequential',
            delay_between_requests=2.0,
            timestamped_output=False,
            separate_debug_files=False
        )
        
        assert config.project_name == 'custom_project'
        assert config.output_dir == '/custom/output'
        assert config.unit_test_directory_path == '/tests'
        assert config.max_workers == 5
        assert config.save_prompts is False
        assert config.aggregate_tests is False
        assert config.generate_readme is False
        assert config.execution_strategy == 'sequential'
        assert config.delay_between_requests == 2.0
        assert config.timestamped_output is False
        assert config.separate_debug_files is False


class TestAggregatedResult:
    """Test cases for AggregatedResult dataclass"""
    
    def create_sample_results(self) -> list:
        """Helper to create sample results"""
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
        
        result1 = GenerationResult(task=task1, success=True)
        result2 = GenerationResult(task=task2, success=False, error='Failed')
        
        return [result1, result2]
    
    def test_creation(self):
        """Test creating AggregatedResult"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        results = self.create_sample_results()
        
        aggregated = AggregatedResult(
            config=config,
            results=results
        )
        
        assert aggregated.config == config
        assert aggregated.results == results
        assert aggregated.generation_info == {}
        assert aggregated.start_time is None
        assert aggregated.end_time is None
    
    def test_successful_count(self):
        """Test successful_count property"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        results = self.create_sample_results()
        
        aggregated = AggregatedResult(
            config=config,
            results=results
        )
        
        assert aggregated.successful_count == 1
    
    def test_failed_count(self):
        """Test failed_count property"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        results = self.create_sample_results()
        
        aggregated = AggregatedResult(
            config=config,
            results=results
        )
        
        assert aggregated.failed_count == 1
    
    def test_total_count(self):
        """Test total_count property"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        results = self.create_sample_results()
        
        aggregated = AggregatedResult(
            config=config,
            results=results
        )
        
        assert aggregated.total_count == 2
    
    def test_success_rate(self):
        """Test success_rate property"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        results = self.create_sample_results()
        
        aggregated = AggregatedResult(
            config=config,
            results=results
        )
        
        assert aggregated.success_rate == 0.5
    
    def test_success_rate_empty(self):
        """Test success_rate property with empty results"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        
        aggregated = AggregatedResult(
            config=config,
            results=[]
        )
        
        assert aggregated.success_rate == 0.0
    
    def test_duration_with_times(self):
        """Test duration property with start and end times"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 0, 30)  # 30 seconds later
        
        aggregated = AggregatedResult(
            config=config,
            results=[],
            start_time=start_time,
            end_time=end_time
        )
        
        assert aggregated.duration == 30.0
    
    def test_duration_without_times(self):
        """Test duration property without times"""
        config = TestGenerationConfig(
            project_name='test',
            output_dir='/output'
        )
        
        aggregated = AggregatedResult(
            config=config,
            results=[]
        )
        
        assert aggregated.duration is None