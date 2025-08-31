"""
Integration tests for the refactored architecture
"""

import pytest
from unittest.mock import Mock

from src.llm.client import LLMClient
from src.test_generation.models import TestGenerationConfig
from src.test_generation.service import TestGenerationService


def test_integration_basic_workflow():
    """Test basic integration workflow"""
    # Create mock client
    client = LLMClient.create_mock_client()
    
    # Create service
    service = TestGenerationService(client)
    
    # Create test data
    function_info = {
        'name': 'add_numbers',
        'file': 'math.c',
        'language': 'c',
        'return_type': 'int',
        'parameters': [
            {'name': 'a', 'type': 'int'},
            {'name': 'b', 'type': 'int'}
        ],
        'body': 'return a + b;'
    }
    
    context = {
        'called_functions': [],
        'macros_used': [],
        'macro_definitions': [],
        'data_structures': []
    }
    
    functions_with_context = [{'function': function_info, 'context': context}]
    
    # Create configuration
    config = TestGenerationConfig(
        project_name="test_project",
        output_dir="",  # No output for test
        max_workers=1,
        execution_strategy="sequential",
        save_prompts=False,
        aggregate_tests=False,
        generate_readme=False
    )
    
    # Generate tests
    result = service.generate_tests_new_api(functions_with_context, config)
    
    assert result.total_count == 1
    assert result.successful_count == 1
    assert len(result.results) == 1
    assert result.results[0].success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])