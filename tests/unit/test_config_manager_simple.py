"""
Test configuration management - Simple version
"""

import os
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.config_manager import ConfigManager


class TestConfigManager:
    """Test configuration manager functionality"""

    def test_init_default_path(self):
        """Test initialization with default config path"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='defaults:\n  llm_provider: openai\n')):
            manager = ConfigManager()
            assert manager.config_path == Path("config/test_generation.yaml")
            assert 'defaults' in manager.config

    def test_init_custom_path(self):
        """Test initialization with custom config path"""
        custom_path = "/custom/config.yaml"
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='defaults:\n  llm_provider: deepseek\n')):
            manager = ConfigManager(custom_path)
            assert manager.config_path == Path(custom_path)

    def test_validate_config_empty_config(self):
        """Test validation of empty config"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()

            # Should add all required sections with defaults
            assert 'defaults' in manager.config
            assert 'projects' in manager.config
            assert 'llm_providers' in manager.config
            assert 'profiles' in manager.config

    def test_validate_config_with_existing_sections(self):
        """Test validation with existing sections"""
        config_data = {
            'defaults': {
                'llm_provider': 'openai',
                'temperature': 0.7
            },
            'projects': {
                'test_project': {
                    'path': 'test'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()

            # Should preserve existing values
            assert manager.config['defaults']['llm_provider'] == 'openai'
            assert manager.config['defaults']['temperature'] == 0.7
            assert 'test_project' in manager.config['projects']

    def test_validate_config_set_defaults(self):
        """Test that defaults are set correctly"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()
            defaults = manager.config['defaults']

            # Check default values
            assert defaults['llm_provider'] == 'deepseek'
            assert defaults['model'] == 'deepseek-coder'
            assert defaults['max_tokens'] == 2500
            assert defaults['temperature'] == 0.3
            assert defaults['output_dir'] == './experiment/generated_tests'
            assert defaults['unit_test_directory_path'] is None

    def test_validate_config_default_error_handling(self):
        """Test default error handling settings"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()
            error_handling = manager.config['defaults']['error_handling']

            assert error_handling['max_retries'] == 3
            assert error_handling['retry_delay'] == 1.0
            assert error_handling['max_delay'] == 60.0
            assert error_handling['backoff_factor'] == 2.0

    def test_validate_config_default_filter(self):
        """Test default filter settings"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()
            filter_config = manager.config['defaults']['filter']

            assert filter_config['skip_std_lib'] is True
            assert filter_config['skip_compiler_builtins'] is True
            assert filter_config['skip_operators'] is True
            assert filter_config['skip_special_functions'] is True
            assert filter_config['custom_include_patterns'] == []
            assert filter_config['custom_exclude_patterns'] == []

    def test_validate_config_default_context_compression(self):
        """Test default context compression settings"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()
            compression = manager.config['defaults']['context_compression']

            assert compression['enabled'] is True
            assert compression['compression_level'] == 1
            assert compression['max_context_size'] is None

    def test_validate_config_default_profiles(self):
        """Test default profiles"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()
            profiles = manager.config['profiles']

            # Check quick profile
            assert 'quick' in profiles
            quick = profiles['quick']
            assert quick['description'] == "Quick test generation with minimal coverage"
            assert quick['max_functions'] == 3
            assert quick['test_cases_per_function'] == 3
            assert quick['max_workers'] == 1
            assert quick['timeout'] == 300

            # Check comprehensive profile
            assert 'comprehensive' in profiles
            comp = profiles['comprehensive']
            assert comp['description'] == "Comprehensive test generation with full coverage"
            assert comp['max_functions'] == 20
            assert comp['test_cases_per_function'] == 10
            assert comp['max_workers'] == 3
            assert comp['timeout'] == 1800

            # Check custom profile
            assert 'custom' in profiles
            custom = profiles['custom']
            assert custom['description'] == "Custom configuration for specific needs"

    def test_get_default_llm_provider_config(self):
        """Test getting default LLM provider configuration"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()

            # Test OpenAI config
            openai_config = manager.get_default_llm_provider_config('openai')
            assert openai_config['api_key_env'] == 'OPENAI_API_KEY'
            assert openai_config['default_model'] == 'gpt-3.5-turbo'
            assert openai_config['base_url'] == 'https://api.openai.com/v1'

            # Test DeepSeek config
            deepseek_config = manager.get_default_llm_provider_config('deepseek')
            assert deepseek_config['api_key_env'] == 'DEEPSEEK_API_KEY'
            assert deepseek_config['default_model'] == 'deepseek-chat'
            assert deepseek_config['base_url'] == 'https://api.deepseek.com/v1'

            # Test unsupported provider
            with pytest.raises(ValueError, match="Unsupported provider"):
                manager.get_default_llm_provider_config('unsupported')

    def test_get_api_key_for_provider(self):
        """Test getting API key for provider"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()

            # With environment variable set
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'}):
                api_key = manager.get_api_key_for_provider('openai')
                assert api_key == 'test-key-123'

            # Without environment variable
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            api_key = manager.get_api_key_for_provider('openai')
            assert api_key is None

            # For unsupported provider
            api_key = manager.get_api_key_for_provider('unsupported')
            assert api_key is None

    def test_is_provider_available_standalone(self):
        """Test checking if provider is available"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()

            # With API key
            with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'}):
                available = manager.is_provider_available_standalone('deepseek')
                assert available is True

            # Without API key
            if 'DEEPSEEK_API_KEY' in os.environ:
                del os.environ['DEEPSEEK_API_KEY']
            available = manager.is_provider_available_standalone('deepseek')
            assert available is False

    def test_get_available_providers_list(self):
        """Test getting list of available providers"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{}')):
            manager = ConfigManager()

            # Mock environment variables
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'openai-key',
                'DEEPSEEK_API_KEY': 'deepseek-key'
            }):
                providers = manager.get_available_providers_list()

                assert providers['openai'] is True
                assert providers['deepseek'] is True
                assert providers['anthropic'] is False  # No key set

    def test_list_projects(self):
        """Test listing projects from config"""
        config_data = {
            'projects': {
                'project_a': {'path': '/a'},
                'project_b': {'path': '/b'},
                'project_c': {'path': '/c'}
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            projects = manager.list_projects()

            assert len(projects) == 3
            assert 'project_a' in projects
            assert 'project_b' in projects
            assert 'project_c' in projects
            assert projects['project_a']['path'] == '/a'

    def test_list_projects_empty(self):
        """Test listing projects when none defined"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='projects: {}\n')):
            manager = ConfigManager()
            projects = manager.list_projects()

            assert projects == {}

    def test_get_project_config(self):
        """Test getting specific project configuration"""
        config_data = {
            'projects': {
                'test_project': {
                    'path': '/test/path',
                    'compile_commands': '/test/compile_commands.json'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            project_config = manager.get_project_config('test_project')

            assert project_config['path'] == '/test/path'
            assert project_config['compile_commands'] == '/test/compile_commands.json'

    def test_get_project_config_not_found(self):
        """Test getting non-existent project configuration"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='projects: {}\n')):
            manager = ConfigManager()

            with pytest.raises(KeyError):
                manager.get_project_config('non_existent_project')

    def test_get_default_llm_provider(self):
        """Test getting default LLM provider from config"""
        config_data = {
            'defaults': {
                'llm_provider': 'openai'
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            provider = manager.get_default_llm_provider()

            assert provider == 'openai'

    def test_get_llm_provider_config(self):
        """Test getting LLM provider configuration"""
        config_data = {
            'llm_providers': {
                'custom_provider': {
                    'api_key': 'test-key',
                    'base_url': 'https://custom.api.com/v1',
                    'model': 'custom-model'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            provider_config = manager.get_llm_provider_config('custom_provider')

            assert provider_config['api_key'] == 'test-key'
            assert provider_config['base_url'] == 'https://custom.api.com/v1'
            assert provider_config['model'] == 'custom-model'

    def test_get_llm_provider_config_not_found(self):
        """Test getting non-existent LLM provider configuration"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='llm_providers: {}\n')):
            manager = ConfigManager()

            with pytest.raises(KeyError):
                manager.get_llm_provider_config('non_existent_provider')

    def test_get_profile_config(self):
        """Test getting profile configuration"""
        config_data = {
            'profiles': {
                'custom_profile': {
                    'max_functions': 10,
                    'timeout': 600,
                    'description': 'Custom test profile'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            profile = manager.get_profile_config('custom_profile')

            assert profile['max_functions'] == 10
            assert profile['timeout'] == 600
            assert profile['description'] == 'Custom test profile'

    def test_get_profile_config_not_found(self):
        """Test getting non-existent profile configuration"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='profiles: {}\n')):
            manager = ConfigManager()

            with pytest.raises(KeyError):
                manager.get_profile_config('non_existent_profile')