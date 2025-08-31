#!/usr/bin/env python3
"""
Check current environment configuration for LLM providers
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_manager import ConfigManager

def check_environment():
    """Check current environment setup"""
    print("Environment Configuration Check")
    print("=" * 40)
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Check API keys
    providers = ['openai', 'deepseek', 'anthropic']
    
    for provider in providers:
        api_key = config_manager.get_api_key_for_provider(provider)
        status = "[SET]" if api_key else "[NOT SET]"
        config = config_manager.get_llm_provider_config(provider)
        
        print(f"\n{provider.upper()}:")
        print(f"  API Key: {status}")
        if api_key:
            print(f"  Key Preview: {api_key[:10]}...{api_key[-4:]}")
        print(f"  Environment Variable: {config['api_key_env']}")
        print(f"  Default Model: {config['default_model']}")
        print(f"  Available Models: {', '.join(config['models'])}")
    
    # Check other important environment variables
    print(f"\nOther Environment Variables:")
    important_vars = ['PROJECT_ROOT', 'COMPILE_COMMANDS', 'LLM_PROVIDER', 'LOG_LEVEL']
    
    for var in important_vars:
        value = os.environ.get(var)
        status = "[SET]" if value else "[NOT SET]"
        print(f"  {var}: {status}")
        if value:
            print(f"    Value: {value}")

if __name__ == "__main__":
    check_environment()