"""
Tests for test_generation.strategies module
"""

import pytest
import time
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
from typing import List

from src.test_generation.strategies import (
    ExecutionStrategy,
    SequentialExecution,
    ConcurrentExecution,
    AdaptiveExecution,
    ExecutionStrategyFactory
)
from src.test_generation.models import GenerationTask, GenerationResult


class TestSequentialExecution:
    """Test cases for SequentialExecution strategy"""
    
    def test_init_default(self):
        """Test SequentialExecution initialization with default delay"""
        strategy = SequentialExecution()
        
        assert strategy.delay_between_requests == 1.0
        assert strategy.strategy_name == "sequential"
    
    def test_init_custom_delay(self):
        """Test SequentialExecution initialization with custom delay"""
        strategy = SequentialExecution(delay_between_requests=0.5)
        
        assert strategy.delay_between_requests == 0.5
    
    def test_execute_success(self):
        """Test successful sequential execution"""
        strategy = SequentialExecution(delay_between_requests=0.1)
        
        # Create test tasks
        tasks = [
            GenerationTask(
                function_info={'name': f'func{i}'},
                context={},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(3)
        ]
        
        # Mock processor that always succeeds
        def mock_processor(task: GenerationTask) -> GenerationResult:
            return GenerationResult(
                task=task,
                success=True,
                test_code=f'TEST({task.suite_name}, {task.function_name}) {{}}'
            )
        
        start_time = time.time()
        results = strategy.execute(tasks, mock_processor)
        execution_time = time.time() - start_time
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(task.function_name in r.test_code for r, task in zip(results, tasks))
        
        # Should take at least delay_between_requests * (num_tasks - 1)
        expected_min_time = strategy.delay_between_requests * (len(tasks) - 1)
        assert execution_time >= expected_min_time * 0.8  # Allow some tolerance
    
    def test_execute_with_failures(self):
        """Test sequential execution with some failures"""
        strategy = SequentialExecution(delay_between_requests=0.0)
        
        tasks = [
            GenerationTask(
                function_info={'name': f'func{i}'},
                context={},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(3)
        ]
        
        def mock_processor(task: GenerationTask) -> GenerationResult:
            if 'func1' in task.function_name:
                return GenerationResult(
                    task=task,
                    success=False,
                    error='Mock error'
                )
            else:
                return GenerationResult(
                    task=task,
                    success=True,
                    test_code=f'TEST({task.suite_name}, {task.function_name}) {{}}'
                )
        
        results = strategy.execute(tasks, mock_processor)
        
        assert len(results) == 3
        assert sum(r.success for r in results) == 2
        assert sum(not r.success for r in results) == 1
        
        failed_result = next(r for r in results if not r.success)
        assert failed_result.error == 'Mock error'
    
    def test_execute_with_exceptions(self):
        """Test sequential execution with processor exceptions"""
        strategy = SequentialExecution(delay_between_requests=0.0)
        
        tasks = [
            GenerationTask(
                function_info={'name': 'test_func'},
                context={},
                target_filepath='test.cpp',
                suite_name='Test'
            )
        ]
        
        def mock_processor(task: GenerationTask) -> GenerationResult:
            raise ValueError("Processor error")
        
        results = strategy.execute(tasks, mock_processor)
        
        assert len(results) == 1
        assert not results[0].success
        assert "Processor error" in results[0].error


class TestConcurrentExecution:
    """Test cases for ConcurrentExecution strategy"""
    
    def test_init_default(self):
        """Test ConcurrentExecution initialization with default workers"""
        strategy = ConcurrentExecution()
        
        assert strategy.max_workers == 3
        assert strategy.strategy_name == "concurrent_w3"
    
    def test_init_custom_workers(self):
        """Test ConcurrentExecution initialization with custom workers"""
        strategy = ConcurrentExecution(max_workers=5)
        
        assert strategy.max_workers == 5
        assert strategy.strategy_name == "concurrent_w5"
    
    def test_execute_success(self):
        """Test successful concurrent execution"""
        strategy = ConcurrentExecution(max_workers=2)
        
        tasks = [
            GenerationTask(
                function_info={'name': f'func{i}'},
                context={},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(4)
        ]
        
        def mock_processor(task: GenerationTask) -> GenerationResult:
            # Add small delay to simulate processing
            time.sleep(0.1)
            return GenerationResult(
                task=task,
                success=True,
                test_code=f'TEST({task.suite_name}, {task.function_name}) {{}}'
            )
        
        start_time = time.time()
        results = strategy.execute(tasks, mock_processor)
        execution_time = time.time() - start_time
        
        assert len(results) == 4
        assert all(r.success for r in results)
        
        # Concurrent execution should be faster than sequential
        # With 2 workers and 4 tasks (0.1s each), should take ~0.2s instead of 0.4s
        assert execution_time < 0.3  # Allow some tolerance
    
    def test_execute_maintains_order(self):
        """Test that concurrent execution maintains task order in results"""
        strategy = ConcurrentExecution(max_workers=3)
        
        tasks = [
            GenerationTask(
                function_info={'name': f'func{i}'},
                context={},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(5)
        ]
        
        def mock_processor(task: GenerationTask) -> GenerationResult:
            # Vary processing time to test ordering
            delay = 0.05 if 'func2' in task.function_name else 0.01
            time.sleep(delay)
            return GenerationResult(
                task=task,
                success=True,
                test_code=f'TEST({task.suite_name}, {task.function_name}) {{}}'
            )
        
        results = strategy.execute(tasks, mock_processor)
        
        # Results should be in the same order as tasks
        for i, (task, result) in enumerate(zip(tasks, results)):
            assert result.task.function_name == task.function_name
            assert f'func{i}' in result.task.function_name
    
    def test_safe_processor_exception_handling(self):
        """Test safe processor handles exceptions properly"""
        strategy = ConcurrentExecution(max_workers=2)
        
        task = GenerationTask(
            function_info={'name': 'test_func'},
            context={},
            target_filepath='test.cpp',
            suite_name='Test'
        )
        
        def failing_processor(task: GenerationTask) -> GenerationResult:
            raise RuntimeError("Processing failed")
        
        result = strategy._safe_processor(task, failing_processor)
        
        assert not result.success
        assert "Processing failed" in result.error
        assert result.task == task
    
    def test_execute_with_mixed_results(self):
        """Test concurrent execution with mixed success/failure"""
        strategy = ConcurrentExecution(max_workers=2)
        
        tasks = [
            GenerationTask(
                function_info={'name': f'func{i}'},
                context={},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(4)
        ]
        
        def mock_processor(task: GenerationTask) -> GenerationResult:
            if 'func1' in task.function_name or 'func3' in task.function_name:
                return GenerationResult(
                    task=task,
                    success=False,
                    error='Mock failure'
                )
            else:
                return GenerationResult(
                    task=task,
                    success=True,
                    test_code=f'TEST({task.suite_name}, {task.function_name}) {{}}'
                )
        
        results = strategy.execute(tasks, mock_processor)
        
        assert len(results) == 4
        assert sum(r.success for r in results) == 2
        assert sum(not r.success for r in results) == 2


class TestAdaptiveExecution:
    """Test cases for AdaptiveExecution strategy"""
    
    def test_init_default(self):
        """Test AdaptiveExecution initialization with defaults"""
        strategy = AdaptiveExecution()
        
        assert strategy.initial_workers == 3
        assert strategy.min_workers == 1
        assert strategy.max_workers == 5
        assert strategy.current_workers == 3
        assert strategy.strategy_name == "adaptive_w3"
    
    def test_init_custom_values(self):
        """Test AdaptiveExecution initialization with custom values"""
        strategy = AdaptiveExecution(
            initial_workers=2,
            min_workers=1,
            max_workers=4
        )
        
        assert strategy.initial_workers == 2
        assert strategy.min_workers == 1
        assert strategy.max_workers == 4
        assert strategy.current_workers == 2
    
    def test_execute_small_task_set(self):
        """Test adaptive execution falls back to sequential for small task sets"""
        strategy = AdaptiveExecution()
        
        tasks = [
            GenerationTask(
                function_info={'name': f'func{i}'},
                context={},
                target_filepath=f'test{i}.cpp',
                suite_name=f'Test{i}'
            )
            for i in range(3)  # Small task set
        ]
        
        def mock_processor(task: GenerationTask) -> GenerationResult:
            return GenerationResult(
                task=task,
                success=True,
                test_code=f'TEST({task.suite_name}, {task.function_name}) {{}}'
            )
        
        results = strategy.execute(tasks, mock_processor)
        
        assert len(results) == 3
        assert all(r.success for r in results)
    
    def test_adapt_workers_low_success_rate(self):
        """Test worker adaptation for low success rate"""
        strategy = AdaptiveExecution(initial_workers=3, min_workers=1)
        
        # Low success rate should reduce workers
        strategy._adapt_workers(0.3)
        assert strategy.current_workers == 2
        
        strategy._adapt_workers(0.4)
        assert strategy.current_workers == 1
        
        # Should not go below min_workers
        strategy._adapt_workers(0.2)
        assert strategy.current_workers == 1
    
    def test_adapt_workers_high_success_rate(self):
        """Test worker adaptation for high success rate"""
        strategy = AdaptiveExecution(initial_workers=3, max_workers=5)
        
        # High success rate should increase workers
        strategy._adapt_workers(0.9)
        assert strategy.current_workers == 4
        
        strategy._adapt_workers(0.95)
        assert strategy.current_workers == 5
        
        # Should not go above max_workers
        strategy._adapt_workers(0.8)
        assert strategy.current_workers == 5
    
    def test_adapt_workers_medium_success_rate(self):
        """Test worker adaptation for medium success rate"""
        strategy = AdaptiveExecution(initial_workers=3)
        
        # Medium success rates should not change worker count
        strategy._adapt_workers(0.6)
        assert strategy.current_workers == 3
        
        strategy._adapt_workers(0.7)
        assert strategy.current_workers == 3


class TestExecutionStrategyFactory:
    """Test cases for ExecutionStrategyFactory"""
    
    def test_create_sequential_strategy(self):
        """Test creating sequential strategy"""
        strategy = ExecutionStrategyFactory.create_strategy("sequential")
        
        assert isinstance(strategy, SequentialExecution)
        assert strategy.delay_between_requests == 1.0
    
    def test_create_sequential_strategy_with_params(self):
        """Test creating sequential strategy with parameters"""
        strategy = ExecutionStrategyFactory.create_strategy(
            "sequential",
            delay_between_requests=0.5
        )
        
        assert isinstance(strategy, SequentialExecution)
        assert strategy.delay_between_requests == 0.5
    
    def test_create_concurrent_strategy(self):
        """Test creating concurrent strategy"""
        strategy = ExecutionStrategyFactory.create_strategy("concurrent")
        
        assert isinstance(strategy, ConcurrentExecution)
        assert strategy.max_workers == 3
    
    def test_create_concurrent_strategy_with_params(self):
        """Test creating concurrent strategy with parameters"""
        strategy = ExecutionStrategyFactory.create_strategy(
            "concurrent",
            max_workers=5
        )
        
        assert isinstance(strategy, ConcurrentExecution)
        assert strategy.max_workers == 5
    
    def test_create_adaptive_strategy(self):
        """Test creating adaptive strategy"""
        strategy = ExecutionStrategyFactory.create_strategy("adaptive")
        
        assert isinstance(strategy, AdaptiveExecution)
        assert strategy.initial_workers == 3
        assert strategy.min_workers == 1
        assert strategy.max_workers == 5
    
    def test_create_adaptive_strategy_with_params(self):
        """Test creating adaptive strategy with parameters"""
        strategy = ExecutionStrategyFactory.create_strategy(
            "adaptive",
            initial_workers=2,
            min_workers=1,
            max_workers=4
        )
        
        assert isinstance(strategy, AdaptiveExecution)
        assert strategy.initial_workers == 2
        assert strategy.min_workers == 1
        assert strategy.max_workers == 4
    
    def test_create_unknown_strategy(self):
        """Test creating unknown strategy raises error"""
        with pytest.raises(ValueError, match="Unknown execution strategy: unknown"):
            ExecutionStrategyFactory.create_strategy("unknown")
    
    def test_get_available_strategies(self):
        """Test getting available strategy names"""
        strategies = ExecutionStrategyFactory.get_available_strategies()
        
        assert "sequential" in strategies
        assert "concurrent" in strategies
        assert "adaptive" in strategies
        assert len(strategies) == 3