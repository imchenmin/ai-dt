#!/usr/bin/env python3
"""
Batch test generation script for complex C project
Generates tests in smaller batches to avoid timeouts
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.context_compressor import ContextCompressor
from src.utils.libclang_config import ensure_libclang_configured

def batch_generate_tests():
    """Generate tests in batches for complex C project"""
    print("Batch Test Generation for Complex C Project")
    print("=" * 50)
    
    ensure_libclang_configured()
    
    # Parse compilation database
    print("\n1. Parsing compile_commands.json...")
    comp_db_path = "test_projects/complex_c_project/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Analyze functions
    print("\n2. Analyzing source code for testable functions...")
    analyzer = FunctionAnalyzer("test_projects/complex_c_project")
    
    functions_with_context = []
    for unit in compilation_units:
        functions = analyzer.analyze_file(unit['file'], unit['arguments'])
        
        for func in functions:
            # Skip main function, internal helpers, and standard library functions
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
    
    print(f"\n   Total testable functions: {len(functions_with_context)}")
    
    # Setup LLM generator
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if api_key:
        print("\n3. Using DeepSeek LLM with real API")
        generator = TestGenerator(llm_provider="deepseek", api_key=api_key, model="deepseek-coder")
    else:
        print("\n3. Using mock LLM (set DEEPSEEK_API_KEY for real API)")
        generator = TestGenerator()
    
    # Generate tests in batches
    output_dir = "generated_tests_complex_c"
    os.makedirs(output_dir, exist_ok=True)
    
    batch_size = 5
    total_batches = (len(functions_with_context) + batch_size - 1) // batch_size
    
    print(f"\n4. Generating tests in {total_batches} batches of {batch_size} functions...")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(functions_with_context))
        batch = functions_with_context[start_idx:end_idx]
        
        print(f"\n   Batch {batch_num + 1}/{total_batches}: Functions {start_idx + 1}-{end_idx}")
        print("   " + "-" * 40)
        
        for item in batch:
            func = item['function']
            context = item['context']
            
            print(f"   Generating test for: {func['name']}")
            
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
            test_filename = f"test_{func['name']}.cpp"
            test_filepath = os.path.join(output_dir, test_filename)
            
            with open(test_filepath, 'w') as f:
                f.write(test_code)
            
            print(f"     Saved: {test_filename} ({len(test_code)} chars)")
            
            # Add delay between generations to avoid rate limiting
            time.sleep(2)
        
        print(f"   Batch {batch_num + 1} completed")
        
        # Add longer delay between batches
        if batch_num < total_batches - 1:
            print(f"   Waiting 10 seconds before next batch...")
            time.sleep(10)
    
    print(f"\n5. Generation completed!")
    print(f"   Generated tests saved in: {output_dir}")
    print(f"   Total functions processed: {len(functions_with_context)}")
    
    # Show summary
    generated_files = [f for f in os.listdir(output_dir) if f.startswith('test_') and f.endswith('.cpp')]
    print(f"   Total test files generated: {len(generated_files)}")
    
    if generated_files:
        print("\n   Generated test files:")
        for i, filename in enumerate(generated_files[:10], 1):
            print(f"     {i}. {filename}")
        if len(generated_files) > 10:
            print(f"     ... and {len(generated_files) - 10} more")

if __name__ == "__main__":
    batch_generate_tests()