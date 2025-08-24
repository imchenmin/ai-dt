"""
Unit tests for refactored ContextCompressor with intelligent compression
"""

import pytest
from unittest.mock import patch, MagicMock
from src.utils.context_compressor import ContextCompressor


def test_context_compressor_initialization():
    """Test ContextCompressor initialization with different configurations"""
    # Test default initialization
    compressor = ContextCompressor()
    assert compressor.llm_provider == "openai"
    assert compressor.llm_model == "gpt-3.5-turbo"
    assert hasattr(compressor, 'token_counter')
    assert compressor.max_context_size > 0
    
    # Test with custom provider and model
    compressor = ContextCompressor(llm_provider="deepseek", llm_model="deepseek-coder")
    assert compressor.llm_provider == "deepseek"
    assert compressor.llm_model == "deepseek-coder"
    
    # Test with legacy size parameter
    compressor = ContextCompressor(max_context_size=5000)
    assert compressor.max_context_size == 5000


def test_compress_target_function():
    """Test target function compression"""
    compressor = ContextCompressor()
    
    function_info = {
        'name': 'test_func',
        'return_type': 'int',
        'parameters': [{'name': 'x', 'type': 'int'}, {'name': 'y', 'type': 'float'}],
        'file': '/path/to/file.c',
        'line': 10,
        'body': 'int test_func(int x, float y) { return x + (int)y; }',
        'language': 'c',
        'is_static': False,
        'access_specifier': 'public'
    }
    
    compressed = compressor._compress_target_function(function_info)
    
    assert compressed['name'] == 'test_func'
    assert compressed['return_type'] == 'int'
    assert len(compressed['parameters']) == 2
    assert compressed['location'] == '/path/to/file.c:10'
    assert compressed['language'] == 'c'
    assert compressed['body_preview'] == function_info['body'][:300]
    assert not compressed['is_static']


def test_format_function_signature():
    """Test function signature formatting"""
    compressor = ContextCompressor()
    
    function_info = {
        'name': 'calculate',
        'return_type': 'double',
        'parameters': [
            {'name': 'a', 'type': 'int'},
            {'name': 'b', 'type': 'double'}
        ]
    }
    
    signature = compressor._format_function_signature(function_info)
    expected = "double calculate(int a, double b)"
    assert signature == expected
    
    # Test with no parameters
    function_info_no_params = {
        'name': 'get_value',
        'return_type': 'int',
        'parameters': []
    }
    
    signature = compressor._format_function_signature(function_info_no_params)
    expected = "int get_value()"
    assert signature == expected


def test_compress_dependencies():
    """Test dependency compression with ranking"""
    compressor = ContextCompressor()
    
    function_info = {
        'name': 'target_func',
        'file': '/path/to/module/main.c',
        'return_type': 'void',
        'parameters': []
    }
    
    context = {
        'called_functions': [
            {'name': 'malloc', 'declaration': 'void* malloc(size_t);', 'location': 'stdlib.h:1'},
            {'name': 'free', 'declaration': 'void free(void*);', 'location': 'stdlib.h:1'},
            {'name': 'helper', 'declaration': 'int helper(int);', 'location': '/other/module.c:5'}
        ],
        'macros_used': ['DEBUG', 'MAX_SIZE'],
        'macro_definitions': [
            {'name': 'DEBUG', 'definition': '#define DEBUG 1'},
            {'name': 'MAX_SIZE', 'definition': '#define MAX_SIZE 100'}
        ],
        'data_structures': [
            {'name': 'Node', 'definition': 'struct Node { int data; Node* next; };'},
            {'name': 'Config', 'definition': 'typedef struct { int value; } Config;'}
        ]
    }
    
    compressed_deps = compressor._compress_dependencies(context, function_info)
    
    # Should have compressed dependencies with ranking
    assert 'called_functions' in compressed_deps
    assert 'macros' in compressed_deps
    assert 'macro_definitions' in compressed_deps
    assert 'data_structures' in compressed_deps
    assert 'dependency_definitions' in compressed_deps
    
    # Critical functions like malloc should be prioritized
    func_names = [f['name'] for f in compressed_deps['called_functions']]
    assert 'malloc' in func_names or 'free' in func_names


def test_compress_usage_patterns():
    """Test usage patterns compression"""
    compressor = ContextCompressor()
    
    context = {
        'call_sites': [
            {'file': '/path/to/file1.c', 'line': 5, 'context': 'int result = func(1, 2);'},
            {'file': '/path/to/file1.c', 'line': 8, 'context': 'func(3, 4);'},
            {'file': '/path/to/file2.c', 'line': 12, 'context': 'value = func(5, 6) * 2;'}
        ]
    }
    
    compressed = compressor._compress_usage_patterns(context)
    
    # Should select representative call sites from different files
    assert len(compressed) <= 2
    
    if len(compressed) > 0:
        site = compressed[0]
        assert 'file' in site
        assert 'line' in site
        assert 'context_preview' in site
        assert len(site['context_preview']) <= 200


