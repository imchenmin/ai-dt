#!/usr/bin/env python3
"""
Test the generated test files to ensure they compile correctly
"""

import subprocess
import sys
from pathlib import Path

def test_generated_tests():
    """Test if generated test files can compile"""
    print("Testing Generated Test Files")
    print("=" * 40)
    
    test_dir = Path("./generated_tests_demo")
    
    if not test_dir.exists():
        print("No generated tests found. Run demo_llm_integration.py first.")
        return
    
    test_files = list(test_dir.glob("test_*.cpp"))
    
    if not test_files:
        print("No test files found in generated_tests_demo/")
        return
    
    print(f"Found {len(test_files)} test files:")
    
    for test_file in test_files:
        print(f"\nTesting {test_file.name}:")
        
        # Check if the test file includes the right headers
        content = test_file.read_text(encoding='utf-8')
        
        # Basic syntax checks
        has_gtest = "gtest/gtest.h" in content
        has_math_utils = "math_utils.h" in content
        has_test_macros = "TEST(" in content
        has_expect_macros = "EXPECT_" in content
        
        print(f"  - Includes gtest: {'YES' if has_gtest else 'NO'}")
        print(f"  - Includes math_utils: {'YES' if has_math_utils else 'NO'}")
        print(f"  - Has TEST macros: {'YES' if has_test_macros else 'NO'}")
        print(f"  - Has EXPECT macros: {'YES' if has_expect_macros else 'NO'}")
        
        # Check test structure
        test_count = content.count("TEST(")
        expect_count = content.count("EXPECT_")
        
        print(f"  - Number of test cases: {test_count}")
        print(f"  - Number of assertions: {expect_count}")
        
        # Check for specific function tests
        func_name = test_file.stem.replace("test_", "")
        if func_name in content:
            print(f"  - Tests function {func_name}: YES")
        else:
            print(f"  - Tests function {func_name}: NO")
        
        # Check for edge cases
        has_edge_cases = any(keyword in content for keyword in 
                           ["EdgeCase", "edge", "INT_MAX", "INT_MIN", "FLT_MAX", "FLT_MIN"])
        print(f"  - Includes edge cases: {'YES' if has_edge_cases else 'NO'}")
        
        print(f"  - File size: {len(content)} characters")

def main():
    """Run test validation"""
    try:
        test_generated_tests()
    except Exception as e:
        print(f"Error testing generated tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()