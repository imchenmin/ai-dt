"""Unit tests for PromptContext and related data models"""

import pytest
from typing import Dict, Any

from src.test_generation.models import (
    PromptContext,
    TargetFunction,
    Dependencies,
    CompilationInfo,
    ExistingTestsContext,
    Language,
    Parameter,
    CalledFunction,
    MacroDefinition,
    UsagePattern,
    TestFunction,
    TestClass
)


class TestPromptContext:
    """Test cases for PromptContext data model"""
    
    def test_creation_with_required_fields(self):
        """Test creating PromptContext with required fields"""
        target = TargetFunction(
            name="test_func",
            signature="int test_func(int x)",
            return_type="int",
            parameters=[],
            body="int test_func(int x) { return x * 2; }",
            location="test.c:10",
            language=Language.C
        )
        
        deps = Dependencies()
        
        context = PromptContext(
            target_function=target,
            dependencies=deps
        )
        
        assert context.target_function == target
        assert context.dependencies == deps
        assert context.usage_patterns == []
        assert context.compilation_info is None
        assert context.existing_tests_context is None
        assert context.existing_fixture_code is None
        assert context.suite_name is None
    
    def test_creation_with_all_fields(self):
        """Test creating PromptContext with all fields"""
        target = TargetFunction(
            name="hash_insert",
            signature="int hash_insert(HashTable* table, const char* key, void* value)",
            location="hash_table.c:145",
            return_type="int",
            language=Language.C,
            parameters=[
                Parameter(name="table", type="HashTable*"),
                Parameter(name="key", type="const char*"),
                Parameter(name="value", type="void*")
            ],
            body="int hash_insert(HashTable* table, const char* key, void* value) { ... }",
            is_static=False,
            access_specifier="public"
        )
        
        deps = Dependencies(
            called_functions=[
                CalledFunction(
                    name="hash_function",
                    declaration="unsigned int hash_function(const char* key)",
                    is_mockable=True,
                    location="hash_table.h:25"
                )
            ],
            macro_definitions=[
                MacroDefinition(name="HASH_SIZE", definition="#define HASH_SIZE 1024")
            ]
        )
        
        usage_patterns = [
            UsagePattern(
                file="main.c",
                line=42,
                context_preview="int result = hash_insert(table, \"key\", value);"
            )
        ]
        
        comp_info = CompilationInfo(
            include_paths=["/usr/include", "/usr/local/include"],
            compiler_flags=["-std=c99", "-Wall"]
        )
        
        existing_tests = ExistingTestsContext(
            existing_test_functions=[
                TestFunction(
                    name="TEST_F(HashTableTest, InsertValidKey)",
                    target_function="hash_insert",
                    code="// 测试插入有效键"
                )
            ],
            existing_test_classes=[
                TestClass(
                    name="HashTableTest",
                    definition="class HashTableTest : public ::testing::Test { ... }"
                )
            ]
        )
        
        context = PromptContext(
            target_function=target,
            dependencies=deps,
            usage_patterns=usage_patterns,
            compilation_info=comp_info,
            existing_tests_context=existing_tests,
            existing_fixture_code="class TestFixture {};",
            suite_name="HashTableTest"
        )
        
        assert context.target_function.name == "hash_insert"
        assert len(context.dependencies.called_functions) == 1
        assert len(context.usage_patterns) == 1
        assert context.compilation_info.include_paths == ["/usr/include", "/usr/local/include"]
        assert context.compilation_info.compiler_flags == ["-std=c99", "-Wall"]
        assert len(context.existing_tests_context.existing_test_functions) == 1
        assert context.existing_fixture_code == "class TestFixture {};"
        assert context.suite_name == "HashTableTest"
    
    def test_from_compressed_context_basic(self):
        """Test creating PromptContext from compressed context dictionary"""
        compressed_context = {
            'target_function': {
                'name': 'calculate_sum',
                'signature': 'int calculate_sum(int a, int b)',
                'location': 'math_utils.c:15',
                'return_type': 'int',
                'language': 'c',
                'parameters': [
                    {'name': 'a', 'type': 'int'},
                    {'name': 'b', 'type': 'int'}
                ],
                'body': 'int calculate_sum(int a, int b) { return a + b; }',
                'is_static': False,
                'access_specifier': 'public'
            },
            'dependencies': {
                'called_functions': [
                    {
                        'name': 'validate_input',
                        'declaration': 'bool validate_input(int value)',
                        'is_mockable': True,
                        'location': 'validation.h:10'
                    }
                ],
                'macro_definitions': [
                    {'name': 'MAX_VALUE', 'definition': '#define MAX_VALUE 1000'}
                ],
                'macros': ['DEBUG'],
                'data_structures': ['InputData'],
                'dependency_definitions': ['struct InputData { int value; };']
            },
            'usage_patterns': [
                {
                    'file': 'main.c',
                    'line': 25,
                    'context_preview': 'int result = calculate_sum(10, 20);'
                }
            ],
            'compilation_info': {
                'include_paths': ['/usr/include'],
                'compiler_flags': ['-std=c99']
            }
        }
        
        context = PromptContext.from_compressed_context(compressed_context)
        
        assert context.target_function.name == 'calculate_sum'
        assert context.target_function.language == Language.C
        assert len(context.target_function.parameters) == 2
        assert context.target_function.parameters[0].name == 'a'
        assert context.target_function.parameters[0].type == 'int'
        
        assert len(context.dependencies.called_functions) == 1
        assert context.dependencies.called_functions[0].name == 'validate_input'
        assert context.dependencies.called_functions[0].is_mockable is True
        
        assert len(context.dependencies.macro_definitions) == 1
        assert context.dependencies.macro_definitions[0].name == 'MAX_VALUE'
        
        assert len(context.usage_patterns) == 1
        assert context.usage_patterns[0].file == 'main.c'
        assert context.usage_patterns[0].line == 25
        
        assert context.compilation_info.include_paths == ['/usr/include']
        assert context.compilation_info.compiler_flags == ['-std=c99']
    
    def test_from_compressed_context_with_existing_tests(self):
        """Test creating PromptContext with existing tests context"""
        compressed_context = {
            'target_function': {
                'name': 'process_data',
                'signature': 'int process_data(int input)',
                'location': 'utils.c:10',
                'return_type': 'int',
                'language': 'c',
                'body': 'int process_data(int input) { return input * 2; }'
            },
            'dependencies': {
                'called_functions': [],
                'macro_definitions': [],
                'macros': [],
                'data_structures': [],
                'dependency_definitions': []
            }
        }
        
        existing_tests_context = {
            'existing_test_functions': [
                {
                    'name': 'TEST_F(UtilsTest, ProcessDataValidInput)',
                    'target_function': 'process_data',
                    'code': '// 测试有效输入'
                }
            ],
            'existing_test_classes': [
                {
                    'name': 'UtilsTest',
                    'definition': 'class UtilsTest : public ::testing::Test { ... }'
                }
            ]
        }
        
        context = PromptContext.from_compressed_context(
            compressed_context,
            existing_fixture_code="class TestFixture {};",
            suite_name="UtilsTest",
            existing_tests_context=existing_tests_context
        )
        
        assert context.target_function.name == 'process_data'
        assert context.existing_fixture_code == "class TestFixture {};"
        assert context.suite_name == "UtilsTest"
        
        assert context.existing_tests_context is not None
        assert len(context.existing_tests_context.existing_test_functions) == 1
        assert context.existing_tests_context.existing_test_functions[0].name == 'TEST_F(UtilsTest, ProcessDataValidInput)'
        assert context.existing_tests_context.existing_test_functions[0].target_function == 'process_data'
        
        assert len(context.existing_tests_context.existing_test_classes) == 1
        assert context.existing_tests_context.existing_test_classes[0].name == 'UtilsTest'
    
    def test_from_compressed_context_minimal(self):
        """Test creating PromptContext from minimal compressed context"""
        compressed_context = {
            'target_function': {
                'name': 'simple_func',
                'signature': 'void simple_func()',
                'location': 'simple.c:5',
                'return_type': 'void',
                'language': 'c',
                'body': 'void simple_func() { }'
            },
            'dependencies': {
                'called_functions': [],
                'macro_definitions': [],
                'macros': [],
                'data_structures': [],
                'dependency_definitions': []
            }
        }
        
        context = PromptContext.from_compressed_context(compressed_context)
        
        assert context.target_function.name == 'simple_func'
        assert context.target_function.return_type == 'void'
        assert context.target_function.language == Language.C
        assert len(context.dependencies.called_functions) == 0
        assert len(context.usage_patterns) == 0
        assert context.compilation_info is None
        assert context.existing_tests_context is None
        assert context.existing_fixture_code is None
        assert context.suite_name is None


