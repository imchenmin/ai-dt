"""
Execution strategies for test generation
"""

import time
import concurrent.futures
from abc import ABC, abstractmethod
from typing import List, Callable, Any
from datetime import datetime

from .models import GenerationTask, GenerationResult
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ExecutionStrategy(ABC):
    """Abstract base class for test generation execution strategies"""
    
    @abstractmethod
    def execute(self, tasks: List[GenerationTask], 
                processor: Callable[[GenerationTask], GenerationResult]) -> List[GenerationResult]:
        """Execute test generation tasks using the strategy"""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Get the strategy name"""
        pass


class SequentialExecution(ExecutionStrategy):
    """Sequential execution strategy - processes tasks one by one"""
    
    def __init__(self, delay_between_requests: float = 1.0):
        self.delay_between_requests = delay_between_requests
    
    @property
    def strategy_name(self) -> str:
        return "sequential"
    
    def execute(self, tasks: List[GenerationTask], 
                processor: Callable[[GenerationTask], GenerationResult]) -> List[GenerationResult]:
        """Execute tasks sequentially"""
        logger.info(f"Starting sequential execution of {len(tasks)} tasks")
        start_time = datetime.now()
        
        results = []
        
        for i, task in enumerate(tasks, 1):
            logger.info(f"Processing task {i}/{len(tasks)}: {task.function_name}")
            
            try:
                result = processor(task)
                results.append(result)
                
                if result.success:
                    logger.info(f"✓ Completed {task.function_name}")
                else:
                    logger.error(f"✗ Failed {task.function_name}: {result.error}")
                
            except Exception as e:
                logger.error(f"✗ Error processing {task.function_name}: {e}")
                results.append(GenerationResult(
                    task=task,
                    success=False,
                    error=str(e)
                ))
            
            # Add delay between requests (except for the last one)
            if i < len(tasks) and self.delay_between_requests > 0:
                time.sleep(self.delay_between_requests)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Sequential execution completed in {duration:.2f}s")
        
        return results


class ConcurrentExecution(ExecutionStrategy):
    """Concurrent execution strategy - processes tasks in parallel"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    @property
    def strategy_name(self) -> str:
        return f"concurrent_w{self.max_workers}"
    
    def execute(self, tasks: List[GenerationTask], 
                processor: Callable[[GenerationTask], GenerationResult]) -> List[GenerationResult]:
        """Execute tasks concurrently"""
        logger.info(f"Starting concurrent execution of {len(tasks)} tasks with {self.max_workers} workers")
        start_time = datetime.now()
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._safe_processor, task, processor): task
                for task in tasks
            }
            
            # Collect results as they complete
            completed = 0
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        logger.info(f"✓ Completed {task.function_name} ({completed}/{len(tasks)})")
                    else:
                        logger.error(f"✗ Failed {task.function_name}: {result.error} ({completed}/{len(tasks)})")
                        
                except Exception as e:
                    logger.error(f"✗ Unexpected error processing {task.function_name}: {e}")
                    results.append(GenerationResult(
                        task=task,
                        success=False,
                        error=f"Unexpected error: {str(e)}"
                    ))
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Concurrent execution completed in {duration:.2f}s")
        
        # Sort results to match original task order
        task_order = {id(task): i for i, task in enumerate(tasks)}
        results.sort(key=lambda r: task_order.get(id(r.task), len(tasks)))
        
        return results
    
    def _safe_processor(self, task: GenerationTask, 
                       processor: Callable[[GenerationTask], GenerationResult]) -> GenerationResult:
        """Safely process a task with error handling"""
        try:
            return processor(task)
        except Exception as e:
            logger.error(f"Error in safe processor for {task.function_name}: {e}")
            return GenerationResult(
                task=task,
                success=False,
                error=str(e)
            )


class AdaptiveExecution(ExecutionStrategy):
    """Adaptive execution strategy - adjusts based on success rate"""
    
    def __init__(self, initial_workers: int = 3, min_workers: int = 1, max_workers: int = 5):
        self.initial_workers = initial_workers
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = initial_workers
    
    @property
    def strategy_name(self) -> str:
        return f"adaptive_w{self.current_workers}"
    
    def execute(self, tasks: List[GenerationTask],
                processor: Callable[[GenerationTask], GenerationResult]) -> List[GenerationResult]:
        """Execute with adaptive worker count based on success rate"""
        logger.info(f"Starting adaptive execution of {len(tasks)} tasks")

        if len(tasks) <= 5:
            # For small task sets, use sequential execution
            sequential = SequentialExecution()
            return sequential.execute(tasks, processor)

        # Execute all tasks concurrently with current worker count
        concurrent = ConcurrentExecution(max_workers=self.current_workers)
        results = concurrent.execute(tasks, processor)

        # Adapt worker count for next execution
        success_rate = len([r for r in results if r.success]) / len(results)
        self._adapt_workers(success_rate)

        return results
    
    def _adapt_workers(self, success_rate: float) -> None:
        """Adapt worker count based on success rate"""
        if success_rate < 0.5:
            # Low success rate, reduce workers
            self.current_workers = max(self.min_workers, self.current_workers - 1)
            logger.info(f"Reduced workers to {self.current_workers} due to low success rate ({success_rate:.2f})")
        elif success_rate > 0.8:
            # High success rate, increase workers
            self.current_workers = min(self.max_workers, self.current_workers + 1)
            logger.info(f"Increased workers to {self.current_workers} due to high success rate ({success_rate:.2f})")


# Strategy factory
class ExecutionStrategyFactory:
    """Factory for creating execution strategies"""
    
    @staticmethod
    def create_strategy(strategy_name: str, **kwargs) -> ExecutionStrategy:
        """Create execution strategy by name"""
        if strategy_name == "sequential":
            return SequentialExecution(
                delay_between_requests=kwargs.get('delay_between_requests', 1.0)
            )
        elif strategy_name == "concurrent":
            return ConcurrentExecution(
                max_workers=kwargs.get('max_workers', 3)
            )
        elif strategy_name == "adaptive":
            return AdaptiveExecution(
                initial_workers=kwargs.get('initial_workers', 3),
                min_workers=kwargs.get('min_workers', 1),
                max_workers=kwargs.get('max_workers', 5)
            )
        else:
            raise ValueError(f"Unknown execution strategy: {strategy_name}")
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """Get list of available strategy names"""
        return ["sequential", "concurrent", "adaptive"]