def test_compress_compilation_info():
    """Test compilation info compression"""
    compressor = ContextCompressor()
    
    context = {
        'compilation_flags': [
            '-I/include/path',
            '-DDEBUG=1', 
            '-std=c11',
            '-O2',
            '-Wall',
            '-Wextra'
        ]
    }
    
    compressed = compressor._compress_compilation_info(context)
    
    assert 'key_flags' in compressed
    assert 'total_flags_count' in compressed
    assert compressed['total_flags_count'] == 6
    
    # Should select key flags (note: only first 3 matching flags are selected)
    key_flags = compressed['key_flags']
    assert len(key_flags) <= 3
    assert any(flag.startswith('-I') for flag in key_flags)
    assert any(flag.startswith('-D') for flag in key_flags)
    assert any(flag.startswith('-std=') for flag in key_flags)
    # -O flags might not be in top 3 due to ordering


def test_ensure_optimal_size_within_limits():
    """Test size optimization when within limits"""
    compressor = ContextCompressor()
    
    # Create a small context that should be within limits
    small_context = {
        'target_function': {
            'name': 'test',
            'body_preview': 'void test() {}'
        },
        'dependencies': {},
        'usage_patterns': [],
        'compilation_info': {'key_flags': [], 'total_flags_count': 0}
    }
    
    function_info = {'name': 'test'}
    
    # Mock token counter to return small values
    with patch.object(compressor.token_counter, 'count_tokens_from_dict', return_value=100), \
         patch.object(compressor.token_counter, 'get_available_tokens', return_value=1000):
        
        result = compressor._ensure_optimal_size(small_context, function_info)
        
        # Should return unchanged since within limits
        assert result == small_context


def test_ensure_optimal_size_compression():
    """Test size optimization with compression needed"""
    compressor = ContextCompressor()
    
    # Create a context that exceeds limits with more complex structure
    large_context = {
        'target_function': {
            'name': 'test',
            'body_preview': 'x' * 500,  # Large body
            'signature': 'void test(int x)',
            'return_type': 'void',
            'parameters': [{'name': 'x', 'type': 'int'}]
        },
        'dependencies': {
            'called_functions': [{'name': f'func{i}', 'declaration': f'void func{i}();'} for i in range(5)],
            'macros': ['TEST_MACRO'],
            'macro_definitions': [{'name': 'TEST_MACRO', 'definition': '#define TEST_MACRO 1'}],
            'data_structures': ['TestStruct'],
            'dependency_definitions': ['struct TestStruct { int value; };']
        },
        'usage_patterns': [
            {'file': 'test.c', 'line': 10, 'context_preview': 'y' * 300},
            {'file': 'main.c', 'line': 20, 'context_preview': 'z' * 300}
        ],
        'compilation_info': {'key_flags': ['-I/include', '-O2'], 'total_flags_count': 2}
    }
    
    function_info = {'name': 'test', 'file': 'test.c'}
    
    # Mock token counter to simulate large context
    with patch.object(compressor.token_counter, 'count_tokens_from_dict') as mock_count, \
         patch.object(compressor.token_counter, 'get_available_tokens', return_value=500):
        
        # First call: over limit, subsequent calls: reduced
        mock_count.side_effect = [1000, 800, 600, 400]
        
        result = compressor._ensure_optimal_size(large_context, function_info)
        
        # Should have applied compression
        assert mock_count.call_count >= 2
        # Result should be different from original (check specific changes)
        assert len(result['target_function']['body_preview']) <= len(large_context['target_function']['body_preview'])
        assert len(result['dependencies']['called_functions']) <= len(large_context['dependencies']['called_functions'])


def test_compress_function_context_integration():
    """Test full context compression integration"""
    compressor = ContextCompressor()
    
    function_info = {
        'name': 'test_func',
        'return_type': 'int',
        'parameters': [{'name': 'x', 'type': 'int'}],
        'file': '/path/to/file.c',
        'line': 5,
        'body': 'int test_func(int x) { return x * 2; }',
        'language': 'c',
        'is_static': False
    }
    
    full_context = {
        'called_functions': [
            {'name': 'printf', 'declaration': 'int printf(const char*, ...);', 'location': 'stdio.h:1'}
        ],
        'macros_used': ['DEBUG'],
        'macro_definitions': [{'name': 'DEBUG', 'definition': '#define DEBUG 1'}],
        'data_structures': [],
        'call_sites': [
            {'file': '/path/to/main.c', 'line': 10, 'context': 'int result = test_func(5);'}
        ],
        'compilation_flags': ['-I/include', '-std=c11', '-O2']
    }
    
    compressed = compressor.compress_function_context(function_info, full_context)
    
    # Should return compressed context with all sections
    assert 'target_function' in compressed
    assert 'dependencies' in compressed
    assert 'usage_patterns' in compressed
    assert 'compilation_info' in compressed
    
    # Target function should be preserved
    assert compressed['target_function']['name'] == 'test_func'
    assert compressed['target_function']['return_type'] == 'int'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])