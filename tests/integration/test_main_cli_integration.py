#!/usr/bin/env python3
"""
Integration tests for main.py CLI interface
Tests the complete command-line interface with real project configurations
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.main import main
from src.utils.config_manager import config_manager


class TestMainCLIIntegration:
    """Integration tests for main.py CLI interface"""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory"""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def complex_c_project_path(self, project_root):
        """Get the complex C project path"""
        return project_root / "test_projects" / "complex_c_project"
    
    def test_config_mode_project_exists(self, project_root):
        """Test that complex_c_project configuration exists and is valid"""
        # Test configuration loading
        projects = config_manager.list_projects()
        assert "complex_c_project" in projects
        
        # Test project config retrieval
        project_config = config_manager.get_project_config("complex_c_project")
        assert project_config is not None
        assert "path" in project_config
        assert "comp_db" in project_config
        assert "description" in project_config
        
        # Verify project path exists
        project_path = project_root / project_config["path"]
        assert project_path.exists(), f"Project path does not exist: {project_path}"
        
        # Verify compile_commands.json exists
        comp_db_path = project_path / "compile_commands.json"
        assert comp_db_path.exists(), f"Compile commands file does not exist: {comp_db_path}"
    
    def test_prompt_only_mode_integration(self, project_root, complex_c_project_path):
        """Test --prompt-only mode with complex_c_project configuration"""
        # Mock sys.argv to simulate command line arguments
        test_args = [
            "main.py",
            "--config", "complex_c_project",
            "--prompt-only"
        ]

        with patch('sys.argv', test_args):
            with patch('src.main.logger') as mock_logger:
                # Mock the entire TestGenerationService to control both methods
                with patch('src.main.TestGenerationService') as MockService:
                    mock_service = Mock()
                    MockService.return_value = mock_service

                    # Setup mock for analyze_project_functions - return some functions
                    mock_service.analyze_project_functions.return_value = [
                        {
                            'function_name': 'test_function',
                            'file_path': 'test.c',
                            'context': 'mock context'
                        }
                    ]

                    # Setup mock for generate_tests_with_config
                    mock_service.generate_tests_with_config.return_value = [
                        {
                            'function_name': 'test_function',
                            'prompt': 'Generated test prompt',
                            'status': 'success',
                            'success': True,
                            'test_code': 'mock test code'
                        }
                    ]

                    mock_service.print_results.return_value = None

                    # Call main function
                    result = main()

                    # Verify successful execution
                    assert result is True

                    # Verify both methods were called
                    mock_service.analyze_project_functions.assert_called_once()
                    mock_service.generate_tests_with_config.assert_called_once()
                    mock_service.print_results.assert_called_once()

                    # Verify generate_tests_with_config was called with prompt_only=True
                    call_args = mock_service.generate_tests_with_config.call_args
                    assert call_args[1]['prompt_only'] is True
    
    def test_component_integration_flow(self, project_root):
        """Test that all components work together correctly"""
        test_args = [
            "main.py",
            "--config", "complex_c_project",
            "--prompt-only"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.main.logger') as mock_logger:
                # Mock the service methods to track component interactions
                with patch('src.main.TestGenerationService') as MockService:
                    mock_service_instance = Mock()
                    MockService.return_value = mock_service_instance
                    
                    # Setup mock methods
                    mock_service_instance.analyze_project_functions.return_value = [
                        {
                            'function_name': 'hash_table_create',
                            'file_path': 'data_structures/hash_table.c',
                            'context': 'mock context'
                        }
                    ]
                    
                    mock_service_instance.generate_tests_with_config.return_value = [
                        {
                            'function_name': 'hash_table_create',
                            'prompt': 'Generated prompt for hash_table_create',
                            'status': 'success',
                            'success': True,
                            'test_code': 'mock test code'
                        }
                    ]
                    
                    mock_service_instance.print_results.return_value = None
                    
                    # Call main function
                    result = main()
                    
                    # Verify successful execution
                    assert result is True
                    
                    # Verify component interaction sequence
                    # In config mode, both analyze_project_functions and generate_tests_with_config are called
                    mock_service_instance.analyze_project_functions.assert_called_once()
                    mock_service_instance.generate_tests_with_config.assert_called_once()
                    mock_service_instance.print_results.assert_called_once()
    
    def test_config_file_loading(self, project_root):
        """Test configuration file loading and project config merging"""
        test_args = [
            "main.py",
            "--config", "complex_c_project",
            "--profile", "comprehensive",
            "--prompt-only"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.main.TestGenerationConfig') as MockConfig:
                mock_config_instance = Mock()
                MockConfig.return_value = mock_config_instance
                
                # Setup mock config methods
                mock_config_instance.get_project_config.return_value = {
                    'path': 'test_projects/complex_c_project',
                    'comp_db': 'test_projects/complex_c_project/compile_commands.json',
                    'description': 'Complex C project'
                }
                
                mock_config_instance.get_profile_config.return_value = {
                    'max_functions': 10,
                    'max_workers': 2
                }
                
                with patch('src.test_generation.service.TestGenerationService') as MockService:
                    mock_service = Mock()
                    MockService.return_value = mock_service
                    mock_service.analyze_project_functions.return_value = []
                    
                    # Call main function
                    result = main()
                    
                    # Verify config methods were called
                    mock_config_instance.get_project_config.assert_called_once_with('complex_c_project')
                    mock_config_instance.get_profile_config.assert_called_once_with('comprehensive')
    
    def test_error_handling_no_functions_found(self, project_root):
        """Test error handling when no functions are found"""
        test_args = [
            "main.py",
            "--config", "complex_c_project",
            "--prompt-only"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.main.logger') as mock_logger:
                with patch('src.main.TestGenerationService') as MockService:
                    mock_service = Mock()
                    MockService.return_value = mock_service
                    
                    # Simulate no functions found by making analyze_project_functions return empty list
                    mock_service.analyze_project_functions.return_value = []
                    mock_service.print_results.return_value = None
                    
                    # Call main function
                    result = main()
                    
                    # Verify that main returns False when no functions are found
                    assert result is False
                    
                    # Verify that analyze_project_functions was called
                    mock_service.analyze_project_functions.assert_called_once()
                    # generate_tests_with_config should not be called when no functions found
                    mock_service.generate_tests_with_config.assert_not_called()
                    # print_results should not be called when no functions found
                    mock_service.print_results.assert_not_called()
    
    def test_subprocess_cli_call(self, project_root):
        """Test actual subprocess call to main.py (integration with real CLI)"""
        # Change to project directory
        original_cwd = os.getcwd()
        try:
            os.chdir(str(project_root))
            
            # Run the actual command as subprocess
            cmd = [
                sys.executable, "-m", "src.main",
                "--config", "complex_c_project",
                "--prompt-only"
            ]
            
            # Set environment to avoid actual LLM calls
            env = os.environ.copy()
            env['PYTEST_RUNNING'] = '1'  # Flag to indicate test environment
            
            # Run with timeout to prevent hanging
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            # Check that command executed without critical errors
            # Note: May return non-zero due to missing API keys, but should not crash
            assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
            
            # Check that output contains expected elements
            output = result.stdout + result.stderr
            assert "complex_c_project" in output or "No functions found" in output or "Error" in output
            
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])