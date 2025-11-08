"""
Core components for test generation with single responsibilities
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .models import GenerationTask, GenerationResult, AggregatedResult
from src.utils.context_compressor import ContextCompressor
# from src.utils.prompt_templates import PromptTemplates  # Moved to avoid circular import
from src.utils.fixture_finder import FixtureFinder
from src.utils.file_organizer import TestFileOrganizer
from src.utils.test_aggregator import TestFileAggregator
from src.llm.client import LLMClient
from src.llm.models import GenerationRequest
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class PromptGenerator:
    """Component responsible for generating prompts from function context"""
    
    def __init__(self, context_compressor: Optional[ContextCompressor] = None,
                 fixture_finder: Optional[FixtureFinder] = None):
        self.context_compressor = context_compressor or ContextCompressor()
        self.fixture_finder = fixture_finder or FixtureFinder()
    
    def generate_prompt(self, task: GenerationTask) -> str:
        """Generate prompt for a test generation task"""
        # Compress context for LLM
        compressed_context = self.context_compressor.compress_function_context(
            task.function_info, task.context
        )
        
        # Generate prompt using the template
        # Delayed import to avoid circular import
        from src.utils.prompt_templates import PromptTemplates
        prompt = PromptTemplates.generate_test_prompt(
            compressed_context,
            existing_fixture_code=task.existing_fixture_code,
            suite_name=task.suite_name,
            existing_tests_context=task.existing_tests_context
        )
        
        logger.debug(f"Generated prompt for {task.function_name} ({len(prompt)} characters)")
        return prompt
    
    def prepare_task(self, function_info: Dict[str, Any], context: Dict[str, Any],
                    unit_test_directory_path: Optional[str] = None,
                    existing_tests_context: Optional[Dict[str, Any]] = None) -> GenerationTask:
        """Prepare a complete generation task from function info and context"""
        # Determine suite name and target file path
        source_file = Path(function_info.get('file', 'unknown'))
        suite_name = f"{source_file.stem.replace('.', '_')}Test"
        target_filepath = f"test_{source_file.stem}.cpp"
        
        # Find existing fixture if available
        existing_fixture_code = None
        if unit_test_directory_path:
            logger.debug(f"Searching for fixture '{suite_name}' in {unit_test_directory_path}")
            existing_fixture_code = self.fixture_finder.find_fixture_definition(
                suite_name, unit_test_directory_path
            )
            if existing_fixture_code:
                logger.debug(f"Found existing fixture for {suite_name}")
        
        return GenerationTask(
            function_info=function_info,
            context=context,
            target_filepath=target_filepath,
            suite_name=suite_name,
            existing_fixture_code=existing_fixture_code,
            existing_tests_context=existing_tests_context
        )


class CoreTestGenerator:
    """Core component responsible for generating test code using LLM"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def validate_test_code(self, test_code: str) -> tuple[bool, str]:
        """
        Validate generated test code for common issues.

        Args:
            test_code: Generated test code

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not test_code:
            return False, "Empty test code"

        # Check for markdown markers that might have been missed
        if '```' in test_code:
            return False, "Test code contains markdown markers"

        # Check for required elements based on language
        required_elements = ['#include', 'TEST_', 'EXPECT_']
        missing_elements = [elem for elem in required_elements if elem not in test_code]

        if missing_elements:
            return False, f"Missing required elements: {', '.join(missing_elements)}"

        # Check for basic C++ test structure if it's a C++ test
        if '#include <gtest/gtest.h>' in test_code or '#include "gtest/gtest.h"' in test_code:
            # Check for proper test class structure
            if 'class ' not in test_code and 'TEST(' not in test_code:
                return False, "Missing test class or test function structure"

        # Check for mock usage if mockcpp is included
        if 'mockcpp' in test_code.lower():
            if 'MOCKER' not in test_code and 'MOCKCPP' not in test_code:
                logger.warning("MockCpp included but no mock setup found")

        return True, ""
    
    def generate_test_with_retry(self, task: GenerationTask, prompt: str, max_retries: int = 3) -> GenerationResult:
        """Generate test code with retry mechanism"""
        last_error = None

        for attempt in range(max_retries):
            try:
                result = self.generate_test(task, prompt)

                # If successful and validation passes, return
                if result.success:
                    return result

                # If generation failed, log and retry
                last_error = result.error or "Unknown error"
                logger.warning(f"Generation failed for {task.function_name}, attempt {attempt + 1}/{max_retries}: {last_error}")

                # Don't retry immediately for certain errors
                if "quota" in str(last_error).lower() or "rate limit" in str(last_error).lower():
                    logger.error(f"Rate limit or quota error for {task.function_name}, not retrying")
                    break

            except Exception as e:
                last_error = str(e)
                logger.error(f"Generation error for {task.function_name}, attempt {attempt + 1}/{max_retries}: {e}")

            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1, 2, 4 seconds
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        # All retries failed
        logger.error(f"Failed to generate test for {task.function_name} after {max_retries} attempts")
        return GenerationResult(
            task=task,
            success=False,
            error=f"Failed after {max_retries} attempts. Last error: {last_error}",
            prompt=prompt
        )

    def generate_test(self, task: GenerationTask, prompt: str) -> GenerationResult:
        """Generate test code for a single task"""
        try:
            # Send to LLM with language information
            llm_result = self.llm_client.generate_test(
                prompt=prompt,
                max_tokens=2500,
                temperature=0.3,
                language=task.language
            )
            
            # Create result object
            test_code = llm_result.get('test_code', '')

            # Validate the generated test code
            if test_code:
                is_valid, validation_error = self.validate_test_code(test_code)
                if not is_valid:
                    logger.error(f"Generated test validation failed for {task.function_name}: {validation_error}")
                    # Don't fail completely, but log the issue
                    logger.warning(f"Proceeding with potentially invalid test code for {task.function_name}")

            result = GenerationResult(
                task=task,
                success=llm_result['success'],
                test_code=test_code,
                prompt=prompt,
                error=llm_result.get('error'),
                usage=llm_result.get('usage', {}),
                model=llm_result.get('model', ''),
                prompt_length=len(prompt),
                test_length=len(test_code)
            )

            if result.success:
                logger.debug(f"Successfully generated test for {task.function_name}")
                logger.debug(f"Tokens used: {result.usage}")
            else:
                logger.error(f"Failed to generate test for {task.function_name}: {result.error}")

            return result
            
        except Exception as e:
            logger.error(f"Error generating test for {task.function_name}: {e}")
            return GenerationResult(
                task=task,
                success=False,
                error=str(e),
                prompt=prompt
            )


class TestFileManager:
    """Component responsible for managing test file operations"""
    
    def __init__(self, file_organizer: Optional[TestFileOrganizer] = None,
                 aggregator: Optional[TestFileAggregator] = None):
        self.file_organizer = file_organizer
        self.aggregator = aggregator or TestFileAggregator()
    
    def save_prompt(self, function_name: str, prompt: str) -> str:
        """Save prompt to file and return path"""
        if not self.file_organizer:
            raise ValueError("File organizer not configured")
        
        prompt_path = self.file_organizer.save_prompt_only(function_name, prompt)
        logger.debug(f"Saved prompt for {function_name} to {prompt_path}")
        return prompt_path
    
    def save_result(self, result: GenerationResult) -> GenerationResult:
        """Save test result and update file information"""
        if not self.file_organizer:
            logger.warning("File organizer not configured, skipping file save")
            return result
        
        if result.success:
            # Aggregate the test code into the target file
            self.aggregator.aggregate(result.task.target_filepath, result.test_code)
            logger.debug(f"Aggregated test for {result.function_name} into {result.task.target_filepath}")
            result.output_path = result.task.target_filepath
            
            # Save debug files (prompt, raw response, and pure test code)
            file_info = self.file_organizer.organize_test_output(
                test_code=result.test_code,  # Save the actual test code
                function_name=result.function_name,
                prompt=result.prompt,
                raw_response=result.test_code
            )
            result.file_info = file_info
            logger.debug(f"Saved debug files for {result.function_name}")
        else:
            # For failed generations, still save the prompt for debugging
            file_info = self.file_organizer.organize_test_output(
                test_code="",
                function_name=result.function_name,
                prompt=result.prompt,
                raw_response=f"Generation failed: {result.error or 'Unknown error'}"
            )
            result.file_info = file_info
        
        return result


class TestResultAggregator:
    """Component responsible for aggregating and analyzing test generation results"""
    
    def __init__(self):
        pass
    
    def aggregate_results(self, results: List[GenerationResult], 
                         config: Any) -> AggregatedResult:
        """Aggregate test generation results"""
        from .models import TestGenerationConfig, AggregatedResult
        from datetime import datetime
        
        # Convert config if needed
        if not isinstance(config, TestGenerationConfig):
            config = TestGenerationConfig(
                project_name=getattr(config, 'project_name', 'unknown'),
                output_dir=getattr(config, 'output_dir', './output'),
                max_workers=getattr(config, 'max_workers', 3)
            )
        
        # Create aggregated result
        aggregated = AggregatedResult(
            config=config,
            results=results,
            end_time=datetime.now()
        )
        
        # Generate summary information
        aggregated.generation_info = {
            'timestamp': datetime.now().isoformat(),
            'project_name': config.project_name,
            'total_functions': len(results),
            'successful': aggregated.successful_count,
            'failed': aggregated.failed_count,
            'success_rate': aggregated.success_rate,
            'duration': aggregated.duration
        }
        
        return aggregated
    
    def generate_summary_report(self, aggregated: AggregatedResult) -> str:
        """Generate summary report of test generation"""
        report_lines = [
            "=== Test Generation Summary ===",
            f"Project: {aggregated.config.project_name}",
            f"Total functions processed: {aggregated.total_count}",
            f"Successful generations: {aggregated.successful_count}",
            f"Failed generations: {aggregated.failed_count}",
            f"Success rate: {aggregated.success_rate:.1%}",
        ]
        
        if aggregated.duration:
            report_lines.append(f"Duration: {aggregated.duration:.2f} seconds")
        
        if aggregated.failed_count > 0:
            report_lines.append("\nFailed functions:")
            for result in aggregated.results:
                if not result.success:
                    report_lines.append(f"  • {result.function_name}: {result.error}")
        
        return '\n'.join(report_lines)


class ComponentFactory:
    """Factory for creating test generation components"""
    
    @staticmethod
    def create_prompt_generator(**kwargs) -> PromptGenerator:
        """Create prompt generator with dependencies"""
        return PromptGenerator(
            context_compressor=kwargs.get('context_compressor'),
            fixture_finder=kwargs.get('fixture_finder')
        )
    
    @staticmethod
    def create_test_generator(llm_client: LLMClient) -> CoreTestGenerator:
        """Create core test generator"""
        return CoreTestGenerator(llm_client)
    
    @staticmethod
    def create_file_manager(output_dir: str, **kwargs) -> TestFileManager:
        """Create test file manager"""
        file_organizer = TestFileOrganizer(output_dir) if output_dir else None
        return TestFileManager(
            file_organizer=file_organizer,
            aggregator=kwargs.get('aggregator')
        )
    
    @staticmethod
    def create_result_aggregator() -> TestResultAggregator:
        """Create result aggregator"""
        return TestResultAggregator()