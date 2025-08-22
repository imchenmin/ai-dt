#!/usr/bin/env python3
"""
Check current environment configuration for LLM providers
"""

import os
from src.utils.config_loader import ConfigLoader

def check_environment():
    """Check current environment setup"""
    print("Environment Configuration Check")
    print("=" * 40)
    
    # Check API keys
    providers = ['openai', 'deepseek', 'anthropic']
    
    for provider in providers:
        api_key = ConfigLoader.get_api_key(provider)
        status = "[SET]" if api_key else "[NOT SET]"
        config = ConfigLoader.get_llm_config(provider)
        
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