#!/usr/bin/env python3
"""
Generate tests for complex project using DeepSeek API
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.libclang_config import ensure_libclang_configured
from src.utils.config_loader import ConfigLoader

def generate_complex_tests_with_deepseek():
    """Generate tests for complex project using DeepSeek"""
    print("🔍 Generating Tests for Complex Project with DeepSeek")
    print("=" * 60)
    
    # Configure libclang
    ensure_libclang_configured()
    
    # Check DeepSeek API key
    api_key = ConfigLoader.get_api_key("deepseek")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment variables.")
        print("Please set your DeepSeek API key:")
        print("export DEEPSEEK_API_KEY=your_deepseek_api_key_here")
        return []
    
    project_root = "test_projects/complex_example"
    comp_db_path = f"{project_root}/compile_commands.json"
    
    # Parse compilation database
    print("1. Parsing compilation database...")
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Analyze custom functions
    print("2. Analyzing custom functions...")
    analyzer = FunctionAnalyzer(project_root)
    
    custom_functions_with_context = []
    
    for unit in compilation_units:
        file_path = unit['file']
        print(f"   Analyzing {file_path}")
        
        functions = analyzer.analyze_file(file_path, unit['arguments'])
        
        for func in functions:
            function_name = func.get('name', '')
            
            # Only analyze our specific custom functions from the complex project
            custom_function_names = [
                # From advanced_math.h
                'calculateCircleArea', 'calculateSphereVolume', 
                'allocateDoubleArray', 'freeDoubleArray',
                'getLastMathError', 'clearMathError',
                # Complex number operations
                'operator+', 'operator-', 'operator*', 'operator/',
                'magnitude', 'conjugate',
                # From main.cpp (demonstration functions)
                'demonstrateVectorMath', 'demonstrateStatistics',
                'demonstrateComplexNumbers', 'demonstrateGeometry',
                'demonstrateMemoryManagement'
            ]
            
            if function_name in custom_function_names:
                # Get complete context
                context = analyzer._analyze_function_context(
                    func, unit['arguments'], compilation_units
                )
                
                custom_functions_with_context.append({
                    'function': func,
                    'context': context
                })
                
                print(f"     ✓ {func['name']}: {func['return_type']} function "
                      f"with {len(func['parameters'])} parameters")
    
    print(f"\n3. Found {len(custom_functions_with_context)} custom functions:")
    for func_data in custom_functions_with_context:
        func = func_data['function']
        print(f"   • {func['name']} ({func['return_type']})")
    
    # Generate tests with DeepSeek
    print(f"\n4. Generating tests with DeepSeek...")
    test_generator = TestGenerator(
        llm_provider="deepseek",
        api_key=api_key,
        model="deepseek-coder"  # Use coder model for better code generation
    )
    
    output_dir = "./generated_tests_complex_deepseek"
    
    print(f"Using output directory: {output_dir}")
    print(f"Generating tests for {len(custom_functions_with_context)} functions...")
    
    results = test_generator.generate_tests(
        custom_functions_with_context,
        output_dir=output_dir
    )
    
    # Print results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n📊 Generation Results:")
    print(f"   Successful: {len(successful)}")
    print(f"   Failed: {len(failed)}")
    
    if successful:
        print(f"\n✅ Successful Tests:")
        for result in successful:
            print(f"   • {result['function_name']}")
            print(f"     Length: {result.get('test_length', 0)} chars")
            print(f"     Output: {result.get('output_path', 'unknown')}")
            
            # Show test preview
            if 'test_code' in result and result['test_code']:
                lines = result['test_code'].split('\n')
                print(f"     Preview: {lines[0][:50]}..." if lines else "     Preview: (empty)")
    
    if failed:
        print(f"\n❌ Failed Tests:")
        for result in failed:
            print(f"   • {result['function_name']}: {result.get('error', 'Unknown error')}")
    
    return results

def main():
    """Main function"""
    try:
        results = generate_complex_tests_with_deepseek()
        
        if results:
            print(f"\n🎉 Test generation completed!")
            print(f"   Total functions processed: {len(results)}")
            
            # Show some example test content
            successful = [r for r in results if r['success']]
            if successful:
                print(f"\n📋 Example test files generated in: generated_tests_complex_deepseek/")
                
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)