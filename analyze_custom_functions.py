#!/usr/bin/env python3
"""
Analyze only custom functions in the complex test project
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.libclang_config import ensure_libclang_configured


def is_custom_function(function_info):
    """Check if function is a custom function (not from standard library)"""
    file_path = function_info.get('file', '')
    function_name = function_info.get('name', '')
    
    # Skip standard library functions
    if any(path in file_path for path in ['/usr/include', '/usr/lib', '/include/c++']):
        return False
    
    # Skip compiler builtins and internal functions
    if function_name.startswith('__') or function_name.startswith('_'):
        return False
    
    # Skip operators and special functions
    if function_name.startswith('operator') or function_name in ['main', 'malloc', 'free']:
        return False
    
    return True


def analyze_custom_functions():
    """Analyze only custom functions in the complex project"""
    print("🔍 Analyzing Custom Functions in Complex Project")
    print("=" * 60)
    
    # Configure libclang
    ensure_libclang_configured()
    
    project_root = "test_projects/complex_example"
    comp_db_path = f"{project_root}/compile_commands.json"
    
    # Parse compilation database
    print("1. Parsing compilation database...")
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Analyze functions
    print("2. Analyzing custom functions...")
    analyzer = FunctionAnalyzer(project_root)
    
    custom_functions_with_context = []
    
    for unit in compilation_units:
        file_path = unit['file']
        print(f"   Analyzing {file_path}")
        
        functions = analyzer.analyze_file(file_path, unit['arguments'])
        
        for func in functions:
            if is_custom_function(func):
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
                print(f"       File: {func['file']}:{func['line']}")
                print(f"       Language: {func.get('language', 'unknown')}")
                print(f"       Static: {func.get('is_static', False)}")
    
    print(f"\n3. Found {len(custom_functions_with_context)} custom functions:")
    for func_data in custom_functions_with_context:
        func = func_data['function']
        context = func_data['context']
        
        print(f"   • {func['name']}")
        print(f"     Return: {func['return_type']}")
        print(f"     Parameters: {len(func['parameters'])}")
        print(f"     Location: {func['file']}:{func['line']}")
        print(f"     Called functions: {len(context.get('called_functions', []))}")
        print(f"     Call sites: {len(context.get('call_sites', []))}")
        print(f"     Macros used: {len(context.get('macros_used', []))}")
        print()
    
    return custom_functions_with_context


def generate_tests_for_custom_functions(functions_with_context):
    """Generate tests for custom functions"""
    print(f"\n🧪 Generating Tests for Custom Functions")
    print("=" * 50)
    
    if not functions_with_context:
        print("❌ No custom functions found to test!")
        return []
    
    # Generate tests
    test_generator = TestGenerator(llm_provider="mock")
    output_dir = "./generated_tests_complex"
    
    print(f"Using output directory: {output_dir}")
    print(f"Generating tests for {len(functions_with_context)} functions...")
    
    results = test_generator.generate_tests(
        functions_with_context,
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
    
    if failed:
        print(f"\n❌ Failed Tests:")
        for result in failed:
            print(f"   • {result['function_name']}: {result.get('error', 'Unknown error')}")
    
    return results


def main():
    """Main function"""
    try:
        # Analyze custom functions
        custom_functions = analyze_custom_functions()
        
        if not custom_functions:
            print("\n❌ No custom functions found!")
            print("Please check if the complex project was built correctly.")
            return False
        
        # Generate tests
        results = generate_tests_for_custom_functions(custom_functions)
        
        print(f"\n🎉 Analysis and test generation completed!")
        print(f"   Total custom functions processed: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)