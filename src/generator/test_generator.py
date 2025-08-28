"""
Test generator using LLM for Google Test + MockCpp generation
"""

import logging
import time
import concurrent.futures
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from src.utils.context_compressor import ContextCompressor
from src.utils.file_organizer import TestFileOrganizer
from src.utils.logging_utils import get_logger
from src.utils.prompt_templates import PromptTemplates
from src.utils.fixture_finder import FixtureFinder
from src.utils.test_aggregator import TestFileAggregator
from .llm_client import LLMClient
from .mock_llm_client import MockLLMClient

logger = get_logger(__name__)


class TestGenerator:
    """Generates tests using LLM with extracted context"""
    
    def __init__(self, llm_provider: str = "mock", api_key: str = None, 
                 base_url: str = None, model: str = None,
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.context_compressor = ContextCompressor()
        self.fixture_finder = FixtureFinder()
        self.aggregator = TestFileAggregator()
        
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
                model=model,
                max_retries=max_retries,
                retry_delay=retry_delay
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
            
            # Send to LLM with language information
            language = function_info.get('language', 'c')
            result = self.llm_client.generate_test(
                prompt=prompt,
                max_tokens=2500,
                temperature=0.3,
                language=language
            )
            
            if result['success']:
                logger.info(f"Successfully generated test for {function_info['name']}")
                logger.info(f"Tokens used: {result.get('usage', {})}")
                
                # Add metadata to result
                result['function_name'] = function_info['name']
                result['prompt_length'] = len(prompt)
                result['test_length'] = len(result['test_code'])
                result['prompt'] = prompt
                
            else:
                logger.error(f"Failed to generate test for {function_info['name']}: "
                           f"{result['error']}")
                result['prompt'] = prompt
            
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
                      project_config: Dict[str, Any],
                      max_workers: int = 3) -> List[Dict[str, Any]]:
        """Generate tests for multiple functions with organized output structure"""
        
        project_name = project_config.get("name", "unknown_project")
        output_dir = project_config.get("output_dir", "./generated_tests")
        unit_test_directory_path = project_config.get("unit_test_directory_path")
        
        # Create file organizer with timestamped directory
        file_organizer = TestFileOrganizer(output_dir)
        timestamped_dir = file_organizer.create_timestamped_directory(project_name)
        organized_organizer = TestFileOrganizer(timestamped_dir)
        
        # First phase: Generate all prompts and save them immediately
        logger.info("Phase 1: Generating and saving prompts for all functions...")
        prompts = []
        
        for func_data in functions_with_context:
            function_info = func_data['function']
            context = func_data['context']
            
            if not self._should_generate_test(function_info):
                logger.info(f"Skipping non-testable function: {function_info['name']}")
                continue
            
            # New logic for fixture finding and prompt generation
            # 1. Determine suite name and target file path
            source_file = Path(function_info.get('file', 'unknown'))
            suite_name = f"{source_file.stem.replace('.', '_')}Test"
            target_filepath = Path(timestamped_dir) / f"test_{source_file.stem}.cpp"

            # 2. Find existing fixture
            existing_fixture_code = None
            if unit_test_directory_path:
                logger.info(f"Searching for fixture '{suite_name}' in {unit_test_directory_path}")
                existing_fixture_code = self.fixture_finder.find_fixture_definition(
                    suite_name, unit_test_directory_path
                )
                if existing_fixture_code:
                    logger.info(f"Found existing fixture for {suite_name}")

            # 3. Generate prompt using the template directly
            compressed_context = self.context_compressor.compress_function_context(
                function_info, context
            )
            prompt = PromptTemplates.generate_test_prompt(
                compressed_context,
                existing_fixture_code=existing_fixture_code,
                suite_name=suite_name
            )
            
            # Save prompt immediately
            prompt_path = organized_organizer.save_prompt_only(function_info['name'], prompt)
            logger.info(f"Saved prompt for {function_info['name']} to {prompt_path}")
            
            prompts.append({
                'function_info': function_info,
                'context': context,
                'prompt': prompt,
                'compressed_context': compressed_context,
                'prompt_path': prompt_path,
                'target_filepath': str(target_filepath) # Pass target path for aggregation
            })
        
        logger.info(f"Generated and saved {len(prompts)} prompts for LLM processing")
        
        # Second phase: Process with LLM using concurrent execution
        logger.info(f"Phase 2: Processing {len(prompts)} functions with {max_workers} concurrent workers...")
        
        if max_workers > 1:
            # Concurrent processing
            results = self._process_concurrently(prompts, organized_organizer, max_workers)
        else:
            # Sequential processing (backward compatibility)
            results = self._process_sequentially(prompts, organized_organizer)
        
        # Generate README with generation info
        generation_info = {
            'timestamp': datetime.now().isoformat(),
            'project_name': project_name,
            'llm_provider': self.llm_client.provider,
            'model': getattr(self.llm_client, 'model', 'unknown'),
            'total_functions': len(functions_with_context),
            'successful': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']]),
            'concurrent_workers': max_workers if max_workers > 1 else 1
        }
        organized_organizer.generate_readme(generation_info)
        
        return results
    
    def _process_sequentially(self, prompts: List[Dict[str, Any]], 
                            organizer: TestFileOrganizer) -> List[Dict[str, Any]]:
        """Process prompts sequentially"""
        results = []
        
        for prompt_data in prompts:
            function_info = prompt_data['function_info']
            context = prompt_data['context']
            
            # Generate test
            result = self.generate_test(function_info, context)
            
            # Save results
            target_filepath = prompt_data['target_filepath']
            result = self._save_test_result(result, function_info, "", organizer, target_filepath)
            results.append(result)
            
            # Add small delay to avoid rate limiting
            time.sleep(1)
            
        return results
    
    def _process_concurrently(self, prompts: List[Dict[str, Any]], 
                             organizer: TestFileOrganizer, max_workers: int) -> List[Dict[str, Any]]:
        """Process prompts concurrently using thread pool"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_prompt = {
                executor.submit(self._process_single_function, prompt_data, organizer): prompt_data
                for prompt_data in prompts
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_prompt):
                prompt_data = future_to_prompt[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed: {prompt_data['function_info']['name']}")
                except Exception as e:
                    logger.error(f"Error processing {prompt_data['function_info']['name']}: {e}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'function_name': prompt_data['function_info']['name']
                    })
        
        return results
    
    def _process_single_function(self, prompt_data: Dict[str, Any], 
                               organizer: TestFileOrganizer) -> Dict[str, Any]:
        """Process a single function (used for concurrent execution)"""
        function_info = prompt_data['function_info']
        context = prompt_data['context']
        
        # Generate test
        result = self.generate_test(function_info, context)
        
        # Save results
        target_filepath = prompt_data['target_filepath']
        return self._save_test_result(result, function_info, "", organizer, target_filepath)
    
    def _save_test_result(self, result: Dict[str, Any], function_info: Dict[str, Any],
                         prompt: str, organizer: TestFileOrganizer, target_filepath: str) -> Dict[str, Any]:
        """Save test results and organize files"""
        if result['success']:
            # Aggregate the test code into the target file
            self.aggregator.aggregate(target_filepath, result['test_code'])
            logger.info(f"Aggregated test for {function_info['name']} into {target_filepath}")

            # Save prompt and raw response, but not the individual test file
            file_info = organizer.organize_test_output(
                test_code="", # Pass empty string to avoid creating individual test file
                function_name=function_info['name'],
                prompt=prompt,
                raw_response=result['test_code']
            )
            result['file_info'] = file_info
            result['output_path'] = target_filepath # Report the aggregated file path
            logger.info(f"Saved debug files for {function_info['name']}")
        else:
            # For failed generations, still save the prompt for debugging
            file_info = organizer.organize_test_output(
                test_code="",
                function_name=function_info['name'],
                prompt=prompt,
                raw_response=f"Generation failed: {result.get('error', 'Unknown error')}"
            )
            result['file_info'] = file_info
        
        return result
    
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
        ]
        
        return '\n'.join(report)