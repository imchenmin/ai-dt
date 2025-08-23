#!/usr/bin/env python3
"""
Demo script for complex C project test generation
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.context_compressor import ContextCompressor
from src.utils.libclang_config import ensure_libclang_configured

def demo_complex_c_workflow():
    """Demonstrate test generation for complex C project"""
    print("Complex C Project Test Generation - Complete Workflow")
    print("=" * 60)
    
    ensure_libclang_configured()
    
    # Step 1: Parse compilation database
    print("\n1. Parsing compile_commands.json...")
    comp_db_path = "test_projects/complex_c_project/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Step 2: Analyze functions
    print("\n2. Analyzing source code for testable functions...")
    analyzer = FunctionAnalyzer("test_projects/complex_c_project")
    
    functions_with_context = []
    for unit in compilation_units:
        functions = analyzer.analyze_file(unit['file'], unit['arguments'])
        
        for func in functions:
            # Skip main function, internal helpers, and standard library functions
            # Only include functions from our project files
            project_files = ['linked_list.c', 'hash_table.c', 'memory_pool.c', 'main.c']
            if (func['name'] == 'main' or 
                func['name'].startswith('_') or
                func['file'].startswith('/usr/') or
                not any(proj_file in func['file'] for proj_file in project_files) or
                any(std_func in func['name'] for std_func in ['printf', 'scanf', 'malloc', 'free', 'atoi', 'atol', 'atof', 'bsearch', 'getchar', 'putchar', 'feof', 'ferror', 'fgetc', 'fputc', 'getc', 'putc'])):
                continue
                
            # Get complete context
            context = analyzer._analyze_function_context(
                func, unit['arguments'], compilation_units
            )
            
            functions_with_context.append({
                'function': func,
                'context': context
            })
            
            print(f"   - {func['name']}: {func['return_type']} function with {len(func['parameters'])} parameters")
            if func.get('is_static', False):
                print(f"     (static function)")
    
    print(f"\n   Total testable functions: {len(functions_with_context)}")
    
    # Step 3: Prepare context for LLM
    print("\n3. Preparing context for LLM...")
    
    for item in functions_with_context:
        func = item['function']
        context = item['context']
        
        # Simple context size calculation
        context_size = len(str(context))
        call_sites = len(context.get('call_sites', []))
        print(f"   - {func['name']}: {context_size} chars context, {call_sites} call sites")
    
    # Step 4: Generate tests with LLM
    print("\n4. Generating tests with LLM...")
    
    # Use real DeepSeek LLM if API key is available
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if api_key:
        print("   Using DeepSeek LLM with real API")
        generator = TestGenerator(llm_provider="deepseek", api_key=api_key, model="deepseek-coder")
    else:
        print("   Using mock LLM (set DEEPSEEK_API_KEY for real API)")
        generator = TestGenerator()
    
    # Generate tests for ALL functions in the complex project
    for item in functions_with_context:
        func = item['function']
        context = item['context']
        
        print(f"DEBUG: Generating test for function: '{func['name']}'")
        
        # Generate test using LLM
        try:
            result = generator.generate_test(func, context)
            test_code = result.get('test_code', '')
            
            if not test_code:
                # Fallback to mock if generation fails
                test_code = f"// Mock test for {func['name']}\n"
                test_code += "#include <gtest/gtest.h>\n"
                test_code += f"#include \"{os.path.basename(func['file'])}\"\n\n"
                test_code += f"TEST({func['name'].capitalize()}Test, BasicFunctionality) {{\n"
                test_code += f"    // Test implementation for {func['name']}\n"
                test_code += "}\n"
        except Exception as e:
            print(f"     Error generating test: {e}")
            # Fallback to mock
            test_code = f"// Mock test for {func['name']}\n"
            test_code += "#include <gtest/gtest.h>\n"
            test_code += f"#include \"{os.path.basename(func['file'])}\"\n\n"
            test_code += f"TEST({func['name'].capitalize()}Test, BasicFunctionality) {{\n"
            test_code += f"    // Test implementation for {func['name']}\n"
            test_code += "}\n"
        
        # Save test file
        output_dir = "generated_tests_complex_c"
        os.makedirs(output_dir, exist_ok=True)
        
        test_filename = f"test_{func['name']}.cpp"
        test_filepath = os.path.join(output_dir, test_filename)
        
        with open(test_filepath, 'w') as f:
            f.write(test_code)
        
        print(f"     Generated: {test_filepath} ({len(test_code)} chars)")
    
    # Step 5: Show results
    print("\n5. Generation Results:")
    print("-" * 40)
    print(f"   Total functions processed: {len(functions_with_context)}")
    print(f"   Generated test files in: {output_dir}")
    
    # Step 6: Show sample
    print("\n6. Sample Generated Test:")
    print("-" * 40)
    if functions_with_context:
        sample_func = functions_with_context[0]['function']
        print(f"File: {output_dir}/test_{sample_func['name']}.cpp")
        print(f"Function: {sample_func['name']}")
        print("\nTest code preview:")
        print("=" * 50)
        
        sample_file = os.path.join(output_dir, f"test_{sample_func['name']}.cpp")
        if os.path.exists(sample_file):
            with open(sample_file, 'r') as f:
                content = f.read()
                print(content)
        else:
            print("  // Sample test code would be here")
        
        print("=" * 50)
    
    print("\nDemo completed successfully!")
    print("\nTo use real DeepSeek API, set your API key:")
    print("   export DEEPSEEK_API_KEY=your_api_key_here")
    print("   Then run this demo again for real AI-generated tests!")

if __name__ == "__main__":
    demo_complex_c_workflow()