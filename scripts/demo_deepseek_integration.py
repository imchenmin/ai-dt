#!/usr/bin/env python3
"""
Demo script for DeepSeek integration
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure libclang using unified configuration
from src.utils.libclang_config import ensure_libclang_configured
ensure_libclang_configured()

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.context_compressor import ContextCompressor
from src.utils.config_loader import ConfigLoader

def demo_deepseek_integration():
    """Demonstrate DeepSeek integration for test generation"""
    print("DeepSeek Integration Demo")
    print("=" * 40)
    
    # Parse compilation database
    print("\n1. Parsing compile_commands.json...")
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    # Analyze functions
    print("\n2. Analyzing source code...")
    analyzer = FunctionAnalyzer("test_projects/c")
    
    # Find the divide function specifically
    target_function = None
    context = None
    
    for unit in compilation_units:
        if 'math_utils.c' in unit['file']:
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                if func['name'] == 'divide':
                    target_function = func
                    # Get complete context
                    target_function['context'] = analyzer._analyze_function_context(
                        func, unit['arguments'], compilation_units
                    )
                    context = target_function['context']
                    break
            
            if target_function:
                break
    
    if not target_function:
        print("Target function 'divide' not found.")
        return
    
    print(f"   Found target function: {target_function['name']}")
    
    # Prepare context for LLM
    print("\n3. Preparing context for DeepSeek...")
    compressor = ContextCompressor()
    compressed_context = compressor.compress_function_context(target_function, context)
    prompt = compressor.format_for_llm_prompt(compressed_context)
    
    print(f"   Context size: {len(prompt)} characters")
    print(f"   Call sites: {len(context.get('call_sites', []))}")
    
    # Check if DeepSeek API key is available
    api_key = ConfigLoader.get_api_key("deepseek")
    
    if not api_key:
        print("\n4. DeepSeek API Configuration:")
        print("   DEEPSEEK_API_KEY not found in environment variables.")
        print("   To use DeepSeek API, set your API key:")
        print("   export DEEPSEEK_API_KEY=your_deepseek_api_key_here")
        
        deepseek_config = ConfigLoader.get_llm_config("deepseek")
        print(f"   \nAvailable DeepSeek models: {', '.join(deepseek_config['models'])}")
        print("   \nExample usage:")
        print("   export DEEPSEEK_API_KEY=your_key")
        print("   python demo_deepseek_integration.py")
        return
    
    print(f"\n4. Using DeepSeek API with key: {api_key[:10]}...")
    
    # Test with different DeepSeek models
    deepseek_models = ["deepseek-chat", "deepseek-coder"]
    
    for model_name in deepseek_models:
        print(f"\n5. Testing with model: {model_name}")
        print("-" * 30)
        
        try:
            test_generator = TestGenerator(
                llm_provider="deepseek",
                api_key=api_key,
                model=model_name
            )
            
            result = test_generator.generate_test(target_function, context)
            
            if result['success']:
                print(f"   [SUCCESS] Successfully generated test with {model_name}")
                print(f"   Tokens used: {result.get('usage', {})}")
                print(f"   Test length: {len(result['test_code'])} characters")
                
                # Save the test
                output_dir = f"./generated_tests_deepseek_{model_name}"
                output_path = test_generator.llm_client.save_test_code(
                    result['test_code'],
                    target_function['name'],
                    output_dir
                )
                print(f"   Saved to: {output_path}")
                
                # Show test preview
                print("   \nTest preview:")
                lines = result['test_code'].split('\n')
                for line in lines[:8]:  # Show first 8 lines
                    print(f"     {line}")
                if len(lines) > 8:
                    print("     ...")
                    
            else:
                print(f"   [FAILED] Failed with {model_name}: {result['error']}")
                
        except Exception as e:
            print(f"   [ERROR] Error with {model_name}: {e}")
        
        # Add delay between API calls
        import time
        time.sleep(2)
    
    print("\n6. Demo completed!")
    print("   Check the generated_tests_deepseek_* directories for results.")


def main():
    """Run DeepSeek integration demo"""
    try:
        demo_deepseek_integration()
    except Exception as e:
        print(f"Error during DeepSeek demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()