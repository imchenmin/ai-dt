#!/usr/bin/env python3
"""
Generate test for calculateSphereVolume function using DeepSeek API
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

def generate_sphere_volume_test_with_deepseek():
    """Generate test for calculateSphereVolume function using DeepSeek"""
    print("🔍 Generating Test for calculateSphereVolume with DeepSeek")
    print("=" * 65)
    
    # Configure libclang
    ensure_libclang_configured()
    
    # Check DeepSeek API key
    api_key = ConfigLoader.get_api_key("deepseek")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment variables.")
        print("Please set your DeepSeek API key:")
        print("export DEEPSEEK_API_KEY=your_deepseek_api_key_here")
        return None
    
    project_root = "test_projects/complex_example"
    comp_db_path = f"{project_root}/compile_commands.json"
    
    # Parse compilation database
    print("1. Parsing compilation database...")
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Find the calculateSphereVolume function
    print("2. Finding calculateSphereVolume function...")
    analyzer = FunctionAnalyzer(project_root)
    
    target_function = None
    context = None
    
    for unit in compilation_units:
        if 'advanced_math.cpp' in unit['file']:
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            
            for func in functions:
                if func['name'] == 'calculateSphereVolume':
                    target_function = func
                    # Get complete context
                    context = analyzer._analyze_function_context(
                        func, unit['arguments'], compilation_units
                    )
                    break
            
            if target_function:
                break
    
    if not target_function:
        print("❌ calculateSphereVolume function not found!")
        return None
    
    print(f"   ✓ Found function: {target_function['name']}")
    print(f"   Return type: {target_function['return_type']}")
    print(f"   Parameters: {len(target_function['parameters'])}")
    
    # Generate test with DeepSeek
    print(f"\n3. Generating test with DeepSeek...")
    test_generator = TestGenerator(
        llm_provider="deepseek",
        api_key=api_key,
        model="deepseek-coder"
    )
    
    result = test_generator.generate_test(target_function, context)
    
    if result['success']:
        print(f"   ✅ Successfully generated test!")
        print(f"   Tokens used: {result.get('usage', {})}")
        print(f"   Test length: {len(result['test_code'])} characters")
        
        # Save the test
        output_dir = "./generated_tests_complex_deepseek"
        output_path = test_generator.llm_client.save_test_code(
            result['test_code'],
            target_function['name'],
            output_dir
        )
        print(f"   Saved to: {output_path}")
        
        # Show the generated test
        print(f"\n📋 Generated Test Code:")
        print("=" * 50)
        print(result['test_code'])
        
        return result
    else:
        print(f"   ❌ Failed to generate test: {result['error']}")
        return None

def main():
    """Main function"""
    try:
        result = generate_sphere_volume_test_with_deepseek()
        
        if result:
            print(f"\n🎉 Test generation completed successfully!")
            return True
        else:
            print(f"\n❌ Test generation failed!")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)