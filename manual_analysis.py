#!/usr/bin/env python3
"""
Manual analysis of complex project functions
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


def analyze_specific_functions():
    """Analyze specific functions from our complex project"""
    print("🔍 Analyzing Specific Functions from Complex Project")
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
    
    # Analyze specific files
    print("2. Analyzing specific files for our custom functions...")
    analyzer = FunctionAnalyzer(project_root)
    
    # We know our custom functions are in advanced_math.cpp
    target_files = [
        "advanced_math.cpp",
        "main.cpp"  # For demonstration functions
    ]
    
    functions_with_context = []
    
    for unit in compilation_units:
        file_path = unit['file']
        filename = os.path.basename(file_path)
        
        if filename in target_files:
            print(f"   Analyzing {filename}")
            
            functions = analyzer.analyze_file(file_path, unit['arguments'])
            
            # Filter for our custom functions
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
            
            for func in functions:
                if func['name'] in custom_function_names:
                    # Get complete context
                    context = analyzer._analyze_function_context(
                        func, unit['arguments'], compilation_units
                    )
                    
                    functions_with_context.append({
                        'function': func,
                        'context': context
                    })
                    
                    print(f"     ✓ {func['name']}: {func['return_type']} function "
                          f"with {len(func['parameters'])} parameters")
                    print(f"       File: {func['file']}:{func['line']}")
                    print(f"       Language: {func.get('language', 'unknown')}")
    
    print(f"\n3. Found {len(functions_with_context)} custom functions:")
    for func_data in functions_with_context:
        func = func_data['function']
        context = func_data['context']
        
        print(f"   • {func['name']}")
        print(f"     Return: {func['return_type']}")
        print(f"     Parameters: {len(func['parameters'])}")
        print(f"     Location: {func['file']}:{func['line']}")
        print(f"     Called functions: {len(context.get('called_functions', []))}")
        print(f"     Call sites: {len(context.get('call_sites', []))}")
        print()
    
    return functions_with_context


def generate_tests(functions_with_context):
    """Generate tests for the custom functions"""
    print(f"\n🧪 Generating Tests")
    print("=" * 50)
    
    if not functions_with_context:
        print("❌ No functions found to test!")
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
        # Analyze specific functions
        functions = analyze_specific_functions()
        
        if not functions:
            print("\n❌ No custom functions found!")
            print("Please check if the complex project contains the expected functions.")
            return False
        
        # Generate tests
        results = generate_tests(functions)
        
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