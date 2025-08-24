"""
Test generator using LLM for Google Test + MockCpp generation
"""

import logging
import time
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from src.utils.context_compressor import ContextCompressor
from src.utils.file_organizer import TestFileOrganizer
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
                      output_dir: str = "./generated_tests",
                      project_name: str = "unknown_project") -> List[Dict[str, Any]]:
        """Generate tests for multiple functions with organized output structure"""
        results = []
        
        # Create file organizer with timestamped directory
        file_organizer = TestFileOrganizer(output_dir)
        timestamped_dir = file_organizer.create_timestamped_directory(project_name)
        organized_organizer = TestFileOrganizer(timestamped_dir)
        
        for func_data in functions_with_context:
            function_info = func_data['function']
            context = func_data['context']
            
            if not self._should_generate_test(function_info):
                logger.info(f"Skipping non-testable function: {function_info['name']}")
                continue
            
            # Generate prompt first
            compressed_context = self.context_compressor.compress_function_context(
                function_info, context
            )
            prompt = self.context_compressor.format_for_llm_prompt(compressed_context)
            
            # Generate test
            result = self.generate_test(function_info, context)
            
            if result['success']:
                # Save all files using the organized structure
                file_info = organized_organizer.organize_test_output(
                    test_code=result['test_code'],
                    function_name=function_info['name'],
                    prompt=prompt,
                    raw_response=result['test_code']  # For now, use test_code as raw response
                )
                result['file_info'] = file_info
                result['output_path'] = file_info['test_path']
                logger.info(f"Saved organized test files for {function_info['name']}")
            else:
                # For failed generations, still save the prompt for debugging
                file_info = organized_organizer.organize_test_output(
                    test_code="",
                    function_name=function_info['name'],
                    prompt=prompt,
                    raw_response=f"Generation failed: {result.get('error', 'Unknown error')}"
                )
                result['file_info'] = file_info
            
            results.append(result)
            
            # Add small delay to avoid rate limiting
            time.sleep(1)
        
        # Generate README with generation info
        generation_info = {
            'timestamp': datetime.now().isoformat(),
            'project_name': project_name,
            'llm_provider': self.llm_client.provider,
            'model': getattr(self.llm_client, 'model', 'unknown'),
            'total_functions': len(functions_with_context),
            'successful': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']])
        }
        organized_organizer.generate_readme(generation_info)
        
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
        """Generate summary report of test generation with new file structure"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        # Find the base output directory from the first successful result
        base_output_dir = None
        if successful and 'file_info' in successful[0]:
            test_path = successful[0]['file_info']['test_path']
            base_output_dir = str(Path(test_path).parent.parent)
        
        report = [
            "=== Test Generation Summary ===",
            f"Total functions processed: {len(results)}",
            f"Successful generations: {len(successful)}",
            f"Failed generations: {len(failed)}",
        ]
        
        if base_output_dir:
            report.extend([
                "",
                "Output Directory Structure:",
                f"{base_output_dir}/",
                "├── 1_prompts/       # Input prompts sent to LLM",
                "├── 2_raw_responses/ # Raw LLM responses", 
                "├── 3_pure_tests/    # Extracted pure C++ test code",
                "└── README.md        # Generation metadata"
            ])
        
        report.extend(["", "Successful tests:"])
        
        for result in successful:
            if 'file_info' in result:
                file_info = result['file_info']
                report.append(f"  - {result['function_name']}: "
                            f"{result['test_length']} chars, "
                            f"saved to {file_info['test_path']}")
            else:
                report.append(f"  - {result['function_name']}: "
                            f"{result['test_length']} chars")
        
        if failed:
            report.extend(["", "Failed generations:"])
            for result in failed:
                error_msg = result.get('error', 'Unknown error')
                if 'file_info' in result:
                    file_info = result['file_info']
                    report.append(f"  - {result['function_name']}: {error_msg} "
                                f"(prompt saved to {file_info['prompt_path']})")
                else:
                    report.append(f"  - {result['function_name']}: {error_msg}")
        
        # Add token usage summary
        total_tokens = sum(
            r.get('usage', {}).get('total_tokens', 0) 
            for r in successful
        )
        if total_tokens > 0:
            report.extend(["", f"Total tokens used: {total_tokens}"])
        
        return '\n'.join(report)