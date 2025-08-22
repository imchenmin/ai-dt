#!/usr/bin/env python3
"""
Main entry point for AI-Driven Test Generator
"""

import argparse
import logging
from pathlib import Path

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="AI-Driven C/C++ Test Generator")
    parser.add_argument("-p", "--project", required=True, help="Project root directory")
    parser.add_argument("-o", "--output", default="./generated_tests", help="Output directory")
    parser.add_argument("--compile-commands", default="compile_commands.json", 
                       help="Path to compile_commands.json")
    
    args = parser.parse_args()
    
    # Parse compilation database
    comp_db_parser = CompilationDatabaseParser(args.compile_commands)
    compilation_units = comp_db_parser.parse()
    
    # Analyze functions
    function_analyzer = FunctionAnalyzer()
    testable_functions = []
    
    for unit in compilation_units:
        functions = function_analyzer.analyze_file(unit['file'], unit['arguments'])
        testable_functions.extend(functions)
    
    # Generate tests
    test_generator = TestGenerator()
    for function in testable_functions:
        test_code = test_generator.generate_test(function)
        
        # Save generated test
        output_path = Path(args.output) / f"test_{function['name']}.cpp"
        output_path.write_text(test_code)
        logger.info(f"Generated test for {function['name']} at {output_path}")


if __name__ == "__main__":
    main()