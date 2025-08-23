#!/usr/bin/env python3
"""
Simple wrapper script for common test generation scenarios
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def generate_simple_tests():
    """Generate tests for simple C project"""
    print("🧪 Generating tests for simple C project...")
    os.system("python generate_tests.py simple_c")


def generate_complex_tests():
    """Generate tests for complex C++ project"""
    print("🧪 Generating tests for complex C++ project...")
    os.system("python generate_tests.py complex_example")


def generate_specific_function(project_name: str, function_name: str):
    """Generate test for a specific function"""
    print(f"🧪 Generating test for {function_name} in {project_name}...")
    # This would require modifying the config temporarily
    print("Feature coming soon!")


def show_help():
    """Show help information"""
    print("""
Test Generation Script
=====================

Usage:
  python run_test_generation.py [command]

Commands:
  simple      Generate tests for simple C project
  complex     Generate tests for complex C++ project  
  help        Show this help message

Examples:
  python run_test_generation.py simple
  python run_test_generation.py complex
""")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return False
    
    command = sys.argv[1].lower()
    
    if command == "simple":
        generate_simple_tests()
    elif command == "complex":
        generate_complex_tests()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)