#!/usr/bin/env python3
"""
Test context compression with macro integration
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
from src.utils.context_compressor import ContextCompressor

def test_context_with_macros():
    """Test context compression with macro information"""
    print("=== Testing Context Compression with Macros ===")
    
    analyzer = ClangAnalyzer()
    compressor = ContextCompressor()
    
    # Test with our macro test file
    test_file = "test_macro.c"
    compile_args = ["-std=gnu11"]
    
    print(f"Analyzing {test_file}...")
    functions = analyzer.analyze_file(test_file, compile_args)
    
    print(f"Found {len(functions)} functions")
    
    for func in functions:
        print(f"\n--- Function: {func['name']} ---")
        
        # Get dependencies including macros
        deps = {
            'called_functions': [],
            'macros_used': ['MAX_VALUE', 'SQUARE'],  # Simulate used macros
            'macro_definitions': [],
            'data_structures': [],
            'include_directives': []
        }
        
        # Get actual macro definitions
        macro_names = ['MAX_VALUE', 'SQUARE']
        print(f"Looking for macros: {macro_names}")
        full_macro_defs = analyzer._get_macro_definitions(macro_names, test_file, compile_args)
        print(f"Found macro definitions: {len(full_macro_defs)}")
        for macro_def in full_macro_defs:
            print(f"  - {macro_def['name']}: {macro_def['definition']}")
        deps['macro_definitions'] = full_macro_defs
        
        print(f"Used macros: {deps['macros_used']}")
        print(f"Macro definitions found: {len(deps['macro_definitions'])}")
        
        # Create mock context
        context = {
            'called_functions': deps['called_functions'],
            'macros_used': deps['macros_used'],
            'macro_definitions': deps['macro_definitions'],
            'data_structures': deps['data_structures'],
            'include_directives': deps['include_directives'],
            'call_sites': [],
            'compilation_flags': compile_args
        }
        
        # Compress context for LLM
        compressed = compressor.compress_function_context(func, context)
        
        print(f"Compressed context keys: {list(compressed.keys())}")
        print(f"Macros in compressed context: {compressed['dependencies']['macros']}")
        print(f"Macro definitions in compressed context: {len(compressed['dependencies']['macro_definitions'])}")
        
        # Generate LLM prompt
        llm_prompt = compressor.format_for_llm_prompt(compressed)
        
        print(f"\n=== LLM Prompt (first 500 chars) ===")
        print(llm_prompt[:500])
        
        # Check if macro definitions are included
        if "宏定义详情" in llm_prompt:
            print("\n✅ Macro definitions section found in prompt!")
        
        if any(macro['name'] in llm_prompt for macro in deps['macro_definitions']):
            print("✅ Macro names found in prompt!")
        
        if any(macro['definition'] in llm_prompt for macro in deps['macro_definitions']):
            print("✅ Macro definitions found in prompt!")

def main():
    """Run context compression test"""
    try:
        test_context_with_macros()
    except Exception as e:
        print(f"Error during context compression test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()