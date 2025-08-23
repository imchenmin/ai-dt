#!/usr/bin/env python3
"""
Test script to demonstrate context extraction for LLM test generation
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
from src.utils.context_compressor import ContextCompressor

def test_context_extraction():
    """Test context extraction for LLM test generation"""
    print("=== Testing Context Extraction for LLM ===")
    
    # Test with C project
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/c")
    compressor = ContextCompressor()
    
    print("\n--- Analyzing C Functions ---")
    for unit in compilation_units:
        if 'math_utils.c' in unit['file']:
            print(f"\nAnalyzing {unit['file']}:")
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                # Get full context
                func['context'] = analyzer._analyze_function_context(
                    func, unit['arguments'], compilation_units
                )
                
                print(f"\nFunction: {func['name']}")
                print(f"Testable: {analyzer._is_testable_function(func)}")
                
                # Compress context for LLM
                compressed = compressor.compress_function_context(func, func['context'])
                
                print("\nCompressed Context:")
                print(f"- Called functions: {len(compressed['dependencies']['called_functions'])}")
                print(f"- Macros used: {compressed['dependencies']['macros']}")
                print(f"- Data structures: {compressed['dependencies']['data_structures']}")
                print(f"- Call sites: {len(compressed['usage_patterns'])}")
                
                # Generate LLM prompt
                llm_prompt = compressor.format_for_llm_prompt(compressed)
                print(f"\nLLM Prompt Length: {len(llm_prompt)} characters")
                print("\nFirst 500 chars of prompt:")
                print(llm_prompt[:500] + "..." if len(llm_prompt) > 500 else llm_prompt)


def test_specific_function():
    """Test context extraction for a specific function"""
    print("\n=== Testing Specific Function ===")
    
    comp_db_path = "test_projects/c/compile_commands.json"
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    
    analyzer = FunctionAnalyzer("test_projects/c")
    compressor = ContextCompressor()
    
    # Find the 'divide' function specifically
    for unit in compilation_units:
        if 'math_utils.c' in unit['file']:
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                if func['name'] == 'divide':
                    print(f"\nFound target function: {func['name']}")
                    
                    # Get full context
                    func['context'] = analyzer._analyze_function_context(
                        func, unit['arguments'], compilation_units
                    )
                    
                    # Compress context for LLM
                    compressed = compressor.compress_function_context(func, func['context'])
                    
                    # Generate complete LLM prompt
                    llm_prompt = compressor.format_for_llm_prompt(compressed)
                    
                    print(f"\nComplete LLM Prompt for '{func['name']}':")
                    print("=" * 50)
                    print(llm_prompt)
                    print("=" * 50)
                    
                    return


def main():
    """Run context extraction tests"""
    try:
        test_context_extraction()
        test_specific_function()
        
    except Exception as e:
        print(f"Error during context extraction testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()