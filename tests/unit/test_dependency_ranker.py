"""
Unit tests for DependencyRanker utility
"""

import pytest
from src.utils.dependency_ranker import (
    DependencyRanker, DependencyType, ImportanceLevel, RankedDependency, select_top_dependencies
)


def test_dependency_ranker_initialization():
    """Test DependencyRanker initialization"""
    target_function = {
        'name': 'test_func',
        'file': '/path/to/module/test.c',
        'return_type': 'int',
        'parameters': []
    }
    
    ranker = DependencyRanker(target_function)
    assert ranker.target_function == target_function
    assert len(ranker.compiled_patterns) > 0


def test_rank_called_functions():
    """Test ranking called functions"""
    target_function = {
        'name': 'target_func',
        'file': '/path/to/module/main.c',
        'return_type': 'void',
        'parameters': []
    }
    
    called_functions = [
        {
            'name': 'malloc',
            'declaration': 'void* malloc(size_t size);',
            'is_mockable': True,
            'location': '/path/to/module/main.c:10'
        },
        {
            'name': 'helper_func',
            'declaration': 'int helper_func(int x);',
            'is_mockable': True,
            'location': '/path/to/other/module/util.c:5'
        }
    ]
    
    all_functions = []  # Not used in current implementation
    
    ranker = DependencyRanker(target_function)
    ranked = ranker.rank_called_functions(called_functions, all_functions)
    
    assert len(ranked) == 2
    assert all(isinstance(dep, RankedDependency) for dep in ranked)
    
    # malloc should have higher score (critical pattern)
    malloc_score = next(dep for dep in ranked if dep.name == 'malloc').score
    helper_score = next(dep for dep in ranked if dep.name == 'helper_func').score
    assert malloc_score > helper_score


def test_rank_data_structures():
    """Test ranking data structures"""
    target_function = {
        'name': 'test_func',
        'file': '/path/to/module/test.c',
        'return_type': 'int',
        'parameters': []
    }
    
    data_structures = [
        {
            'name': 'complex_struct',
            'definition': 'struct complex_struct {\n    int data;\n    char* buffer;\n};'
        },
        {
            'name': 'simple_type',
            'definition': 'typedef int simple_type;'
        }
    ]
    
    ranker = DependencyRanker(target_function)
    ranked = ranker.rank_data_structures(data_structures)
    
    assert len(ranked) == 2
    assert all(dep.type == DependencyType.DATA_STRUCTURE for dep in ranked)
    
    # complex_struct should have higher score
    complex_score = next(dep for dep in ranked if dep.name == 'complex_struct').score
    simple_score = next(dep for dep in ranked if dep.name == 'simple_type').score
    assert complex_score > simple_score


def test_rank_macros():
    """Test ranking macros"""
    target_function = {
        'name': 'test_func',
        'file': '/path/to/module/test.c',
        'return_type': 'int',
        'parameters': []
    }
    
    macros = ['DEBUG', 'MAX_SIZE']
    macro_definitions = [
        {'name': 'DEBUG', 'definition': '#define DEBUG 1'},
        {'name': 'MAX_SIZE', 'definition': '#define MAX_SIZE(x) ((x) * 2)'}
    ]
    
    ranker = DependencyRanker(target_function)
    ranked = ranker.rank_macros(macros, macro_definitions)
    
    assert len(ranked) == 2
    assert all(dep.type == DependencyType.MACRO for dep in ranked)
    
    # MAX_SIZE should have higher score (function-like macro)
    max_size_score = next(dep for dep in ranked if dep.name == 'MAX_SIZE').score
    debug_score = next(dep for dep in ranked if dep.name == 'DEBUG').score
    assert max_size_score > debug_score


def test_importance_level_determination():
    """Test importance level determination from scores"""
    target_function = {
        'name': 'test_func',
        'file': '/path/to/module/test.c',
        'return_type': 'int',
        'parameters': []
    }
    
    ranker = DependencyRanker(target_function)
    
    # Test different score ranges
    assert ranker._determine_importance_level(3.5) == ImportanceLevel.CRITICAL
    assert ranker._determine_importance_level(2.0) == ImportanceLevel.HIGH
    assert ranker._determine_importance_level(1.0) == ImportanceLevel.MEDIUM
    assert ranker._determine_importance_level(0.2) == ImportanceLevel.LOW
    assert ranker._determine_importance_level(0.0) == ImportanceLevel.LOW


def test_select_top_dependencies():
    """Test selecting top dependencies"""
    # Create mock ranked dependencies
    ranked_deps = [
        RankedDependency('func1', DependencyType.CALLED_FUNCTION, ImportanceLevel.CRITICAL, 4.0, {}),
        RankedDependency('func2', DependencyType.CALLED_FUNCTION, ImportanceLevel.HIGH, 3.0, {}),
        RankedDependency('func3', DependencyType.CALLED_FUNCTION, ImportanceLevel.MEDIUM, 2.0, {}),
        RankedDependency('func4', DependencyType.CALLED_FUNCTION, ImportanceLevel.LOW, 1.0, {})
    ]
    
    # Test selecting top 2
    selected = select_top_dependencies(ranked_deps, max_count=2)
    assert len(selected) == 2
    
    # Test with minimum importance
    selected_high = select_top_dependencies(ranked_deps, max_count=10, 
                                          min_importance=ImportanceLevel.HIGH)
    assert len(selected_high) == 2  # Only CRITICAL and HIGH
    
    # Test empty input
    assert select_top_dependencies([], max_count=5) == []


def test_same_module_detection():
    """Test same module detection heuristic"""
    target_function = {
        'name': 'test_func',
        'file': '/path/to/module/main.c',
        'return_type': 'int',
        'parameters': []
    }
    
    ranker = DependencyRanker(target_function)
    
    # Same module
    assert ranker._is_same_module('/path/to/module/main.c', '/path/to/module/util.c')
    
    # Different module
    assert not ranker._is_same_module('/path/to/module/main.c', '/other/path/util.c')
    
    # Edge cases
    assert not ranker._is_same_module('', '/path/file.c')
    assert not ranker._is_same_module('/path/file.c', '')


def test_function_complexity_estimation():
    """Test function complexity estimation"""
    target_function = {
        'name': 'test_func',
        'file': '/path/to/module/test.c',
        'return_type': 'int',
        'parameters': []
    }
    
    ranker = DependencyRanker(target_function)
    
    # Test with different function signatures
    simple_func = {'parameters': [], 'return_type': 'int'}
    complex_func = {'parameters': [{'name': 'x'}, {'name': 'y'}], 'return_type': 'struct complex*'}
    
    simple_score = ranker._estimate_function_complexity(simple_func)
    complex_score = ranker._estimate_function_complexity(complex_func)
    
    assert complex_score > simple_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])