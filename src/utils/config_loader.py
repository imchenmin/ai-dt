"""
Configuration loader for LLM providers
"""

import os
from typing import Dict, Any, Optional
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """Loads configuration for different LLM providers"""
    
    @staticmethod
    def get_llm_config(provider: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM provider"""
        configs = {
            "openai": {
                "api_key_env": "OPENAI_API_KEY",
                "default_model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
            },
            "deepseek": {
                "api_key_env": "DEEPSEEK_API_KEY",
                "default_model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
                "models": ["deepseek-chat", "deepseek-coder"]
            },
            "anthropic": {
                "api_key_env": "ANTHROPIC_API_KEY",
                "default_model": "claude-3-sonnet",
                "base_url": "https://api.anthropic.com/v1",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
            }
        }
        
        if provider not in configs:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return configs[provider]
    
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key for a specific provider from environment"""
        config = ConfigLoader.get_llm_config(provider)
        return os.environ.get(config["api_key_env"])
    
    @staticmethod
    def is_provider_available(provider: str) -> bool:
        """Check if a provider is configured and available"""
        return ConfigLoader.get_api_key(provider) is not None
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """Get all available providers and their status"""
        providers = ["openai", "deepseek", "anthropic"]
        return {provider: ConfigLoader.is_provider_available(provider) for provider in providers}
    
    @staticmethod
    def print_provider_status():
        """Print status of all LLM providers"""
        logger.info("LLM Provider Status:")
        logger.info("=" * 40)
        
        providers = ConfigLoader.get_available_providers()
        
        for provider, available in providers.items():
            status = "✅ Available" if available else "❌ Not configured"
            config = ConfigLoader.get_llm_config(provider)
            
            logger.info(f"{provider.upper()}:")
            logger.info(f"  Status: {status}")
            logger.info(f"  API Key Env: {config['api_key_env']}")
            logger.info(f"  Default Model: {config['default_model']}")
            logger.info(f"  Available Models: {', '.join(config['models'])}")
            logger.info("")
        
        if not any(providers.values()):
            logger.info("No LLM providers configured. Set API keys for:")
            logger.info("  - OPENAI_API_KEY for OpenAI")
            logger.info("  - DEEPSEEK_API_KEY for DeepSeek") 
            logger.info("  - ANTHROPIC_API_KEY for Anthropic")


# Example usage
if __name__ == "__main__":
    ConfigLoader.print_provider_status()