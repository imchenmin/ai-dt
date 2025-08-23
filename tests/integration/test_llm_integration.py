#!/usr/bin/env python3
"""
Test script for LLM integration and test generation
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure libclang using unified configuration
from src.utils.libclang_config import ensure_libclang_configured
ensure_libclang_configured()

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator

def test_llm_generation():
    """Test LLM-based test generation"""
    print("=== Testing LLM Test Generation ===")
    
    # Test with C project
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/c")
    
    # Use mock LLM client for testing
    test_generator = TestGenerator(llm_provider="mock")
    
    print("\n--- Analyzing and Generating Tests ---")
    
    functions_with_context = []
    
    for unit in compilation_units:
        if 'math_utils.c' in unit['file']:
            print(f"\nAnalyzing {unit['file']}:")
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                print(f"  Processing function: {func['name']}")
                
                # Get full context
                func['context'] = analyzer._analyze_function_context(
                    func, unit['arguments'], compilation_units
                )
                
                functions_with_context.append({
                    'function': func,
                    'context': func['context']
                })
    
    # Generate tests
    print("\n--- Generating Tests with LLM ---")
    results = test_generator.generate_tests(
        functions_with_context,
        output_dir="./generated_tests"
    )
    
    # Print summary
    summary = test_generator.generate_summary_report(results)
    print(f"\n{summary}")
    
    # Show sample generated test
    successful_tests = [r for r in results if r['success']]
    if successful_tests:
        print("\n--- Sample Generated Test ---")
        sample_test = successful_tests[0]
        print(f"Function: {sample_test['function_name']}")
        print(f"Output: {sample_test.get('output_path', 'unknown')}")
        print("\nTest code preview:")
        print("=" * 50)
        print(sample_test['test_code'][:500] + "..." 
              if len(sample_test['test_code']) > 500 else sample_test['test_code'])
        print("=" * 50)


def test_real_llm_integration():
    """Test with real LLM API (if configured)"""
    print("\n=== Testing Real LLM Integration ===")
    
    # Check if OpenAI API key is available
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        print("OPENAI_API_KEY not found in environment variables.")
        print("To test with real OpenAI API, set your API key:")
        print("export OPENAI_API_KEY=your_api_key_here")
        print("Skipping real API test...")
        return
    
    print("OpenAI API key found. Testing real integration...")
    
    # Test with a single function to save tokens
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/c")
    
    # Use real OpenAI client
    test_generator = TestGenerator(
        llm_provider="openai",
        api_key=api_key,
        model="gpt-3.5-turbo"
    )
    
    # Find just the divide function
    target_function = None
    context = None
    
    for unit in compilation_units:
        if 'math_utils.c' in unit['file']:
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                if func['name'] == 'divide':
                    target_function = func
                    # Get full context
                    target_function['context'] = analyzer._analyze_function_context(
                        func, unit['arguments'], compilation_units
                    )
                    context = target_function['context']
                    break
            
            if target_function:
                break
    
    if target_function and context:
        print(f"\nGenerating test for: {target_function['name']}")
        
        result = test_generator.generate_test(target_function, context)
        
        if result['success']:
            print("✅ Successfully generated test with real OpenAI API!")
            print(f"Tokens used: {result.get('usage', {})}")
            
            # Save the test
            output_path = test_generator.llm_client.save_test_code(
                result['test_code'],
                target_function['name'],
                "./generated_tests_real"
            )
            print(f"Saved to: {output_path}")
            
            print("\nGenerated test:")
            print("=" * 50)
            print(result['test_code'])
            print("=" * 50)
        else:
            print(f"❌ Failed: {result['error']}")
    else:
        print("Target function 'divide' not found.")


def main():
    """Run LLM integration tests"""
    try:
        test_llm_generation()
        test_real_llm_integration()
        
    except Exception as e:
        print(f"Error during LLM integration testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()