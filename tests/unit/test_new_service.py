"""
Tests for test_generation.service module (new API)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from src.test_generation.service import TestGenerationService
from src.test_generation.models import (
    GenerationTask,
    GenerationResult,
    TestGenerationConfig,
    AggregatedResult
)
from src.test_generation.orchestrator import TestGenerationOrchestrator
from src.llm.client import LLMClient
from src.llm.models import LLMConfig


class TestNewTestGenerationService:
    """Test cases for new TestGenerationService API"""
    
    def create_sample_functions_with_context(self):
        """Helper to create sample functions with context"""
        return [
            {
                'function': {
                    'name': 'test_func1',
                    'return_type': 'int',
                    'parameters': [],
                    'file': '/project/src/utils.c',
                    'language': 'c'
                },
                'context': {'includes': [], 'macros': []}
            },
            {
                'function': {
                    'name': 'test_func2',
                    'return_type': 'void',
                    'parameters': [{'name': 'param1', 'type': 'int'}],
                    'file': '/project/src/math.c',
                    'language': 'c'
                },
                'context': {'includes': ['<math.h>'], 'macros': []}
            }
        ]
    
    def create_sample_project_config(self):
        """Helper to create sample project config"""
        return {
            'name': 'test_project',
            'output_dir': '/output',
            'llm_provider': 'deepseek',
            'model': 'deepseek-coder',
            'max_workers': 2,
            'error_handling': {
                'max_retries': 3,
                'retry_delay': 1.0
            }
        }
    
    def test_init_without_llm_client(self):
        """Test service initialization without LLM client"""
        service = TestGenerationService()
        
        assert service.llm_client is None
        assert service.orchestrator is None
    
    def test_init_with_llm_client(self):
        """Test service initialization with LLM client"""
        mock_client = Mock(spec=LLMClient)
        service = TestGenerationService(llm_client=mock_client)
        
        assert service.llm_client == mock_client
        assert service.orchestrator is None
    
    @patch('src.test_generation.service.TestGenerationOrchestrator')
    @patch('src.test_generation.service.ExecutionStrategyFactory')
    def test_generate_tests_backward_compatible(self, mock_strategy_factory, mock_orchestrator_class):
        """Test backward compatible generate_tests method"""
        # Setup mocks
        mock_client = Mock(spec=LLMClient)
        mock_orchestrator = Mock(spec=TestGenerationOrchestrator)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_strategy = Mock()
        mock_strategy_factory.create_strategy.return_value = mock_strategy
        
        # Create sample results
        sample_tasks = [
            GenerationTask(
                function_info={'name': 'test_func'},
                context={},
                target_filepath='test.cpp',
                suite_name='Test'
            )
        ]
        sample_results = [
            GenerationResult(task=sample_tasks[0], success=True, test_code='TEST code')
        ]
        
        aggregated = AggregatedResult(
            config=TestGenerationConfig(project_name='test', output_dir='/output'),
            results=sample_results
        )
        mock_orchestrator.generate_tests.return_value = aggregated
        
        service = TestGenerationService(llm_client=mock_client)
        
        functions_with_context = self.create_sample_functions_with_context()
        project_config = self.create_sample_project_config()
        
        results = service.generate_tests(functions_with_context, project_config, max_workers=3)
        
        # Verify orchestrator was created and called
        mock_orchestrator_class.assert_called_once()
        mock_orchestrator.generate_tests.assert_called_once()
        
        # Verify results are converted to backward compatible format
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert results[0]['success'] is True
        assert results[0]['test_code'] == 'TEST code'
        assert results[0]['function_name'] == 'test_func'
    
    @patch('src.test_generation.service.TestGenerationOrchestrator')
    def test_generate_tests_new_api(self, mock_orchestrator_class):
        """Test new API generate_tests_new_api method"""
        mock_client = Mock(spec=LLMClient)
        mock_orchestrator = Mock(spec=TestGenerationOrchestrator)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        config = TestGenerationConfig(
            project_name='test_project',
            output_dir='/output',
            max_workers=2
        )
        
        llm_config = LLMConfig(
            provider_name='deepseek',
            api_key='test_key',
            model='deepseek-coder'
        )
        
        aggregated = AggregatedResult(config=config, results=[])
        mock_orchestrator.generate_tests.return_value = aggregated
        
        service = TestGenerationService(llm_client=mock_client)
        
        functions_with_context = self.create_sample_functions_with_context()
        
        result = service.generate_tests_new_api(functions_with_context, config, llm_config)
        
        assert isinstance(result, AggregatedResult)
        mock_orchestrator.generate_tests.assert_called_once_with(functions_with_context, config)
    
    def test_generate_tests_new_api_no_llm_config(self):
        """Test new API without LLM config raises error"""
        service = TestGenerationService()
        
        functions_with_context = self.create_sample_functions_with_context()
        config = TestGenerationConfig(project_name='test', output_dir='/output')
        
        with pytest.raises(ValueError, match="Either llm_client or llm_config must be provided"):
            service.generate_tests_new_api(functions_with_context, config)
    
    def test_create_config_from_dict(self):
        """Test creating TestGenerationConfig from dictionary"""
        service = TestGenerationService()
        
        project_config = self.create_sample_project_config()
        
        config = service.create_config_from_dict(project_config, max_workers=5)
        
        assert isinstance(config, TestGenerationConfig)
        assert config.project_name == 'test_project'
        assert 'test_project_' in config.output_dir  # Should have timestamp
        assert config.max_workers == 5
        assert config.execution_strategy == 'concurrent'
    
    def test_create_llm_config_from_dict(self):
        """Test creating LLMConfig from dictionary"""
        service = TestGenerationService()
        
        project_config = self.create_sample_project_config()
        
        with patch('src.test_generation.service.ConfigLoader.get_api_key', return_value='test_key'):
            llm_config = service.create_llm_config_from_dict(project_config)
        
        assert isinstance(llm_config, LLMConfig)
        assert llm_config.provider_name == 'deepseek'
        assert llm_config.model == 'deepseek-coder'
        assert llm_config.api_key == 'test_key'
        assert llm_config.max_retries == 3
        assert llm_config.retry_delay == 1.0
    
    @patch('src.test_generation.service.ConfigLoader.get_api_key')
    def test_create_llm_client_with_api_key(self, mock_get_api_key):
        """Test LLM client creation with API key"""
        mock_get_api_key.return_value = 'test_api_key'
        
        service = TestGenerationService()
        project_config = self.create_sample_project_config()
        
        with patch('src.test_generation.service.LLMClient.create_from_config') as mock_create:
            mock_client = Mock(spec=LLMClient)
            mock_create.return_value = mock_client
            
            client = service._create_llm_client(project_config)
            
            assert client == mock_client
            mock_create.assert_called_once()
    
    @patch('src.test_generation.service.ConfigLoader.get_api_key')
    @patch('src.test_generation.service.ConfigLoader.get_llm_config')
    def test_create_llm_client_no_api_key(self, mock_get_llm_config, mock_get_api_key):
        """Test LLM client creation without API key falls back to mock"""
        mock_get_api_key.return_value = None
        mock_get_llm_config.return_value = {'api_key_env': 'DEEPSEEK_API_KEY'}
        
        service = TestGenerationService()
        project_config = self.create_sample_project_config()
        
        with patch('src.test_generation.service.LLMClient.create_mock_client') as mock_create_mock:
            mock_client = Mock(spec=LLMClient)
            mock_create_mock.return_value = mock_client
            
            client = service._create_llm_client(project_config)
            
            assert client == mock_client
            mock_create_mock.assert_called_once_with('deepseek-coder')
    
    def test_create_llm_client_prompt_only_mode(self):
        """Test LLM client creation in prompt-only mode"""
        service = TestGenerationService()
        project_config = self.create_sample_project_config()
        project_config['prompt_only'] = True
        
        with patch('src.test_generation.service.LLMClient.create_mock_client') as mock_create_mock:
            mock_client = Mock(spec=LLMClient)
            mock_create_mock.return_value = mock_client
            
            client = service._create_llm_client(project_config)
            
            assert client == mock_client
            mock_create_mock.assert_called_once_with('deepseek-coder')
    
    def test_create_llm_config_model_defaults(self):
        """Test LLM config creation with model defaults"""
        service = TestGenerationService()
        
        # Test OpenAI provider with default model switch
        openai_config = {
            'llm_provider': 'openai',
            'model': 'deepseek-coder',  # Should switch to gpt-3.5-turbo
            'error_handling': {'max_retries': 2, 'retry_delay': 0.5}
        }
        
        with patch('src.test_generation.service.ConfigLoader.get_api_key', return_value='test_key'):
            llm_config = service._create_llm_config(openai_config)
        
        assert llm_config.model == 'gpt-3.5-turbo'
        assert llm_config.provider_name == 'openai'
        
        # Test Dify provider with default model switch
        dify_config = {
            'llm_provider': 'dify',
            'model': 'deepseek-coder',  # Should switch to dify_model
            'error_handling': {}
        }
        
        with patch('src.test_generation.service.ConfigLoader.get_api_key', return_value='test_key'):
            llm_config = service._create_llm_config(dify_config)
        
        assert llm_config.model == 'dify_model'
        assert llm_config.provider_name == 'dify'
    
    def test_get_summary_report(self):
        """Test summary report generation"""
        service = TestGenerationService()
        
        results = [
            {'success': True, 'function_name': 'func1'},
            {'success': False, 'function_name': 'func2', 'error': 'Generation failed'},
            {'success': True, 'function_name': 'func3'}
        ]
        
        report = service.get_summary_report(results)
        
        assert 'Test Generation Summary' in report
        assert 'Total functions processed: 3' in report
        assert 'Successful generations: 2' in report
        assert 'Failed generations: 1' in report
        assert 'func2: Generation failed' in report
    
    def test_set_llm_client(self):
        """Test setting LLM client"""
        service = TestGenerationService()
        mock_client = Mock(spec=LLMClient)
        
        service.set_llm_client(mock_client)
        
        assert service.llm_client == mock_client
    
    def test_set_llm_client_with_orchestrator(self):
        """Test setting LLM client when orchestrator exists"""
        service = TestGenerationService()
        mock_client = Mock(spec=LLMClient)
        mock_orchestrator = Mock(spec=TestGenerationOrchestrator)
        service.orchestrator = mock_orchestrator
        
        service.set_llm_client(mock_client)
        
        assert service.llm_client == mock_client
        mock_orchestrator.set_llm_client.assert_called_once_with(mock_client)
    
    def test_create_for_testing(self):
        """Test factory method for testing"""
        service = TestGenerationService.create_for_testing()
        
        assert isinstance(service, TestGenerationService)
        assert service.llm_client is not None
    
    def test_create_for_testing_with_custom_client(self):
        """Test factory method for testing with custom client"""
        mock_client = Mock(spec=LLMClient)
        
        service = TestGenerationService.create_for_testing(mock_client)
        
        assert service.llm_client == mock_client
    
    def test_convert_project_config_timestamped(self):
        """Test project config conversion with timestamping"""
        service = TestGenerationService()
        
        project_config = {
            'name': 'test_project',
            'output_dir': './output',
            'path': '/project/path'
        }
        
        config = service._convert_project_config(project_config, max_workers=3)
        
        assert config.project_name == 'path'  # Path('/project/path').name == 'path'
        # Just check that timestamp was added (any timestamp is fine)
        assert 'path_' in config.output_dir
        assert config.max_workers == 3
        assert config.execution_strategy == 'concurrent'
    
    def test_convert_project_config_ready_output_dir(self):
        """Test project config conversion with ready output directory"""
        service = TestGenerationService()
        
        project_config = {
            'name': 'test_project',
            'output_dir': '/ready/output',
            'output_dir_ready': True
        }
        
        config = service._convert_project_config(project_config, max_workers=1)
        
        assert config.output_dir == '/ready/output'
        assert config.execution_strategy == 'sequential'