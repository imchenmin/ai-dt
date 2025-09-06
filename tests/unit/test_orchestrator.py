"""
Tests for test_generation.orchestrator module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.test_generation.orchestrator import TestGenerationOrchestrator
from src.test_generation.models import (
    GenerationTask,
    GenerationResult,
    TestGenerationConfig,
    AggregatedResult
)
from src.test_generation.components import (
    PromptGenerator,
    CoreTestGenerator,
    TestFileManager,
    TestResultAggregator
)
from src.test_generation.strategies import SequentialExecution, ConcurrentExecution
from src.llm.client import LLMClient


class TestTestGenerationOrchestrator:
    """Test cases for TestGenerationOrchestrator"""
    
    def create_sample_tasks(self) -> list:
        """Helper to create sample tasks"""
        return [
            GenerationTask(
                function_info={'name': f'func{i}', 'language': 'c'},
                context={'includes': [], 'macros': []},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(3)
        ]
    
    def create_sample_config(self) -> TestGenerationConfig:
        """Helper to create sample config"""
        return TestGenerationConfig(
            project_name='test_project',
            output_dir='/output',
            max_workers=2,
            save_prompts=True,
            aggregate_tests=True,
            generate_readme=True
        )
    
    def test_init_with_required_dependencies(self):
        """Test orchestrator initialization with required dependencies"""
        mock_client = Mock(spec=LLMClient)
        
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        assert orchestrator.llm_client == mock_client
        assert isinstance(orchestrator.prompt_generator, PromptGenerator)
        assert isinstance(orchestrator.test_generator, CoreTestGenerator)
        assert orchestrator.file_manager is None  # Not provided
        assert isinstance(orchestrator.result_aggregator, TestResultAggregator)
        assert orchestrator.execution_strategy is None  # Not provided
    
    def test_init_with_all_dependencies(self):
        """Test orchestrator initialization with all dependencies"""
        mock_client = Mock(spec=LLMClient)
        mock_prompt_gen = Mock(spec=PromptGenerator)
        mock_test_gen = Mock(spec=CoreTestGenerator)
        mock_file_mgr = Mock(spec=TestFileManager)
        mock_aggregator = Mock(spec=TestResultAggregator)
        mock_strategy = Mock(spec=SequentialExecution)
        
        orchestrator = TestGenerationOrchestrator(
            llm_client=mock_client,
            prompt_generator=mock_prompt_gen,
            test_generator=mock_test_gen,
            file_manager=mock_file_mgr,
            result_aggregator=mock_aggregator,
            execution_strategy=mock_strategy
        )
        
        assert orchestrator.llm_client == mock_client
        assert orchestrator.prompt_generator == mock_prompt_gen
        assert orchestrator.test_generator == mock_test_gen
        assert orchestrator.file_manager == mock_file_mgr
        assert orchestrator.result_aggregator == mock_aggregator
        assert orchestrator.execution_strategy == mock_strategy
    
    @patch('src.test_generation.orchestrator.TestFileOrganizer')
    @patch('src.test_generation.orchestrator.ExecutionStrategyFactory')
    def test_setup_components_with_output_dir(self, mock_strategy_factory, mock_organizer_class):
        """Test component setup with output directory"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        mock_strategy = Mock()
        mock_strategy_factory.create_strategy.return_value = mock_strategy
        
        config = self.create_sample_config()
        orchestrator._setup_components(config)
        
        assert orchestrator.file_manager is not None
        assert orchestrator.execution_strategy == mock_strategy
        mock_strategy_factory.create_strategy.assert_called_once()
    
    def test_prepare_tasks(self):
        """Test task preparation phase"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        # Mock prompt generator
        orchestrator.prompt_generator = Mock()
        orchestrator.prompt_generator.prepare_task.side_effect = lambda func, ctx, unit_path, existing_tests_ctx=None: GenerationTask(
            function_info=func,
            context=ctx,
            target_filepath=f"test_{func['name']}.cpp",
            suite_name=f"{func['name']}Test"
        )
        
        functions_with_context = [
            {
                'function': {'name': 'test_func1'},
                'context': {'includes': []}
            },
            {
                'function': {'name': 'test_func2'},
                'context': {'includes': []}
            }
        ]
        
        config = self.create_sample_config()
        tasks = orchestrator._prepare_tasks(functions_with_context, config)
        
        assert len(tasks) == 2
        assert all(isinstance(task, GenerationTask) for task in tasks)
        assert tasks[0].function_info['name'] == 'test_func1'
        assert tasks[1].function_info['name'] == 'test_func2'
        
        # Verify paths are updated with output directory
        for task in tasks:
            assert str(Path(config.output_dir)) in task.target_filepath
    
    def test_save_all_prompts(self):
        """Test prompt saving phase"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        # Mock components
        orchestrator.prompt_generator = Mock()
        orchestrator.prompt_generator.generate_prompt.side_effect = lambda task: f"prompt for {task.function_name}"
        
        orchestrator.file_manager = Mock()
        
        tasks = self.create_sample_tasks()
        orchestrator._save_all_prompts(tasks)
        
        # Verify prompt generation and saving
        assert orchestrator.prompt_generator.generate_prompt.call_count == 3
        assert orchestrator.file_manager.save_prompt.call_count == 3
        
        # Verify prompts are stored in tasks
        for task in tasks:
            assert hasattr(task, 'prompt')
            assert task.prompt == f"prompt for {task.function_name}"
    
    def test_save_all_prompts_no_file_manager(self):
        """Test prompt saving when file manager is not configured"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        orchestrator.prompt_generator = Mock()
        orchestrator.file_manager = None  # No file manager
        
        tasks = self.create_sample_tasks()
        
        # Should not raise exception, just log warning
        orchestrator._save_all_prompts(tasks)
        
        # Prompt generation should not be called without file manager
        orchestrator.prompt_generator.generate_prompt.assert_not_called()
    
    def test_execute_generation(self):
        """Test test generation execution phase"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        # Mock components
        orchestrator.prompt_generator = Mock()
        orchestrator.prompt_generator.generate_prompt.side_effect = lambda task: f"prompt for {task.function_name}"
        
        orchestrator.test_generator = Mock()
        orchestrator.test_generator.generate_test.side_effect = lambda task, prompt: GenerationResult(
            task=task,
            success=True,
            test_code=f"TEST({task.suite_name}, {task.function_name}) {{}}",
            prompt=prompt
        )
        
        orchestrator.file_manager = Mock()
        orchestrator.file_manager.save_result.side_effect = lambda result: result
        
        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.execute.side_effect = lambda tasks, processor: [processor(task) for task in tasks]
        orchestrator.execution_strategy = mock_strategy
        
        tasks = self.create_sample_tasks()
        config = self.create_sample_config()
        
        results = orchestrator._execute_generation(tasks, config)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all("TEST(" in r.test_code for r in results)
        
        mock_strategy.execute.assert_called_once()
        assert orchestrator.file_manager.save_result.call_count == 3
    
    def test_post_process_results(self):
        """Test results post-processing phase"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        orchestrator.file_manager = Mock()
        orchestrator.file_manager.save_result.side_effect = lambda result: result
        
        tasks = self.create_sample_tasks()
        results = [
            GenerationResult(task=task, success=True, test_code=f"test for {task.function_name}")
            for task in tasks
        ]
        
        processed_results = orchestrator._post_process_results(results)
        
        assert len(processed_results) == 3
        assert orchestrator.file_manager.save_result.call_count == 3
    
    def test_post_process_results_no_file_manager(self):
        """Test results post-processing without file manager"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        orchestrator.file_manager = None
        
        tasks = self.create_sample_tasks()
        results = [
            GenerationResult(task=task, success=True, test_code=f"test for {task.function_name}")
            for task in tasks
        ]
        
        processed_results = orchestrator._post_process_results(results)
        
        # Should return original results unchanged
        assert processed_results == results
    
    @patch('src.test_generation.orchestrator.datetime')
    def test_generate_tests_complete_flow(self, mock_datetime):
        """Test complete test generation flow"""
        # Mock datetime for consistent timing
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 0, 30)
        mock_datetime.now.side_effect = [start_time, end_time]
        
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        # Mock all components
        orchestrator.prompt_generator = Mock()
        orchestrator.prompt_generator.prepare_task.side_effect = lambda func, ctx, unit_path, existing_tests_ctx=None: GenerationTask(
            function_info=func,
            context=ctx,
            target_filepath=f"test_{func['name']}.cpp",
            suite_name=f"{func['name']}Test"
        )
        orchestrator.prompt_generator.generate_prompt.side_effect = lambda task: f"prompt for {task.function_name}"
        
        orchestrator.test_generator = Mock()
        orchestrator.test_generator.generate_test.side_effect = lambda task, prompt: GenerationResult(
            task=task,
            success=True,
            test_code=f"TEST({task.suite_name}, {task.function_name}) {{}}",
            prompt=prompt
        )
        
        orchestrator.file_manager = Mock()
        orchestrator.file_manager.save_result.side_effect = lambda result: result
        
        orchestrator.result_aggregator = Mock()
        mock_aggregated = AggregatedResult(
            config=self.create_sample_config(),
            results=[]
        )
        orchestrator.result_aggregator.aggregate_results.return_value = mock_aggregated
        
        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.execute.side_effect = lambda tasks, processor: [processor(task) for task in tasks]
        orchestrator.execution_strategy = mock_strategy
        
        functions_with_context = [
            {
                'function': {'name': 'test_func1'},
                'context': {'includes': []}
            }
        ]
        
        config = self.create_sample_config()
        result = orchestrator.generate_tests(functions_with_context, config)
        
        assert isinstance(result, AggregatedResult)
        assert result.start_time == start_time
        assert result.end_time == end_time
        
        # Verify all phases were called
        orchestrator.prompt_generator.prepare_task.assert_called()
        orchestrator.prompt_generator.generate_prompt.assert_called()
        orchestrator.test_generator.generate_test.assert_called()
        orchestrator.file_manager.save_result.assert_called()
        orchestrator.result_aggregator.aggregate_results.assert_called()
        mock_strategy.execute.assert_called()
    
    def test_generate_readme(self):
        """Test README generation"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        mock_file_organizer = Mock()
        orchestrator.file_manager = Mock()
        orchestrator.file_manager.file_organizer = mock_file_organizer
        
        aggregated = AggregatedResult(
            config=self.create_sample_config(),
            results=[],
            generation_info={'project_name': 'test_project'}
        )
        
        orchestrator._generate_readme(aggregated)
        
        mock_file_organizer.generate_readme.assert_called_once_with(aggregated.generation_info)
    
    def test_generate_readme_no_file_manager(self):
        """Test README generation without file manager"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        orchestrator.file_manager = None
        
        aggregated = AggregatedResult(
            config=self.create_sample_config(),
            results=[]
        )
        
        # Should not raise exception
        orchestrator._generate_readme(aggregated)
    
    def test_generate_readme_exception_handling(self):
        """Test README generation with exception"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        mock_file_organizer = Mock()
        mock_file_organizer.generate_readme.side_effect = Exception("README generation failed")
        orchestrator.file_manager = Mock()
        orchestrator.file_manager.file_organizer = mock_file_organizer
        
        aggregated = AggregatedResult(
            config=self.create_sample_config(),
            results=[]
        )
        
        # Should not raise exception, just log error
        orchestrator._generate_readme(aggregated)
    
    def test_should_generate_test(self):
        """Test function filtering logic"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        # Should generate test for normal function
        normal_function = {'name': 'normal_func', 'is_static': False, 'language': 'c'}
        assert orchestrator._should_generate_test(normal_function) is True
        
        # Should not generate test for static function (any language)
        static_function = {'name': 'static_func', 'is_static': True, 'language': 'c'}
        assert orchestrator._should_generate_test(static_function) is False
        
        # Should not generate test for static C++ function either (based on current logic)
        static_cpp_function = {'name': 'static_func', 'is_static': True, 'language': 'cpp'}
        assert orchestrator._should_generate_test(static_cpp_function) is False
    
    def test_set_llm_client(self):
        """Test LLM client setter"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        new_client = Mock(spec=LLMClient)
        orchestrator.set_llm_client(new_client)
        
        assert orchestrator.llm_client == new_client
        assert orchestrator.test_generator.llm_client == new_client
    
    def test_set_execution_strategy(self):
        """Test execution strategy setter"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        new_strategy = Mock(spec=ConcurrentExecution)
        new_strategy.strategy_name = "test_strategy"
        
        orchestrator.set_execution_strategy(new_strategy)
        
        assert orchestrator.execution_strategy == new_strategy
    
    def test_get_summary_report(self):
        """Test summary report generation"""
        mock_client = Mock(spec=LLMClient)
        orchestrator = TestGenerationOrchestrator(llm_client=mock_client)
        
        orchestrator.result_aggregator = Mock()
        orchestrator.result_aggregator.generate_summary_report.return_value = "Test summary report"
        
        aggregated = AggregatedResult(
            config=self.create_sample_config(),
            results=[]
        )
        
        report = orchestrator.get_summary_report(aggregated)
        
        assert report == "Test summary report"
        orchestrator.result_aggregator.generate_summary_report.assert_called_once_with(aggregated)