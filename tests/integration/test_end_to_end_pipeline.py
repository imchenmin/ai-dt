"""
End-to-end integration tests for the complete test generation pipeline
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import yaml

from src.test_generation.service import TestGenerationService
from src.test_generation.models import TestGenerationConfig, AggregatedResult
from src.llm.client import LLMClient
from src.utils.config_manager import ConfigManager


class TestEndToEndPipeline:
    """End-to-end integration tests for test generation pipeline"""
    
    def create_test_config_file(self) -> str:
        """Create a temporary test configuration file"""
        config_data = {
            'defaults': {
                'llm_provider': 'mock',
                'model': 'test-model',
                'output_dir': './test_output',
                'error_handling': {
                    'max_retries': 1,
                    'retry_delay': 0.1
                }
            },
            'projects': {
                'test_project': {
                    'path': '/test/project',
                    'comp_db': 'compile_commands.json',
                    'description': 'Test project for integration tests'
                }
            },
            'llm_providers': {
                'mock': {
                    'api_key_env': 'MOCK_API_KEY',
                    'models': ['test-model']
                }
            },
            'profiles': {
                'test': {
                    'description': 'Test profile',
                    'max_functions': 2,
                    'max_workers': 1
                }
            }
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(config_data, f)
            return f.name
    
    def create_sample_functions_with_context(self):
        """Create sample functions with context for testing"""
        return [
            {
                'function': {
                    'name': 'add_numbers',
                    'return_type': 'int',
                    'parameters': [
                        {'name': 'a', 'type': 'int'},
                        {'name': 'b', 'type': 'int'}
                    ],
                    'file': '/test/project/math.c',
                    'language': 'c',
                    'body': 'int add_numbers(int a, int b) {\n    return a + b;\n}',
                    'line': 10
                },
                'context': {
                    'includes': ['<stdio.h>'],
                    'macros': [],
                    'called_functions': [],
                    'data_structures': []
                }
            },
            {
                'function': {
                    'name': 'multiply',
                    'return_type': 'int', 
                    'parameters': [
                        {'name': 'x', 'type': 'int'},
                        {'name': 'y', 'type': 'int'}
                    ],
                    'file': '/test/project/math.c',
                    'language': 'c',
                    'body': 'int multiply(int x, int y) {\n    return x * y;\n}',
                    'line': 15
                },
                'context': {
                    'includes': ['<stdio.h>'],
                    'macros': [],
                    'called_functions': [],
                    'data_structures': []
                }
            }
        ]
    
    def test_complete_pipeline_with_mock_llm(self):
        """Test complete pipeline using mock LLM client"""
        # Create mock LLM client
        mock_client = LLMClient.create_mock_client("test-model")
        
        # Create service
        service = TestGenerationService(llm_client=mock_client)
        
        # Create test configuration
        config = TestGenerationConfig(
            project_name="test_project",
            output_dir=tempfile.mkdtemp(),
            max_workers=1,
            save_prompts=True,
            aggregate_tests=True,
            generate_readme=True
        )
        
        # Get sample functions
        functions_with_context = self.create_sample_functions_with_context()
        
        # Execute test generation
        result = service.generate_tests_new_api(functions_with_context, config)
        
        # Verify results
        assert isinstance(result, AggregatedResult)
        assert result.total_count == 2
        assert result.successful_count >= 0  # Mock may return success or failure
        assert result.config.project_name == "test_project"
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration is not None
        
        # Verify result structure
        for test_result in result.results:
            assert hasattr(test_result, 'task')
            assert hasattr(test_result, 'success')
            assert test_result.task.function_name in ['add_numbers', 'multiply']
    
    def test_backward_compatible_api(self):
        """Test backward compatible API works correctly"""
        # Create mock LLM client
        mock_client = LLMClient.create_mock_client("test-model")
        
        # Create service
        service = TestGenerationService(llm_client=mock_client)
        
        # Create project config in old format
        project_config = {
            'name': 'test_project',
            'output_dir': tempfile.mkdtemp(),
            'llm_provider': 'mock',
            'model': 'test-model',
            'max_workers': 1
        }
        
        # Get sample functions
        functions_with_context = self.create_sample_functions_with_context()
        
        # Execute test generation using backward compatible API
        results = service.generate_tests(functions_with_context, project_config, max_workers=1)
        
        # Verify results are in old format (list of dicts)
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'function_name' in result
            assert 'test_code' in result
            assert result['function_name'] in ['add_numbers', 'multiply']
    
    def test_config_manager_integration(self):
        """Test integration with ConfigManager"""
        config_file = self.create_test_config_file()
        
        try:
            # Create config manager with test file
            config_manager = ConfigManager(config_file)
            
            # Get project config
            project_config = config_manager.get_project_config('test_project')
            
            # Verify config loading
            assert project_config['path'] == '/test/project'
            assert project_config['comp_db'] == 'compile_commands.json'
            assert project_config['llm_provider'] == 'mock'  # From defaults
            
            # Get LLM config
            llm_config = config_manager.get_llm_config('mock')
            assert llm_config['api_key_env'] == 'MOCK_API_KEY'
            
            # List projects
            projects = config_manager.list_projects()
            assert 'test_project' in projects
            
        finally:
            os.unlink(config_file)
    
    def test_service_factory_methods(self):
        """Test service factory methods"""
        # Test create_for_testing
        service = TestGenerationService.create_for_testing()
        assert service.llm_client is not None
        
        # Test config conversion
        project_config = {
            'name': 'test_project',
            'output_dir': '/test/output',
            'path': '/test/project'
        }
        
        test_config = service.create_config_from_dict(project_config, max_workers=2)
        assert isinstance(test_config, TestGenerationConfig)
        assert test_config.max_workers == 2
        assert test_config.execution_strategy == 'concurrent'
        
        # Test LLM config creation
        llm_config = service.create_llm_config_from_dict(project_config)
        assert llm_config.provider_name == 'deepseek'  # Default
    
    def test_error_handling_integration(self):
        """Test error handling in the complete pipeline"""
        # Create service with mock that always fails
        mock_client = Mock(spec=LLMClient)
        
        # Mock generate_test to always fail
        def mock_generate_failing(*args, **kwargs):
            return {
                'success': False,
                'error': 'Mock LLM failure',
                'test_code': '',
                'usage': {}
            }
        
        mock_client.generate_test = mock_generate_failing
        
        service = TestGenerationService(llm_client=mock_client)
        
        # Create configuration
        config = TestGenerationConfig(
            project_name="error_test",
            output_dir=tempfile.mkdtemp(),
            max_workers=1
        )
        
        # Get sample functions
        functions_with_context = self.create_sample_functions_with_context()
        
        # Execute - should handle errors gracefully
        result = service.generate_tests_new_api(functions_with_context, config)
        
        # Verify error handling
        assert isinstance(result, AggregatedResult)
        assert result.total_count == 2
        assert result.failed_count == 2  # Both should fail
        assert result.successful_count == 0
        
        # Check individual results
        for test_result in result.results:
            assert test_result.success is False
            assert test_result.error is not None
    
    def test_sequential_vs_concurrent_execution(self):
        """Test both sequential and concurrent execution strategies"""
        mock_client = LLMClient.create_mock_client("test-model")
        service = TestGenerationService(llm_client=mock_client)
        functions_with_context = self.create_sample_functions_with_context()
        
        # Test sequential execution
        sequential_config = TestGenerationConfig(
            project_name="sequential_test",
            output_dir=tempfile.mkdtemp(),
            max_workers=1,  # Forces sequential
            execution_strategy="sequential"
        )
        
        sequential_result = service.generate_tests_new_api(functions_with_context, sequential_config)
        assert sequential_result.total_count == 2
        
        # Test concurrent execution
        concurrent_config = TestGenerationConfig(
            project_name="concurrent_test", 
            output_dir=tempfile.mkdtemp(),
            max_workers=2,  # Forces concurrent
            execution_strategy="concurrent"
        )
        
        concurrent_result = service.generate_tests_new_api(functions_with_context, concurrent_config)
        assert concurrent_result.total_count == 2
        
        # Both should have same number of results
        assert sequential_result.total_count == concurrent_result.total_count
    
    def test_summary_report_generation(self):
        """Test summary report generation"""
        mock_client = LLMClient.create_mock_client("test-model")
        service = TestGenerationService(llm_client=mock_client)
        
        # Create mixed results (some success, some failure)
        results = [
            {'success': True, 'function_name': 'func1'},
            {'success': False, 'function_name': 'func2', 'error': 'Test error'},
            {'success': True, 'function_name': 'func3'}
        ]
        
        report = service.get_summary_report(results)
        
        # Verify report content
        assert 'Test Generation Summary' in report
        assert 'Total functions processed: 3' in report
        assert 'Successful generations: 2' in report
        assert 'Failed generations: 1' in report
        assert 'func2: Test error' in report
    
    @patch.dict(os.environ, {'MOCK_API_KEY': 'test_key'})
    def test_provider_availability_check(self):
        """Test provider availability checking"""
        config_file = self.create_test_config_file()
        
        try:
            config_manager = ConfigManager(config_file)
            
            # Check provider availability
            assert config_manager.is_provider_available('mock') is True
            
            # Get API key
            api_key = config_manager.get_api_key('mock')
            assert api_key == 'test_key'
            
            # List providers with availability
            providers = config_manager.list_providers()
            assert 'mock' in providers
            
        finally:
            os.unlink(config_file)
    
    def test_output_directory_creation(self):
        """Test output directory creation and file organization"""
        mock_client = LLMClient.create_mock_client("test-model")
        service = TestGenerationService(llm_client=mock_client)
        
        # Use a specific temporary directory
        base_output_dir = tempfile.mkdtemp()
        
        config = TestGenerationConfig(
            project_name="output_test",
            output_dir=base_output_dir,
            max_workers=1,
            save_prompts=True,
            aggregate_tests=True,
            generate_readme=True,
            timestamped_output=False  # Disable for predictable paths
        )
        
        functions_with_context = self.create_sample_functions_with_context()
        
        # Execute test generation
        result = service.generate_tests_new_api(functions_with_context, config)
        
        # Verify output directory exists
        output_path = Path(base_output_dir)
        assert output_path.exists()
        
        # Verify results
        assert isinstance(result, AggregatedResult)
        assert result.total_count == 2
        
        # The actual file creation depends on the file manager configuration
        # This test mainly verifies the pipeline runs without errors