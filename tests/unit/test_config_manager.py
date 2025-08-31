"""
Tests for utils.config_manager module
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from src.utils.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager"""
    
    def create_test_config(self) -> dict:
        """Helper to create a valid test configuration"""
        return {
            'defaults': {
                'llm_provider': 'deepseek',
                'model': 'deepseek-coder',
                'max_tokens': 2500,
                'temperature': 0.3,
                'output_dir': './test_output'
            },
            'projects': {
                'test_project': {
                    'path': '/path/to/project',
                    'comp_db': 'compile_commands.json',
                    'description': 'Test project'
                }
            },
            'llm_providers': {
                'deepseek': {
                    'api_key_env': 'DEEPSEEK_API_KEY',
                    'base_url': 'https://api.deepseek.com/v1',
                    'models': ['deepseek-chat', 'deepseek-coder'],
                    'default_model': 'deepseek-coder'
                },
                'openai': {
                    'api_key_env': 'OPENAI_API_KEY',
                    'base_url': 'https://api.openai.com/v1',
                    'models': ['gpt-3.5-turbo', 'gpt-4'],
                    'default_model': 'gpt-3.5-turbo'
                }
            },
            'profiles': {
                'quick': {
                    'description': 'Quick test generation',
                    'max_functions': 3,
                    'max_workers': 1
                }
            }
        }
    
    def test_init_with_existing_config_file(self):
        """Test ConfigManager initialization with existing config file"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            assert manager.config_path == Path(config_path)
            assert manager.config['defaults']['llm_provider'] == 'deepseek'
            assert 'test_project' in manager.config['projects']
            
        finally:
            os.unlink(config_path)
    
    def test_init_with_nonexistent_config_file(self):
        """Test ConfigManager initialization with nonexistent config file"""
        with pytest.raises(SystemExit):
            ConfigManager('/nonexistent/config.yaml')
    
    def test_validate_config_adds_defaults(self):
        """Test that _validate_config adds missing sections and defaults"""
        minimal_config = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(minimal_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            # Check that all required sections were added
            assert 'defaults' in manager.config
            assert 'projects' in manager.config
            assert 'llm_providers' in manager.config
            assert 'profiles' in manager.config
            
            # Check that default values were set
            defaults = manager.config['defaults']
            assert defaults['llm_provider'] == 'deepseek'
            assert defaults['model'] == 'deepseek-coder'
            assert defaults['max_tokens'] == 2500
            assert defaults['temperature'] == 0.3
            assert 'error_handling' in defaults
            assert 'filter' in defaults
            assert 'context_compression' in defaults
            
            # Check that default profiles were added
            profiles = manager.config['profiles']
            assert 'quick' in profiles
            assert 'comprehensive' in profiles
            assert 'custom' in profiles
            
        finally:
            os.unlink(config_path)
    
    def test_get_project_config_success(self):
        """Test successful project config retrieval"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            project_config = manager.get_project_config('test_project')
            
            assert project_config['path'] == '/path/to/project'
            assert project_config['comp_db'] == 'compile_commands.json'
            assert project_config['description'] == 'Test project'
            
            # Should include defaults
            assert project_config['llm_provider'] == 'deepseek'
            assert project_config['model'] == 'deepseek-coder'
            
        finally:
            os.unlink(config_path)
    
    def test_get_project_config_not_found(self):
        """Test project config retrieval for nonexistent project"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            with pytest.raises(ValueError, match="Project 'nonexistent' not found"):
                manager.get_project_config('nonexistent')
                
        finally:
            os.unlink(config_path)
    
    def test_get_project_config_missing_required_fields(self):
        """Test project config validation for missing required fields"""
        test_config = {
            'defaults': {},
            'projects': {
                'invalid_project': {
                    'description': 'Missing required fields'
                    # Missing 'path' and 'comp_db'
                }
            },
            'llm_providers': {},
            'profiles': {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            with pytest.raises(ValueError, match="missing required 'path' field"):
                manager.get_project_config('invalid_project')
                
        finally:
            os.unlink(config_path)
    
    def test_get_llm_config_success(self):
        """Test successful LLM config retrieval"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            llm_config = manager.get_llm_config('deepseek')
            
            assert llm_config['api_key_env'] == 'DEEPSEEK_API_KEY'
            assert llm_config['base_url'] == 'https://api.deepseek.com/v1'
            assert 'deepseek-coder' in llm_config['models']
            
        finally:
            os.unlink(config_path)
    
    def test_get_llm_config_not_found(self):
        """Test LLM config retrieval for nonexistent provider"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            with pytest.raises(ValueError, match="LLM provider 'unknown' not configured"):
                manager.get_llm_config('unknown')
                
        finally:
            os.unlink(config_path)
    
    def test_get_profile_config_success(self):
        """Test successful profile config retrieval"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            profile_config = manager.get_profile_config('quick')
            
            assert profile_config['description'] == 'Quick test generation'
            assert profile_config['max_functions'] == 3
            assert profile_config['max_workers'] == 1
            
        finally:
            os.unlink(config_path)
    
    def test_get_profile_config_not_found(self):
        """Test profile config retrieval for nonexistent profile"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            with pytest.raises(ValueError, match="Profile 'unknown' not found"):
                manager.get_profile_config('unknown')
                
        finally:
            os.unlink(config_path)
    
    def test_list_projects(self):
        """Test listing available projects"""
        test_config = self.create_test_config()
        test_config['projects']['another_project'] = {
            'path': '/path/to/another',
            'comp_db': 'compile_commands.json',
            'description': 'Another test project'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            projects = manager.list_projects()
            
            assert len(projects) == 2
            assert projects['test_project'] == 'Test project'
            assert projects['another_project'] == 'Another test project'
            
        finally:
            os.unlink(config_path)
    
    def test_list_providers(self):
        """Test listing available LLM providers"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            providers = manager.list_providers()
            
            assert 'deepseek' in providers
            assert 'openai' in providers
            # Availability will be False unless env vars are set
            assert isinstance(providers['deepseek'], bool)
            assert isinstance(providers['openai'], bool)
            
        finally:
            os.unlink(config_path)
    
    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'})
    def test_is_provider_available_true(self):
        """Test provider availability check when API key is set"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            assert manager.is_provider_available('deepseek') is True
            assert manager.is_provider_available('openai') is False  # No OPENAI_API_KEY set
            
        finally:
            os.unlink(config_path)
    
    def test_is_provider_available_unknown_provider(self):
        """Test provider availability check for unknown provider"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            assert manager.is_provider_available('unknown') is False
            
        finally:
            os.unlink(config_path)
    
    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'})
    def test_get_api_key_success(self):
        """Test successful API key retrieval"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            api_key = manager.get_api_key('deepseek')
            assert api_key == 'test_key'
            
        finally:
            os.unlink(config_path)
    
    def test_get_api_key_not_set(self):
        """Test API key retrieval when environment variable is not set"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            # Make sure the env var is not set
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            api_key = manager.get_api_key('openai')
            assert api_key is None
            
        finally:
            os.unlink(config_path)
    
    def test_get_api_key_unknown_provider(self):
        """Test API key retrieval for unknown provider"""
        test_config = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            api_key = manager.get_api_key('unknown')
            assert api_key is None
            
        finally:
            os.unlink(config_path)
    
    def test_config_with_malformed_yaml(self):
        """Test ConfigManager with malformed YAML file"""
        malformed_yaml = "invalid: yaml: content: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_yaml)
            config_path = f.name
        
        try:
            with pytest.raises(SystemExit):
                ConfigManager(config_path)
                
        finally:
            os.unlink(config_path)