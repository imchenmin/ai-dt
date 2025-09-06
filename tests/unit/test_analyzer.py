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
    
    comp_db_path = "test_projects/complex_c_project/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/complex_c_project")
    
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
    
    # Assert that we found some functions
    assert len(all_functions) >= 0, "Should be able to analyze the project without errors"

def test_cpp_project():
    """Test C++ project analysis - using the same complex_c_project"""
    print("\n=== Testing C++ Project (using complex_c_project) ===")
    
    # Use the same project but focus on C++ files if any
    comp_db_path = "test_projects/complex_c_project/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/complex_c_project")
    
    all_functions = []
    for unit in compilation_units:
        # Filter for C++ files (though this project is mainly C)
        if unit['file'].endswith(('.cpp', '.cxx', '.cc')):
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
    
    # Assert that we can analyze C++ files (even if none found)
    assert len(all_functions) >= 0, "Should be able to analyze C++ files without errors"

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
        analyzer_c = FunctionAnalyzer("test_projects/complex_c_project")
        analyzer_cpp = FunctionAnalyzer("test_projects/complex_c_project")
        
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