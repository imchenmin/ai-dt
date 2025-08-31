#!/usr/bin/env python3
"""
Demo script showing complete LLM integration for test generation
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.test_generation.service import TestGenerationService
from src.utils.context_compressor import ContextCompressor
from src.utils.libclang_config import ensure_libclang_configured

def demo_complete_workflow():
    """Demonstrate the complete LLM test generation workflow"""
    print("AI-Driven C/C++ Test Generation - Complete Workflow")
    print("=" * 60)
    
    # Ensure libclang is configured
    ensure_libclang_configured()
    
    # Step 1: Parse compilation database
    print("\n1. Parsing compile_commands.json...")
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Step 2: Analyze functions
    print("\n2. Analyzing source code for testable functions...")
    analyzer = FunctionAnalyzer("test_projects/c")
    
    functions_with_context = []
    for unit in compilation_units:
        if 'math_utils.c' in unit['file']:
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                # Get complete context
                func['context'] = analyzer._analyze_function_context(
                    func, unit['arguments'], compilation_units
                )
                
                functions_with_context.append({
                    'function': func,
                    'context': func['context']
                })
                
                print(f"   - {func['name']}: {func['return_type']} function with {len(func['parameters'])} parameters")
    
    # Step 3: Prepare context for LLM
    print("\n3. Preparing context for LLM...")
    compressor = ContextCompressor()
    
    for func_data in functions_with_context:
        func = func_data['function']
        context = func_data['context']
        
        compressed = compressor.compress_function_context(func, context)
        prompt = compressor.format_for_llm_prompt(compressed)
        
        print(f"   - {func['name']}: {len(prompt)} chars context, {len(context.get('call_sites', []))} call sites")
    
    # Step 4: Generate tests with LLM
    print("\n4. Generating tests with TestGenerationService...")
    
    # Create project configuration for the service
    project_config = {
        'name': 'demo_project',
        'path': 'test_projects/c',
        'comp_db': comp_db_path,
        'llm_provider': 'openai',
        'model': 'gpt-3.5-turbo',
        'output_dir': './generated_tests_demo',
        'max_workers': 1
    }
    
    # Check if real API key is available
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        print("   Using real OpenAI API")
    else:
        print("   Using mock LLM (set OPENAI_API_KEY for real API)")
        project_config['prompt_only'] = True  # Use mock mode
    
    # Create and use the service
    service = TestGenerationService()
    results = service.generate_tests_with_config(
        functions_with_context,
        project_config
    )
    
    # Step 5: Show results
    print("\n5. Generation Results:")
    print("-" * 40)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"   Successful: {len(successful)} tests")
    print(f"   Failed: {len(failed)} tests")
    
    if successful:
        print("\n   Generated test files:")
        for result in successful:
            output_path = result.get('output_path', 'unknown')
            test_length = result.get('test_length', len(result.get('test_code', '')))
            print(f"     - {output_path} ({test_length} chars)")
    
    if failed:
        print("\n   Failures:")
        for result in failed:
            function_name = result.get('function_name', 'unknown')
            error = result.get('error', 'Unknown error')
            print(f"     - {function_name}: {error}")
    
    # Show sample of generated tests
    if successful:
        print("\n6. Sample Generated Test:")
        print("-" * 40)
        
        sample = successful[0]
        output_path = sample.get('output_path', 'unknown')
        function_name = sample.get('function_name', 'unknown')
        test_code = sample.get('test_code', '')
        
        print(f"File: {output_path}")
        print(f"Function: {function_name}")
        print("\nTest code preview:")
        print("=" * 50)
        
        test_code = sample['test_code']
        lines = test_code.split('\n')
        for line in lines[:15]:  # Show first 15 lines
            print(f"  {line}")
        
        if len(lines) > 15:
            print("  ...")
        
        print("=" * 50)
    
    print("\nDemo completed successfully!")
    
    if not api_key:
        print("\nTo use real OpenAI API, set your API key:")
        print("   export OPENAI_API_KEY=your_api_key_here")
        print("   Then run this demo again for real AI-generated tests!")


def main():
    """Run the complete workflow demo"""
    try:
        demo_complete_workflow()
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()