class TestTargetFunction:
    """Test cases for TargetFunction data model"""
    
    def test_creation_minimal(self):
        """Test creating TargetFunction with minimal fields"""
        target = TargetFunction(
            name="test_func",
            signature="int test_func()",
            return_type="int",
            parameters=[],
            body="int test_func() { return 0; }",
            location="test.c:10",
            language=Language.C
        )
        
        assert target.name == "test_func"
        assert target.signature == "int test_func()"
        assert target.location == "test.c:10"
        assert target.return_type == "int"
        assert target.language == Language.C
        assert target.parameters == []
        assert target.body == "int test_func() { return 0; }"
        assert target.is_static is False
        assert target.access_specifier == "public"
    
    def test_from_dict(self):
        """Test creating TargetFunction from dictionary"""
        data = {
            'name': 'hash_function',
            'signature': 'unsigned int hash_function(const char* key)',
            'location': 'hash.c:25',
            'return_type': 'unsigned int',
            'language': 'c',
            'parameters': [
                {'name': 'key', 'type': 'const char*'}
            ],
            'body': 'unsigned int hash_function(const char* key) { ... }',
            'is_static': True,
            'access_specifier': 'private'
        }
        
        target = TargetFunction.from_dict(data)
        
        assert target.name == 'hash_function'
        assert target.return_type == 'unsigned int'
        assert target.language == Language.C
        assert len(target.parameters) == 1
        assert target.parameters[0].name == 'key'
        assert target.parameters[0].type == 'const char*'
        assert target.is_static is True
        assert target.access_specifier == 'private'


