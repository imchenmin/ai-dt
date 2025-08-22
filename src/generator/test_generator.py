"""
Test generator using LLM for Google Test + MockCpp generation
"""

import logging
import time
from typing import Dict, Any, List
from pathlib import Path

from src.utils.context_compressor import ContextCompressor
from .llm_client import LLMClient, MockLLMClient

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generates tests using LLM with extracted context"""
    
    def __init__(self, llm_provider: str = "mock", api_key: str = None, 
                 base_url: str = None, model: str = None):
        self.context_compressor = ContextCompressor()
        
        if llm_provider == "mock":
            self.llm_client = MockLLMClient()
        else:
            # Set default models based on provider
            if model is None:
                if llm_provider == "openai":
                    model = "gpt-3.5-turbo"
                elif llm_provider == "deepseek":
                    model = "deepseek-chat"  # Default DeepSeek model
                else:
                    model = "gpt-3.5-turbo"
            
            self.llm_client = LLMClient(
                provider=llm_provider,
                api_key=api_key,
                base_url=base_url,
                model=model
            )
    
    def generate_test(self, function_info: Dict[str, Any], 
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test for a single function"""
        try:
            # Compress context for LLM
            compressed_context = self.context_compressor.compress_function_context(
                function_info, context
            )
            
            # Generate LLM prompt
            prompt = self.context_compressor.format_for_llm_prompt(compressed_context)
            
            logger.info(f"Generated prompt for {function_info['name']} "
                       f"({len(prompt)} characters)")
            
            # Send to LLM
            result = self.llm_client.generate_test(
                prompt=prompt,
                max_tokens=2500,
                temperature=0.3
            )
            
            if result['success']:
                logger.info(f"Successfully generated test for {function_info['name']}")
                logger.info(f"Tokens used: {result.get('usage', {})}")
                
                # Add metadata to result
                result['function_name'] = function_info['name']
                result['prompt_length'] = len(prompt)
                result['test_length'] = len(result['test_code'])
                
            else:
                logger.error(f"Failed to generate test for {function_info['name']}: "
                           f"{result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating test for {function_info['name']}: {e}")
            return {
                'success': False,
                'error': str(e),
                'function_name': function_info['name'],
                'test_code': ''
            }
    
    def generate_tests(self, functions_with_context: List[Dict[str, Any]], 
                      output_dir: str = "./generated_tests") -> List[Dict[str, Any]]:
        """Generate tests for multiple functions"""
        results = []
        
        for func_data in functions_with_context:
            function_info = func_data['function']
            context = func_data['context']
            
            if not self._should_generate_test(function_info):
                logger.info(f"Skipping non-testable function: {function_info['name']}")
                continue
            
            result = self.generate_test(function_info, context)
            
            if result['success']:
                # Save test code to file
                output_path = self.llm_client.save_test_code(
                    result['test_code'],
                    function_info['name'],
                    output_dir
                )
                result['output_path'] = output_path
                logger.info(f"Saved test to: {output_path}")
            
            results.append(result)
            
            # Add small delay to avoid rate limiting
            time.sleep(1)
        
        return results
    
    def _should_generate_test(self, function_info: Dict[str, Any]) -> bool:
        """Determine if test should be generated for this function"""
        # Basic filtering - you can enhance this
        if function_info.get('is_static', False):
            return False
        
        if function_info.get('language') == 'c' and function_info.get('is_static', False):
            return False
        
        return True
    
    def generate_summary_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate summary report of test generation"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        report = [
            "=== Test Generation Summary ===",
            f"Total functions processed: {len(results)}",
            f"Successful generations: {len(successful)}",
            f"Failed generations: {len(failed)}",
            "",
            "Successful tests:"
        ]
        
        for result in successful:
            report.append(f"  - {result['function_name']}: "
                        f"{result['test_length']} chars, "
                        f"saved to {result.get('output_path', 'unknown')}")
        
        if failed:
            report.extend(["", "Failed generations:"])
            for result in failed:
                report.append(f"  - {result['function_name']}: {result['error']}")
        
        # Add token usage summary
        total_tokens = sum(
            r.get('usage', {}).get('total_tokens', 0) 
            for r in successful
        )
        if total_tokens > 0:
            report.extend(["", f"Total tokens used: {total_tokens}"])
        
        return '\n'.join(report)