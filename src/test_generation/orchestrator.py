"""
Test generation orchestrator - coordinates the entire test generation process
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import GenerationTask, GenerationResult, TestGenerationConfig, AggregatedResult
from .strategies import ExecutionStrategy, ExecutionStrategyFactory
from .components import PromptGenerator, CoreTestGenerator, TestFileManager, TestResultAggregator
from src.utils.file_organizer import TestFileOrganizer
from src.llm.client import LLMClient
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class TestGenerationOrchestrator:
    """
    Orchestrates the entire test generation process with proper separation of concerns
    
    This class coordinates between different components to perform test generation
    while maintaining clear separation of responsibilities.
    """
    
    def __init__(self, 
                 llm_client: LLMClient,
                 prompt_generator: Optional[PromptGenerator] = None,
                 test_generator: Optional[CoreTestGenerator] = None,
                 file_manager: Optional[TestFileManager] = None,
                 result_aggregator: Optional[TestResultAggregator] = None,
                 execution_strategy: Optional[ExecutionStrategy] = None):
        """Initialize orchestrator with components"""
        self.llm_client = llm_client
        self.prompt_generator = prompt_generator or PromptGenerator()
        self.test_generator = test_generator or CoreTestGenerator(llm_client)
        self.file_manager = file_manager
        self.result_aggregator = result_aggregator or TestResultAggregator()
        self.execution_strategy = execution_strategy
    
    def generate_tests(self, functions_with_context: List[Dict[str, Any]], 
                      config: TestGenerationConfig) -> AggregatedResult:
        """
        Generate tests for multiple functions with the configured strategy
        
        Args:
            functions_with_context: List of function data with context
            config: Test generation configuration
            
        Returns:
            Aggregated results of test generation
        """
        start_time = datetime.now()
        logger.info(f"Starting test generation for {len(functions_with_context)} functions")
        
        # Setup components based on configuration
        self._setup_components(config)
        
        # Phase 1: Prepare tasks and generate prompts
        tasks = self._prepare_tasks(functions_with_context, config)
        
        if config.save_prompts:
            self._save_all_prompts(tasks)
        
        # Phase 2: Execute test generation
        results = self._execute_generation(tasks, config)
        
        # Phase 3: Post-process results (if not already processed)
        if config.aggregate_tests and not self.file_manager:
            results = self._post_process_results(results)
        
        # Phase 4: Generate final aggregated result
        aggregated = self.result_aggregator.aggregate_results(results, config)
        aggregated.start_time = start_time
        aggregated.end_time = datetime.now()
        
        # Generate README if configured
        if config.generate_readme:
            self._generate_readme(aggregated)
        
        logger.info(f"Test generation completed in {aggregated.duration:.2f}s: "
                   f"{aggregated.successful_count}/{aggregated.total_count} successful")
        
        return aggregated
    
    def _setup_components(self, config: TestGenerationConfig) -> None:
        """Setup components based on configuration"""
        # Setup file manager if output directory is specified
        if config.output_dir and not self.file_manager:
            if config.timestamped_output:
                # Create timestamped directory
                file_organizer = TestFileOrganizer(config.output_dir)
                timestamped_dir = file_organizer.create_timestamped_directory(config.project_name)
                organized_organizer = TestFileOrganizer(timestamped_dir)
                config.output_dir = timestamped_dir  # Update config with actual directory
            else:
                organized_organizer = TestFileOrganizer(config.output_dir)
            
            from .components import ComponentFactory
            self.file_manager = ComponentFactory.create_file_manager(
                config.output_dir, 
                file_organizer=organized_organizer
            )
        
        # Setup execution strategy if not provided
        if not self.execution_strategy:
            self.execution_strategy = ExecutionStrategyFactory.create_strategy(
                config.execution_strategy,
                max_workers=config.max_workers,
                delay_between_requests=config.delay_between_requests
            )
    
    def _prepare_tasks(self, functions_with_context: List[Dict[str, Any]], 
                      config: TestGenerationConfig) -> List[GenerationTask]:
        """Prepare generation tasks from function data"""
        logger.info("Phase 1: Preparing generation tasks...")
        
        tasks = []
        for func_data in functions_with_context:
            function_info = func_data['function']
            context = func_data['context']
            existing_tests_context = func_data.get('existing_tests_context')
            
            if not self._should_generate_test(function_info):
                logger.info(f"Skipping non-testable function: {function_info['name']}")
                continue
            
            # Prepare task with fixture finding and existing tests context
            task = self.prompt_generator.prepare_task(
                function_info, 
                context, 
                config.unit_test_directory_path,
                existing_tests_context
            )
            
            # Update target filepath with output directory
            if config.output_dir:
                task.target_filepath = str(Path(config.output_dir) / task.target_filepath)
            
            tasks.append(task)
        
        logger.info(f"Prepared {len(tasks)} generation tasks")
        return tasks
    
    def _save_all_prompts(self, tasks: List[GenerationTask]) -> None:
        """Save all prompts for the tasks"""
        if not self.file_manager:
            logger.warning("File manager not configured, skipping prompt saving")
            return
        
        logger.info("Generating and saving prompts for all functions...")
        
        for task in tasks:
            prompt = self.prompt_generator.generate_prompt(task)
            task.prompt = prompt  # Store for later use
            self.file_manager.save_prompt(task.function_name, prompt)
        
        logger.info(f"Saved prompts for {len(tasks)} functions")
    
    def _execute_generation(self, tasks: List[GenerationTask], 
                           config: TestGenerationConfig) -> List[GenerationResult]:
        """Execute test generation using the configured strategy"""
        logger.info(f"Phase 2: Executing test generation with {self.execution_strategy.strategy_name} strategy")
        
        def process_task(task: GenerationTask) -> GenerationResult:
            """Process a single task"""
            # Generate prompt if not already done
            if not hasattr(task, 'prompt'):
                task.prompt = self.prompt_generator.generate_prompt(task)
            
            # Generate test code
            result = self.test_generator.generate_test(task, task.prompt)
            
            # Save result immediately if file manager is available
            if self.file_manager:
                result = self.file_manager.save_result(result)
            
            return result
        
        # Execute using strategy
        results = self.execution_strategy.execute(tasks, process_task)

        # Generate detailed statistics
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Log detailed statistics
        logger.info(f"Completed test generation: {len(successful_results)} successful, "
                   f"{len(failed_results)} failed")

        # Log failed function names
        if failed_results:
            failed_names = [r.task.function_name for r in failed_results]
            logger.warning(f"Failed to generate tests for: {', '.join(failed_names)}")

            # Group failures by error type
            error_groups = {}
            for r in failed_results:
                error = r.error or "Unknown error"
                error_key = error[:50]  # First 50 chars
                if error_key not in error_groups:
                    error_groups[error_key] = []
                error_groups[error_key].append(r.task.function_name)

            logger.info("Failure breakdown:")
            for error, functions in error_groups.items():
                logger.info(f"  - {error}: {len(functions)} function(s)")

        # Log token usage statistics
        if successful_results:
            total_tokens = sum(r.usage.get('total_tokens', 0) if r.usage else 0 for r in successful_results)
            avg_tokens = total_tokens / len(successful_results) if successful_results else 0
            logger.info(f"Token usage: Total={total_tokens}, Average per function={avg_tokens:.0f}")

        return results
    
    def _post_process_results(self, results: List[GenerationResult]) -> List[GenerationResult]:
        """Post-process results (save files, etc.)"""
        if not self.file_manager:
            return results
        
        logger.info("Phase 3: Post-processing results...")
        
        processed_results = []
        for result in results:
            processed_result = self.file_manager.save_result(result)
            processed_results.append(processed_result)
        
        return processed_results
    
    def _generate_readme(self, aggregated: AggregatedResult) -> None:
        """Generate README file with generation information"""
        if not self.file_manager or not self.file_manager.file_organizer:
            return
        
        try:
            self.file_manager.file_organizer.generate_readme(aggregated.generation_info)
            logger.info("Generated README file")
        except Exception as e:
            logger.error(f"Failed to generate README: {e}")
    
    def _should_generate_test(self, function_info: Dict[str, Any]) -> bool:
        """Determine if test should be generated for this function"""
        # Basic filtering - can be enhanced
        if function_info.get('is_static', False):
            return False
        
        if function_info.get('language') == 'c' and function_info.get('is_static', False):
            return False
        
        return True
    
    def set_llm_client(self, llm_client: LLMClient) -> None:
        """Set a new LLM client (useful for testing)"""
        self.llm_client = llm_client
        self.test_generator.llm_client = llm_client
    
    def set_execution_strategy(self, strategy: ExecutionStrategy) -> None:
        """Set a custom execution strategy"""
        self.execution_strategy = strategy
        logger.info(f"Set execution strategy: {strategy.strategy_name}")
    
    def get_summary_report(self, aggregated: AggregatedResult) -> str:
        """Get summary report of test generation"""
        return self.result_aggregator.generate_summary_report(aggregated)