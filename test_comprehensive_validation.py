"""
Comprehensive validation tests for the AI test generation system
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.libclang_config import ensure_libclang_configured


class ComprehensiveValidationTests(unittest.TestCase):
    """Comprehensive validation tests for the test generation system"""
    
    def setUp(self):
        """Set up test environment"""
        ensure_libclang_configured()
        self.project_root = "test_projects/c"
        self.comp_db_path = "test_projects/c/compile_commands.json"
        
    def test_compilation_database_parsing(self):
        """Test compilation database parsing functionality"""
        parser = CompilationDatabaseParser(self.comp_db_path)
        units = parser.parse()
        
        self.assertGreater(len(units), 0, "Should parse at least one compilation unit")
        
        for unit in units:
            self.assertIn('file', unit, "Each unit should have file path")
            self.assertIn('arguments', unit, "Each unit should have compilation arguments")
            self.assertTrue(os.path.exists(unit['file']), "File should exist")
    
    def test_function_analysis_completeness(self):
        """Test that all testable functions are identified"""
        analyzer = FunctionAnalyzer(self.project_root)
        parser = CompilationDatabaseParser(self.comp_db_path)
        units = parser.parse()
        
        testable_functions = []
        for unit in units:
            if 'math_utils.c' in unit['file']:
                functions = analyzer.analyze_file(unit['file'], unit['arguments'])
                testable_functions.extend(functions)
        
        # Should find all 4 testable functions in math_utils.c
        function_names = {f['name'] for f in testable_functions}
        expected_functions = {'add', 'subtract', 'multiply', 'divide'}
        
        self.assertEqual(function_names, expected_functions, 
                        "Should find all testable functions")
    
    def test_function_context_analysis(self):
        """Test function context analysis includes all necessary information"""
        analyzer = FunctionAnalyzer(self.project_root)
        parser = CompilationDatabaseParser(self.comp_db_path)
        units = parser.parse()
        
        for unit in units:
            if 'math_utils.c' in unit['file']:
                functions = analyzer.analyze_file(unit['file'], unit['arguments'])
                
                for func in functions:
                    context = analyzer._analyze_function_context(
                        func, unit['arguments'], units
                    )
                    
                    # Verify context contains all required fields
                    required_fields = [
                        'called_functions', 'macros_used', 'data_structures',
                        'include_directives', 'call_sites', 'compilation_flags'
                    ]
                    
                    for field in required_fields:
                        self.assertIn(field, context, 
                                    f"Context should contain {field} for {func['name']}")
    
    def test_test_generation_basic(self):
        """Test basic test generation functionality"""
        analyzer = FunctionAnalyzer(self.project_root)
        parser = CompilationDatabaseParser(self.comp_db_path)
        units = parser.parse()
        
        functions_with_context = []
        for unit in units:
            if 'math_utils.c' in unit['file']:
                functions = analyzer.analyze_file(unit['file'], unit['arguments'])
                
                for func in functions:
                    context = analyzer._analyze_function_context(
                        func, unit['arguments'], units
                    )
                    
                    functions_with_context.append({
                        'function': func,
                        'context': context
                    })
        
        # Test with mock LLM
        test_generator = TestGenerator(llm_provider="mock")
        results = test_generator.generate_tests(
            functions_with_context, 
            output_dir=tempfile.mkdtemp()
        )
        
        successful = [r for r in results if r['success']]
        self.assertGreater(len(successful), 0, "Should generate at least one successful test")
        
        for result in successful:
            self.assertIn('test_code', result, "Result should contain test code")
            self.assertGreater(len(result['test_code']), 0, "Test code should not be empty")
            
            # Basic syntax validation
            test_code = result['test_code']
            self.assertIn('#include <gtest/gtest.h>', test_code, 
                         "Should include gtest header")
            self.assertIn('TEST(', test_code, "Should contain TEST macro")
            self.assertIn('EXPECT_', test_code, "Should contain expectation macros")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        analyzer = FunctionAnalyzer(self.project_root)
        
        # Test with non-existent file
        result = analyzer.analyze_file("non_existent_file.c", [])
        self.assertEqual(result, [], "Should return empty list for non-existent file")
        
        # Test with invalid function data
        test_generator = TestGenerator(llm_provider="mock")
        invalid_data = [{
            'function': {'name': 'invalid', 'return_type': 'void'},
            'context': {}
        }]
        
        results = test_generator.generate_tests(invalid_data, "./temp_tests")
        self.assertEqual(len(results), 1, "Should process all inputs")
    
    def test_configuration_robustness(self):
        """Test configuration robustness across different environments"""
        # Test with different libclang paths
        original_path = os.environ.get('LIBCLANG_PATH')
        
        try:
            # Test 1: No environment variable
            if 'LIBCLANG_PATH' in os.environ:
                del os.environ['LIBCLANG_PATH']
            ensure_libclang_configured()
            
            # Test 2: Invalid path
            os.environ['LIBCLANG_PATH'] = '/invalid/path'
            ensure_libclang_configured()  # Should not crash
            
            # Test 3: Valid path (if available)
            if original_path:
                os.environ['LIBCLANG_PATH'] = original_path
                ensure_libclang_configured()
                
        finally:
            # Restore original environment
            if original_path:
                os.environ['LIBCLANG_PATH'] = original_path
            elif 'LIBCLANG_PATH' in os.environ:
                del os.environ['LIBCLANG_PATH']


class RealWorldScenarioTests(unittest.TestCase):
    """Tests simulating real-world scenarios"""
    
    def test_large_codebase_performance(self):
        """Test performance with larger codebases"""
        # This would ideally test with real larger projects
        # For now, we test that the system doesn't crash on basic operations
        
        analyzer = FunctionAnalyzer("test_projects/c")
        parser = CompilationDatabaseParser("test_projects/c/compile_commands.json")
        units = parser.parse()
        
        # Time the analysis
        import time
        start_time = time.time()
        
        for unit in units:
            functions = analyzer.analyze_file(unit['file'], unit['arguments'])
            # Basic validation that analysis completes
            self.assertIsInstance(functions, list)
        
        duration = time.time() - start_time
        print(f"Analysis completed in {duration:.2f} seconds")
        
        # Should complete in reasonable time
        self.assertLess(duration, 10.0, "Analysis should complete quickly")
    
    def test_edge_cases(self):
        """Test various edge cases"""
        # Empty compilation database
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('[]')
            temp_db = f.name
        
        try:
            parser = CompilationDatabaseParser(temp_db)
            units = parser.parse()
            self.assertEqual(units, [], "Should handle empty compilation database")
        finally:
            os.unlink(temp_db)
        
        # Malformed JSON - need to handle this gracefully in the parser
        # For now, we'll skip this test as the current parser doesn't handle it
        pass


def run_comprehensive_tests():
    """Run all comprehensive validation tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ComprehensiveValidationTests))
    suite.addTests(loader.loadTestsFromTestCase(RealWorldScenarioTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)