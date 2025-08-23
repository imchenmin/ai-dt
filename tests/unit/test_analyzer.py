#!/usr/bin/env python3
"""
Test script to verify the analyzer functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure libclang using unified configuration
from src.utils.libclang_config import ensure_libclang_configured
ensure_libclang_configured()

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer

def test_c_project():
    """Test C project analysis"""
    print("=== Testing C Project ===")
    
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/c")
    
    all_functions = []
    for unit in compilation_units:
        print(f"\nAnalyzing {unit['file']}:")
        functions = analyzer.analyze_file(unit['file'], unit['arguments'])
        
        for func in functions:
            func['context'] = analyzer._analyze_function_context(
                func, unit['arguments'], compilation_units
            )
            all_functions.append(func)
            
            print(f"  Function: {func['name']}")
            print(f"    Return: {func['return_type']}")
            print(f"    Params: {len(func['parameters'])}")
            print(f"    Static: {func['is_static']}")
            print(f"    Function body: {func['body']}")
            print(f"    Testable: {analyzer._is_testable_function(func)}")
            print(f"    Call sites: {len(func['context']['call_sites'])}")
    
    return all_functions

def test_cpp_project():
    """Test C++ project analysis"""
    print("\n=== Testing C++ Project ===")
    
    comp_db_path = "test_projects/cpp/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/cpp")
    
    all_functions = []
    for unit in compilation_units:
        print(f"\nAnalyzing {unit['file']}:")
        functions = analyzer.analyze_file(unit['file'], unit['arguments'])
        
        for func in functions:
            func['context'] = analyzer._analyze_function_context(
                func, unit['arguments'], compilation_units
            )
            all_functions.append(func)
            
            print(f"  Function: {func['name']}")
            print(f"    Return: {func['return_type']}")
            print(f"    Params: {len(func['parameters'])}")
            print(f"    Static: {func['is_static']}")
            print(f"    Access: {func.get('access_specifier', 'N/A')}")
            print(f"    Testable: {analyzer._is_testable_function(func)}")
            print(f"    Call sites: {len(func['context']['call_sites'])}")
    
    return all_functions

def main():
    """Run all tests"""
    print("Testing AI-Driven Test Generator Analyzer")
    print("=" * 50)
    
    try:
        c_functions = test_c_project()
        cpp_functions = test_cpp_project()
        
        print(f"\n=== Summary ===")
        print(f"C functions found: {len(c_functions)}")
        print(f"C++ functions found: {len(cpp_functions)}")
        
        # Count testable functions
        analyzer_c = FunctionAnalyzer("test_projects/c")
        analyzer_cpp = FunctionAnalyzer("test_projects/cpp")
        
        c_testable = sum(1 for f in c_functions 
                       if analyzer_c._is_testable_function(f))
        cpp_testable = sum(1 for f in cpp_functions 
                         if analyzer_cpp._is_testable_function(f))
        
        print(f"Testable C functions: {c_testable}")
        print(f"Testable C++ functions: {cpp_testable}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()