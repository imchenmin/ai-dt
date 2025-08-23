#!/usr/bin/env python3
"""
Test script to verify macro extraction functionality
"""

import sys
import os
from pathlib import Path

# Configure libclang first
import clang.cindex
clang.cindex.Config.set_library_file('/usr/lib/llvm-10/lib/libclang.so.1')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer.clang_analyzer import ClangAnalyzer

def test_macro_extraction():
    """Test macro extraction from test_macro.c"""
    print("=== Testing Macro Extraction ===")
    
    analyzer = ClangAnalyzer()
    
    # Test with our macro test file
    test_file = "test_macro.c"
    compile_args = ["-std=gnu11"]
    
    print(f"Analyzing {test_file}...")
    functions = analyzer.analyze_file(test_file, compile_args)
    
    print(f"Found {len(functions)} functions")
    
    # Test macro extraction for each function
    for func in functions:
        print(f"\n--- Function: {func['name']} ---")
        
        # Get dependencies including macros
        deps = analyzer.get_function_dependencies(
            func, test_file, compile_args
        )
        
        print(f"Called functions: {len(deps['called_functions'])}")
        print(f"Macros used: {deps['macros_used']}")
        print(f"Macro definitions found: {len(deps['macro_definitions'])}")
        
        # Print macro details
        for macro_def in deps['macro_definitions']:
            print(f"  Macro: {macro_def['name']}")
            print(f"    Definition: {macro_def['definition']}")
            print(f"    Location: {macro_def['location']}")
            print(f"    Function-like: {macro_def['is_function_like']}")
            print(f"    Has parameters: {macro_def['has_parameters']}")
            print()

def main():
    """Run macro extraction test"""
    try:
        test_macro_extraction()
    except Exception as e:
        print(f"Error during macro extraction test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()