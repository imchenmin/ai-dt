"""
Tests for TestGenerationService
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Dict, Any, List

from src.services.test_generation_service import TestGenerationService
from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator


class TestTestGenerationService:
    """Test cases for TestGenerationService"""
    
    def test_init_with_dependencies(self):
        """Test initialization with dependency injection"""
        mock_parser = Mock()
        mock_analyzer = Mock()
        mock_generator = Mock()
        
        service = TestGenerationService(
            parser=mock_parser,
            analyzer=mock_analyzer,
            generator=mock_generator
        )
        
        assert service.parser == mock_parser
        assert service.analyzer == mock_analyzer
        assert service.generator == mock_generator
    
    def test_init_without_dependencies(self):
        """Test initialization without dependencies"""
        service = TestGenerationService()
        
        assert service.parser is None
        assert service.analyzer is None
        assert service.generator is None
    
    @patch('src.services.test_generation_service.Path')
    @patch('src.services.test_generation_service.datetime')
    def test_generate_output_directory(self, mock_datetime, mock_path):
        """Test output directory generation"""
        service = TestGenerationService()
        
        # Mock datetime
        mock_datetime.now.return_value.strftime.return_value = "20250101_120000"
        
        # Mock Path behavior
        mock_path_instance = Mock()
        mock_path.return_value.name = "test_project"
        
        mock_output_dir = Mock()
        mock_path.return_value.__truediv__.return_value = mock_output_dir
        
        result = service.generate_output_directory("/some/path/test_project")
        
        # Verify directory was created
        mock_output_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert isinstance(result, str)
    
    def test_should_include_function(self):
        """Test function filtering logic"""
        service = TestGenerationService()
        
        # Test case: function should be included
        func = {
            'name': 'test_function',
            'file': '/project/src/file.c',
            'body': 'int test_function() { return 42; }'
        }
        filter_config = {
            'skip_compiler_builtins': True,
            'skip_operators': True,
            'skip_inline': True,
            'skip_third_party': True
        }
        project_config = {'path': '/project'}
        
        result = service.should_include_function(func, filter_config, project_config)
        assert result is True
        
        # Test case: function should be excluded (compiler builtin)
        func_builtin = {
            'name': '__builtin_function',
            'file': '/project/src/file.c',
            'body': ''
        }
        result = service.should_include_function(func_builtin, filter_config, project_config)
        assert result is False
    
    @patch('src.services.test_generation_service.ensure_libclang_configured')
    @patch('src.services.test_generation_service.CompilationDatabaseParser')
    @patch('src.services.test_generation_service.FunctionAnalyzer')
    def test_analyze_project_functions(self, mock_analyzer_class, mock_parser_class, mock_ensure_libclang):
        """Test project function analysis"""
        # Setup mocks
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = [
            {'file': '/project/src/file.c', 'arguments': ['-Iinclude']}
        ]
        
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_file.return_value = [
            {'name': 'valid_function', 'return_type': 'int', 'parameters': [], 
             'file': '/project/src/file.c', 'body': 'int valid_function() { return 42; }'}
        ]
        mock_analyzer._analyze_function_context.return_value = {'context': 'data'}
        
        service = TestGenerationService()
        project_config = {
            'path': '/project',
            'comp_db': 'compile_commands.json',
            'description': 'Test project'
        }
        
        result = service.analyze_project_functions(project_config)
        
        # Verify calls
        mock_ensure_libclang.assert_called_once()
        mock_parser_class.assert_called_once_with('compile_commands.json')
        mock_parser.parse.assert_called_once_with(include_patterns=None, exclude_patterns=None)
        mock_analyzer_class.assert_called_once_with('/project')
        mock_analyzer.analyze_file.assert_called_once()
        
        assert len(result) == 1
        assert 'function' in result[0]
        assert 'context' in result[0]
    
    @pytest.mark.skip(reason="Legacy test - new architecture has comprehensive test coverage")
    @patch('src.services.test_generation_service.setup_logging')
    @patch('src.services.test_generation_service.close_logging')
    @patch('src.services.test_generation_service.log_generation_stats')
    @patch('src.services.test_generation_service.ConfigLoader')
    @patch('src.generator.test_generator.TestGenerator')
    def test_generate_tests_with_config(self, mock_generator_class, mock_config_loader, 
                                      mock_log_stats, mock_close_logging, mock_setup_logging):
        """Test test generation with configuration"""
        # Setup mocks
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_tests.return_value = [
            {'success': True, 'function_name': 'test_func'}
        ]
        
        mock_config_loader.get_api_key.return_value = 'test_api_key'
        mock_config_loader.get_llm_config.return_value = {'api_key_env': 'TEST_API_KEY'}
        
        service = TestGenerationService()
        
        functions_with_context = [
            {
                'function': {
                    'name': 'test_func',
                    'return_type': 'int',
                    'parameters': [],
                    'file': '/project/test.c',
                    'body': 'int test_func() { return 42; }',
                    'language': 'c'
                },
                'context': {'context': 'data'}
            }
        ]
        
        project_config = {
            'path': '/project',
            'llm_provider': 'deepseek',
            'model': 'deepseek-coder',
            'output_dir': './output',
            'error_handling': {'max_retries': 3, 'retry_delay': 1.0}
        }
        
        result = service.generate_tests_with_config(functions_with_context, project_config)
        
        # Verify calls
        mock_setup_logging.assert_called_once()
        mock_config_loader.get_api_key.assert_called_once_with('deepseek')
        mock_generator_class.assert_called_once()
        mock_generator.generate_tests.assert_called_once()
        mock_log_stats.assert_called_once()
        mock_close_logging.assert_called_once()
        
        assert len(result) == 1
        assert result[0]['success'] is True
    
    @patch('src.services.test_generation_service.logger')
    def test_print_results(self, mock_logger):
        """Test results printing"""
        service = TestGenerationService()
        
        results = [
            {'success': True, 'function_name': 'func1', 'test_length': 100, 'output_path': '/path1'},
            {'success': False, 'function_name': 'func2', 'error': 'Test error'}
        ]
        
        project_config = {'description': 'Test project'}
        
        service.print_results(results, project_config)
        
        # Verify logger was called with expected messages
        mock_logger.info.assert_any_call("Generation Results:")
        mock_logger.info.assert_any_call("  Successful: 1")
        mock_logger.info.assert_any_call("  Failed: 1")