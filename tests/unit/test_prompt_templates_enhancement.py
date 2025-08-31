"""Unit tests for PromptTemplates enhancement - existing test context format and test class structure logic"""

import pytest
from src.utils.prompt_templates import PromptTemplates


class TestPromptTemplatesEnhancement:
    """Test class for prompt templates enhancement features"""
    
    def setup_method(self):
        """Setup test data"""
        self.compressed_context = {
            'target_function': {
                'name': 'process_data',
                'signature': 'int process_data(int input)',
                'return_type': 'int',
                'parameters': [{'name': 'input', 'type': 'int'}],
                'body': 'int process_data(int input) { return input * 2; }',
                'location': '/path/to/utils.c:10',
                'language': 'c',
                'is_static': False,
                'access_specifier': 'public'
            },
            'dependencies': {
                'called_functions': [],
                'macros': [],
                'macro_definitions': [],
                'data_structures': [],
                'dependency_definitions': []
            },
            'compilation_info': {
                'include_paths': ['/usr/include'],
                'defines': ['DEBUG=1'],
                'compiler_flags': ['-std=c99']
            }
        }
        
        # Mock existing tests context with detailed test code
        self.existing_tests_context_with_details = {
            'matched_test_files': [
                '/path/to/tests/test_utils.cpp'
            ],
            'existing_test_functions': [
                {
                    'name': 'TEST_F(utils_test, process_data_When_PositiveInput_Should_ReturnDouble)',
                    'target_function': 'process_data',
                    'code': '''int input = 10;
int expected_output = 20;
int actual_output = process_data(input);
EXPECT_EQ(expected_output, actual_output);
// Additional test logic here
// More complex assertions
// Even more test code'''
                },
                {
                    'name': 'TEST_F(utils_test, another_function_When_ValidInput_Should_Work)',
                    'target_function': 'another_function',
                    'code': '''// Some test code for another function
int result = another_function(42);
EXPECT_GT(result, 0);'''
                }
            ],
            'test_coverage_summary': 'Found 2 existing tests in 1 test files',
            'existing_test_classes': [
                {
                    'name': 'utils_test',
                    'definition': '''class utils_test : public ::testing::Test {
protected:
    void SetUp() override {
        // Custom setup code
        test_data = new TestData();
    }
    void TearDown() override {
        GlobalMockObject::verify();
        delete test_data;
    }
    TestData* test_data;
};''',
                    'file_path': '/path/to/tests/test_utils.cpp'
                }
            ]
        }
        
        # Mock existing tests context without existing test classes
        self.existing_tests_context_no_classes = {
            'matched_test_files': [],
            'existing_test_functions': [],
            'test_coverage_summary': 'Found 0 existing tests in 0 test files'
        }
    
    def test_existing_test_context_simplified_format(self):
        """Test that existing test functions only show TEST_F and function name, not detailed code"""
        prompt = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=self.existing_tests_context_with_details
        )
        
        # Should contain TEST_F and function name
        assert 'TEST_F(utils_test, process_data_When_PositiveInput_Should_ReturnDouble)' in prompt
        assert 'TEST_F(utils_test, another_function_When_ValidInput_Should_Work)' in prompt
        
        # Should NOT contain detailed test code
        assert 'int input = 10;' not in prompt
        assert 'int expected_output = 20;' not in prompt
        assert 'EXPECT_EQ(expected_output, actual_output);' not in prompt
        assert 'Additional test logic here' not in prompt
        assert 'More complex assertions' not in prompt
        
        # Should still contain target function information
        assert '(测试目标: process_data)' in prompt
        assert '(测试目标: another_function)' in prompt
    
    def test_recommended_test_class_with_existing_classes(self):
        """Test that when existing test classes are found, use their definition instead of default template"""
        prompt = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=self.existing_tests_context_with_details
        )
        
        # Should use existing test class definition
        assert 'class utils_test : public ::testing::Test {' in prompt
        assert 'TestData* test_data;' in prompt
        assert 'test_data = new TestData();' in prompt
        assert 'delete test_data;' in prompt
        
        # Should NOT contain default template
        assert '// 仅在确实需要时添加共同的初始化代码' not in prompt
        assert '// 大多数情况下可以为空' not in prompt
    
    def test_recommended_test_class_without_existing_classes(self):
        """Test that when no existing test classes are found, use default template"""
        prompt = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=self.existing_tests_context_no_classes
        )
        
        # Should use default template
        assert 'class utils_test : public ::testing::Test {' in prompt
        assert '// 仅在确实需要时添加共同的初始化代码' in prompt
        assert '// 大多数情况下可以为空' in prompt
        assert 'GlobalMockObject::verify();' in prompt
        
        # Should NOT contain custom test class elements
        assert 'TestData* test_data;' not in prompt
        assert 'test_data = new TestData();' not in prompt
    
    def test_recommended_test_class_without_existing_context(self):
        """Test that when no existing tests context is provided, use default template"""
        prompt = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=None
        )
        
        # Should use default template
        assert 'class utils_test : public ::testing::Test {' in prompt
        assert '// 仅在确实需要时添加共同的初始化代码' in prompt
        assert '// 大多数情况下可以为空' in prompt
        assert 'GlobalMockObject::verify();' in prompt
    
    def test_existing_test_context_section_presence(self):
        """Test that existing test context section is only present when there are existing tests"""
        # With existing tests
        prompt_with_tests = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=self.existing_tests_context_with_details
        )
        assert '# 3.1. 现有测试上下文 (Existing Test Context)' in prompt_with_tests
        assert '**重要提示:** 以下是在单元测试目录中发现的与当前待测函数相关的现有测试信息' in prompt_with_tests
        
        # Without existing tests
        prompt_without_tests = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=None
        )
        assert '# 3.1. 现有测试上下文 (Existing Test Context)' not in prompt_without_tests
        
        # With empty existing tests
        prompt_empty_tests = PromptTemplates.generate_test_prompt(
            self.compressed_context,
            existing_tests_context=self.existing_tests_context_no_classes
        )
        assert '# 3.1. 现有测试上下文 (Existing Test Context)' in prompt_empty_tests


if __name__ == '__main__':
    pytest.main([__file__, '-v'])