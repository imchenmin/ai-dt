#!/usr/bin/env python3
"""
Analyze the complex test project and generate tests
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


def analyze_complex_project():
    """Analyze the complex test project"""
    print("🔍 Analyzing Complex Test Project")
    print("=" * 50)
    
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
    print("2. Analyzing functions...")
    analyzer = FunctionAnalyzer(project_root)
    
    functions_with_context = []
    for unit in compilation_units:
        print(f"   Analyzing {unit['file']}")
        functions = analyzer.analyze_file(unit['file'], unit['arguments'])
        
        for func in functions:
            # Get complete context
            context = analyzer._analyze_function_context(
                func, unit['arguments'], compilation_units
            )
            
            functions_with_context.append({
                'function': func,
                'context': context
            })
            
            print(f"     - {func['name']}: {func['return_type']} function "
                  f"with {len(func['parameters'])} parameters")
            print(f"       Language: {func.get('language', 'unknown')}")
            print(f"       Static: {func.get('is_static', False)}")
            print(f"       Access: {func.get('access_specifier', 'unknown')}")
    
    print(f"\n3. Found {len(functions_with_context)} testable functions:")
    for func_data in functions_with_context:
        func = func_data['function']
        context = func_data['context']
        
        print(f"   • {func['name']}")
        print(f"     Return: {func['return_type']}")
        print(f"     Parameters: {len(func['parameters'])}")
        print(f"     Called functions: {len(context.get('called_functions', []))}")
        print(f"     Call sites: {len(context.get('call_sites', []))}")
        print(f"     Macros used: {len(context.get('macros_used', []))}")
    
    return functions_with_context


def generate_tests_for_complex_project(functions_with_context):
    """Generate tests for the complex project"""
    print(f"\n🧪 Generating Tests for Complex Project")
    print("=" * 50)
    
    # Generate tests
    test_generator = TestGenerator(llm_provider="mock")
    output_dir = "./generated_tests_complex"
    
    print(f"Using output directory: {output_dir}")
    
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
        # Analyze the complex project
        functions_with_context = analyze_complex_project()
        
        # Generate tests
        results = generate_tests_for_complex_project(functions_with_context)
        
        print(f"\n🎉 Analysis and test generation completed!")
        print(f"   Total functions processed: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)