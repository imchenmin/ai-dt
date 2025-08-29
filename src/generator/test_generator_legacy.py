"""
Legacy test generator - backward compatibility wrapper

This module provides a wrapper around the new modular architecture to maintain
backward compatibility with existing code.
"""

from typing import Dict, Any, List

from src.test_generation import TestGenerationService, TestGenerationConfig
from src.llm.client import LLMClient
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class TestGenerator:
    """
    Legacy test generator that maintains backward compatibility
    
    This class wraps the new TestGenerationService to provide the same API
    as the original TestGenerator while using the improved architecture.
    """
    
    def __init__(self, llm_provider: str = "mock", api_key: str = None, 
                 base_url: str = None, model: str = None,
                 max_retries: int = 3, retry_delay: float = 1.0):
        
        # Create LLM client using new architecture
        self.llm_client = LLMClient(
            provider=llm_provider,
            api_key=api_key,
            base_url=base_url,
            model=model or self._get_default_model(llm_provider),
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # Create service using new architecture
        self.service = TestGenerationService(self.llm_client)
        
        # Store provider info for compatibility
        self.provider = llm_provider
        self.model = model or self._get_default_model(llm_provider)
    
    def _get_default_model(self, llm_provider: str) -> str:
        """Get default model for provider"""
        if llm_provider == "openai":
            return "gpt-3.5-turbo"
        elif llm_provider == "deepseek":
            return "deepseek-chat"
        else:
            return "gpt-3.5-turbo"
    
    def generate_test(self, function_info: Dict[str, Any], 
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test for a single function (backward compatible)"""
        # Use new service for single function generation
        functions_with_context = [{'function': function_info, 'context': context}]
        
        # Create minimal config
        config = TestGenerationConfig(
            project_name="single_function",
            output_dir="",  # No file output for single generation
            max_workers=1,
            execution_strategy="sequential",
            save_prompts=False,
            aggregate_tests=False,
            generate_readme=False
        )
        
        # Generate using new service
        results = self.service.generate_tests_new_api(functions_with_context, config)
        
        if results.results:
            return results.results[0].to_dict()
        else:
            return {
                'success': False,
                'error': 'No results generated',
                'function_name': function_info['name'],
                'test_code': ''
            }
    
    def generate_tests(self, functions_with_context: List[Dict[str, Any]], 
                      project_config: Dict[str, Any],
                      max_workers: int = 3) -> List[Dict[str, Any]]:
        """Generate tests for multiple functions (backward compatible)"""
        
        # Use new service architecture
        return self.service.generate_tests(
            functions_with_context, project_config, max_workers
        )
    
    def generate_summary_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate summary report of test generation"""
        return self.service.get_summary_report(results)
    
    def _should_generate_test(self, function_info: Dict[str, Any]) -> bool:
        """Determine if test should be generated for this function"""
        # Basic filtering - you can enhance this
        if function_info.get('is_static', False):
            return False
        
        if function_info.get('language') == 'c' and function_info.get('is_static', False):
            return False
        
        return True