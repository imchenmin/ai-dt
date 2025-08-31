"""
Backward-compatible configuration loader that delegates to ConfigManager
"""

import os
from typing import Dict, Any, Optional
from src.utils.config_manager import config_manager
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """Backward-compatible configuration loader that delegates to ConfigManager"""
    
    @staticmethod
    def get_llm_config(provider: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM provider"""
        return config_manager.get_llm_provider_config(provider)
    
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key for a specific provider from environment"""
        return config_manager.get_api_key_for_provider(provider)
    
    @staticmethod
    def is_provider_available(provider: str) -> bool:
        """Check if a provider is configured and available"""
        return config_manager.is_provider_available_standalone(provider)
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """Get all available providers and their status"""
        return config_manager.get_available_providers_list()
    
    @staticmethod
    def print_provider_status():
        """Print status of all LLM providers"""
        config_manager.print_provider_status()


# Example usage
if __name__ == "__main__":
    ConfigLoader.print_provider_status()