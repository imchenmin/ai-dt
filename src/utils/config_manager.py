"""
Centralized configuration management with validation and defaults
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.utils.logging_utils import get_logger
from src.utils.error_handler import with_error_handling

logger = get_logger(__name__)


class ConfigManager:
    """Centralized configuration management with validation"""
    
    def __init__(self, config_path: str = "config/test_generation.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    @with_error_handling(context="config loading", critical=True)
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return self._validate_config(config)
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration structure and set defaults"""
        # Ensure required sections exist
        if 'defaults' not in config:
            config['defaults'] = {}
        if 'projects' not in config:
            config['projects'] = {}
        if 'llm_providers' not in config:
            config['llm_providers'] = {}
        if 'profiles' not in config:
            config['profiles'] = {}
        
        # Set default values
        defaults = config['defaults']
        defaults.setdefault('llm_provider', 'deepseek')
        defaults.setdefault('model', 'deepseek-coder')
        defaults.setdefault('max_tokens', 2500)
        defaults.setdefault('temperature', 0.3)
        defaults.setdefault('output_dir', './experiment/generated_tests')
        
        # Set default error handling
        defaults.setdefault('error_handling', {
            'max_retries': 3,
            'retry_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0
        })
        
        # Set default filtering
        defaults.setdefault('filter', {
            'skip_std_lib': True,
            'skip_compiler_builtins': True,
            'skip_operators': True,
            'skip_special_functions': True,
            'custom_include_patterns': [],
            'custom_exclude_patterns': []
        })

        # Set default context compression
        defaults.setdefault('context_compression', {
            'enabled': True,
            'compression_level': 1,
            'max_context_size': None
        })
        
        # Set default profiles
        profiles = config['profiles']
        profiles.setdefault('quick', {
            'description': "Quick test generation with minimal coverage",
            'max_functions': 3,
            'test_cases_per_function': 3,
            'max_workers': 1,
            'timeout': 300
        })
        
        profiles.setdefault('comprehensive', {
            'description': "Comprehensive test generation with full coverage",
            'max_functions': 20,
            'test_cases_per_function': 10,
            'max_workers': 3,
            'timeout': 1800
        })
        
        profiles.setdefault('custom', {
            'description': "Custom configuration for specific needs",
            'max_functions': None,
            'test_cases_per_function': None,
            'max_workers': 5,
            'timeout': 3600
        })
        
        return config
    
    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get validated project configuration with defaults applied"""
        projects = self.config.get('projects', {})
        
        if project_name not in projects:
            available = list(projects.keys())
            raise ValueError(f"Project '{project_name}' not found. Available: {', '.join(available)}")
        
        project_config = projects[project_name].copy()
        defaults = self.config.get('defaults', {})
        
        # Apply defaults for missing keys
        for key, value in defaults.items():
            if key not in project_config:
                project_config[key] = value
        
        # Ensure required fields
        if 'path' not in project_config:
            raise ValueError(f"Project '{project_name}' missing required 'path' field")
        if 'comp_db' not in project_config:
            raise ValueError(f"Project '{project_name}' missing required 'comp_db' field")
        
        return project_config
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration"""
        providers = self.config.get('llm_providers', {})
        
        if provider not in providers:
            available = list(providers.keys())
            raise ValueError(f"LLM provider '{provider}' not configured. Available: {', '.join(available)}")
        
        return providers[provider]
    
    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Get execution profile configuration"""
        profiles = self.config.get('profiles', {})
        
        if profile_name not in profiles:
            available = list(profiles.keys())
            raise ValueError(f"Profile '{profile_name}' not found. Available: {', '.join(available)}")
        
        return profiles[profile_name]
    
    def list_projects(self) -> Dict[str, str]:
        """List all available projects with descriptions"""
        projects = self.config.get('projects', {})
        return {
            name: config.get('description', 'No description')
            for name, config in projects.items()
        }
    
    def list_providers(self) -> Dict[str, bool]:
        """List all LLM providers and their availability"""
        providers = self.config.get('llm_providers', {})
        return {
            provider: self.is_provider_available(provider)
            for provider in providers.keys()
        }
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is configured and available"""
        try:
            config = self.get_llm_config(provider)
            api_key_env = config.get('api_key_env')
            return bool(api_key_env and os.environ.get(api_key_env))
        except ValueError:
            return False
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider from environment"""
        try:
            config = self.get_llm_config(provider)
            api_key_env = config.get('api_key_env')
            return os.environ.get(api_key_env) if api_key_env else None
        except ValueError:
            return None


# Global config manager instance
config_manager = ConfigManager()