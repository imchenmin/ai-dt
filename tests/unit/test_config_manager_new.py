"""
Test configuration management
"""

import os
import pytest
import tempfile
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

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file"""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Configuration file not found"):
                ConfigManager("non_existent.yaml")

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML file"""
        invalid_yaml = "invalid: yaml: content:\n  - missing\n    - proper"
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=invalid_yaml)):
            # YAML parsing errors are handled by yaml.safe_load
            ConfigManager("invalid.yaml")

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

    def test_get_project_config(self):
        """Test getting project configuration"""
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
        """Test getting default LLM provider"""
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
                'openai': {
                    'api_key': 'test-key',
                    'base_url': 'https://api.openai.com/v1',
                    'model': 'gpt-4'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            provider_config = manager.get_llm_provider_config('openai')

            assert provider_config['api_key'] == 'test-key'
            assert provider_config['base_url'] == 'https://api.openai.com/v1'
            assert provider_config['model'] == 'gpt-4'

    def test_get_llm_provider_config_not_found(self):
        """Test getting non-existent LLM provider configuration"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='llm_providers: {}\n')):
            manager = ConfigManager()

            with pytest.raises(KeyError):
                manager.get_llm_provider_config('non_existent_provider')

    def test_get_api_key_for_provider(self):
        """Test getting API key for provider"""
        config_data = {
            'llm_providers': {
                'deepseek': {
                    'api_key': 'deepseek-key-123'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            api_key = manager.get_api_key_for_provider('deepseek')

            assert api_key == 'deepseek-key-123'

    def test_get_api_key_from_env(self):
        """Test getting API key from environment variable"""
        config_data = {
            'llm_providers': {
                'openai': {
                    'api_key_env': 'OPENAI_API_KEY'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key-456'}):
            manager = ConfigManager()
            api_key = manager.get_api_key_for_provider('openai')

            assert api_key == 'env-key-456'

    def test_get_api_key_not_found(self):
        """Test getting API key when not found"""
        config_data = {
            'llm_providers': {
                'test_provider': {}
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            api_key = manager.get_api_key_for_provider('test_provider')

            assert api_key is None

    def test_get_profile_config(self):
        """Test getting profile configuration"""
        config_data = {
            'profiles': {
                'quick': {
                    'max_functions': 5,
                    'timeout': 600
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            profile = manager.get_profile_config('quick')

            assert profile['max_functions'] == 5
            assert profile['timeout'] == 600

    def test_is_provider_available_true(self):
        """Test checking if provider is available - true case"""
        config_data = {
            'llm_providers': {
                'openai': {
                    'api_key': 'test-key'
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            available = manager.is_provider_available('openai')

            assert available is True

    def test_is_provider_available_false_no_key(self):
        """Test checking if provider is available - no API key"""
        config_data = {
            'llm_providers': {
                'openai': {}
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()
            available = manager.is_provider_available('openai')

            assert available is False

    def test_is_provider_available_false_not_found(self):
        """Test checking if provider is available - provider not found"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='llm_providers: {}\n')):
            manager = ConfigManager()
            available = manager.is_provider_available('non_existent')

            assert available is False

    def test_merge_with_defaults(self):
        """Test merging config with defaults"""
        config_data = {
            'defaults': {
                'llm_provider': 'openai',
                'temperature': 0.7,
                'max_tokens': 2000
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()

            override = {'temperature': 0.5, 'model': 'gpt-4'}
            merged = manager.merge_with_defaults(override)

            # Should keep defaults for missing keys
            assert merged['llm_provider'] == 'openai'
            assert merged['max_tokens'] == 2000

            # Should use override values
            assert merged['temperature'] == 0.5
            assert merged['model'] == 'gpt-4'

    def test_list_projects(self):
        """Test listing all projects"""
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

    def test_list_projects_empty(self):
        """Test listing projects when none defined"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='projects: {}\n')):
            manager = ConfigManager()
            projects = manager.list_projects()

            assert projects == []

    def test_update_config_value(self):
        """Test updating a configuration value"""
        config_data = {
            'defaults': {
                'temperature': 0.7
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()

            # Update value
            manager.update_config_value('defaults.temperature', 0.9)

            assert manager.config['defaults']['temperature'] == 0.9

    def test_update_config_value_nested(self):
        """Test updating a nested configuration value"""
        config_data = {
            'defaults': {
                'error_handling': {
                    'max_retries': 3
                }
            }
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml.dump(config_data))):
            manager = ConfigManager()

            # Update nested value
            manager.update_config_value('defaults.error_handling.max_retries', 5)

            assert manager.config['defaults']['error_handling']['max_retries'] == 5

    def test_update_config_value_new_key(self):
        """Test updating a new configuration key"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='defaults: {}\n')):
            manager = ConfigManager()

            # Add new key
            manager.update_config_value('defaults.new_setting', 'test_value')

            assert manager.config['defaults']['new_setting'] == 'test_value'