class TestDependencies:
    """Test cases for Dependencies data model"""
    
    def test_creation_empty(self):
        """Test creating empty Dependencies"""
        deps = Dependencies()
        
        assert deps.called_functions == []
        assert deps.macro_definitions == []
        assert deps.macros == []
        assert deps.data_structures == []
        assert deps.dependency_definitions == []
    
    def test_has_external_dependencies_true(self):
        """Test has_external_dependencies property returns True when dependencies exist"""
        deps = Dependencies(
            called_functions=[
                CalledFunction(name="malloc", declaration="void* malloc(size_t)")
            ]
        )
        
        assert deps.has_external_dependencies is True
    
    def test_has_external_dependencies_false(self):
        """Test has_external_dependencies property returns False when no dependencies"""
        deps = Dependencies()
        
        assert deps.has_external_dependencies is False
    
    def test_from_dict(self):
        """Test creating Dependencies from dictionary"""
        data = {
            'called_functions': [
                {
                    'name': 'strlen',
                    'declaration': 'size_t strlen(const char* str)',
                    'is_mockable': False,
                    'location': 'string.h:1'
                }
            ],
            'macro_definitions': [
                {'name': 'BUFFER_SIZE', 'definition': '#define BUFFER_SIZE 1024'}
            ],
            'macros': ['DEBUG', 'VERBOSE'],
            'data_structures': ['Node', 'Tree'],
            'dependency_definitions': [
                'struct Node { int data; Node* next; };'
            ]
        }
        
        deps = Dependencies.from_dict(data)
        
        assert len(deps.called_functions) == 1
        assert deps.called_functions[0].name == 'strlen'
        assert deps.called_functions[0].is_mockable is False
        
        assert len(deps.macro_definitions) == 1
        assert deps.macro_definitions[0].name == 'BUFFER_SIZE'
        
        assert deps.macros == ['DEBUG', 'VERBOSE']
        assert deps.data_structures == ['Node', 'Tree']
        assert len(deps.dependency_definitions) == 1


class TestLanguageEnum:
    """Test cases for Language enum"""
    
    def test_language_values(self):
        """Test Language enum values"""
        assert Language.C.value == 'c'
        assert Language.CPP.value == 'c++'
    
    def test_display_names(self):
        """Test Language display names"""
        assert Language.C.display_name == 'C'
        assert Language.CPP.display_name == 'C++'
    
    def test_language_creation(self):
        """Test creating Language instances"""
        assert Language.C == Language.C
        assert Language.CPP == Language.CPP
        
        # Test string values
        assert Language.C.value == 'c'
        assert Language.CPP.value == 'c++'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])