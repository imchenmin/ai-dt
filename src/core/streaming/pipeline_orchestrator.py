"""
Streaming pipeline orchestrator for test generation.

This component coordinates all streaming processors and manages the overall
pipeline execution flow. It handles stage transitions, error recovery,
metrics collection, and graceful shutdown.
"""

import asyncio
import time
from typing import AsyncIterator, List, Dict, Any, Optional, Set
from dataclasses import dataclass
from contextlib import asynccontextmanager

from .interfaces import (
    StreamStage, StreamPacket, StreamingPipelineOrchestrator,
    StreamingConfiguration, StreamObserver, StreamMetrics,
    StreamProcessor, StreamQueue
)
from src.utils.logging_utils import get_logger
from .file_discoverer import FileDiscoverer, FileDiscoveryFilter
from .function_processor import FunctionProcessor, FunctionProcessingFilter
from .llm_processor import LLMProcessor, LLMRateLimiter
from .result_collector import ResultCollector, TestSuiteAggregator


@dataclass
class PipelineStatistics:
    """Statistics for pipeline execution"""
    start_time: float
    packets_processed: int = 0
    packets_by_stage: Dict[StreamStage, int] = None
    errors_count: int = 0
    last_activity_time: float = 0

    def __post_init__(self):
        if self.packets_by_stage is None:
            self.packets_by_stage = {stage: 0 for stage in StreamStage}


class AsyncStreamQueue:
    """Async implementation of StreamQueue interface"""

    def __init__(self, name: str, max_size: int = 0):
        self.name = name
        self.max_size = max_size
        self._queue = asyncio.Queue(maxsize=max_size)
        self._closed = False

    async def put(self, packet: StreamPacket) -> None:
        if self._closed:
            raise RuntimeError(f"Queue {self.name} is closed")
        await self._queue.put(packet)

    async def get(self) -> StreamPacket:
        return await self._queue.get()

    async def size(self) -> int:
        return self._queue.qsize()

    async def close(self) -> None:
        self._closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class StreamingPipelineOrchestrator:
    """
    Orchestrates the entire streaming test generation pipeline.

    This class coordinates all streaming processors, manages stage transitions,
    handles error recovery, and provides comprehensive monitoring capabilities.
    """

    def __init__(
        self,
        config: StreamingConfiguration,
        output_dir: str,
        observers: Optional[List[StreamObserver]] = None,
        llm_client=None,
        project_root: str = "."
    ):
        """
        Initialize streaming pipeline orchestrator

        Args:
            config: Streaming configuration
            output_dir: Directory for output files
            observers: Optional observers for monitoring
            llm_client: Optional LLM client
            project_root: Project root path
        """
        self.config = config
        self.output_dir = output_dir
        self.observers = observers or []
        self.project_root = project_root
        self.logger = get_logger(__name__)

        # Validate configuration
        config.validate()

        # Initialize statistics
        self.statistics = PipelineStatistics(start_time=time.time())
        self.is_running = False
        self.is_shutdown = False

        # Initialize processors
        self._initialize_processors(llm_client)

        # Initialize queues for stage communication
        self._initialize_queues()

        # Setup cancellation handling
        self._cancellation_event = asyncio.Event()

    def _initialize_processors(self, llm_client) -> None:
        """Initialize all streaming processors"""
        # File discoverer
        self.file_discoverer = FileDiscoverer(
            config=self.config,
            filter=FileDiscoveryFilter(),
            observers=self.observers
        )

        # Function processor
        self.function_processor = FunctionProcessor(
            config=self.config,
            filter=FunctionProcessingFilter(),
            observers=self.observers,
            project_root=self.project_root
        )

        # LLM processor
        self.llm_processor = LLMProcessor(
            config=self.config,
            llm_client=llm_client,
            observers=self.observers
        )

        # Result collector
        self.result_collector = ResultCollector(
            config=self.config,
            output_dir=self.output_dir,
            observers=self.observers
        )

    def _initialize_queues(self) -> None:
        """Initialize communication queues between stages"""
        self.file_discovery_queue = AsyncStreamQueue(
            "file_discovery", self.config.max_queue_size
        )
        self.function_processing_queue = AsyncStreamQueue(
            "function_processing", self.config.max_queue_size
        )
        self.llm_processing_queue = AsyncStreamQueue(
            "llm_processing", self.config.max_queue_size
        )
        self.result_collection_queue = AsyncStreamQueue(
            "result_collection", self.config.max_queue_size
        )

    async def execute_streaming(
        self,
        compilation_units: List[Dict[str, Any]],
        observers: Optional[List[StreamObserver]] = None
    ) -> AsyncIterator[StreamPacket]:
        """
        Execute streaming test generation pipeline

        Args:
            compilation_units: List of compilation units to process
            observers: Optional additional observers

        Yields:
            StreamPacket: Result packets as they become available
        """
        if self.is_running:
            raise RuntimeError("Pipeline is already running")

        if self.is_shutdown:
            raise RuntimeError("Pipeline has been shutdown")

        self.is_running = True
        all_observers = (self.observers + (observers or []))

        try:
            self.logger.info(f"Starting streaming pipeline for {len(compilation_units)} compilation units")

            # Start stage workers
            stage_tasks = await self._start_stage_workers()

            # Create initial packet and start flow
            initial_packet = StreamPacket(
                stage=StreamStage.FILE_DISCOVERY,
                data={"compilation_units": compilation_units},
                timestamp=time.time(),
                packet_id="pipeline-start"
            )

            # Submit initial packet to file discovery
            await self.file_discovery_queue.put(initial_packet)

            # Monitor and yield results
            async for result_packet in self.monitor_pipeline_results():
                yield result_packet

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            await self._notify_observers_error(None, e)
            raise
        finally:
            self.is_running = False
            await self._shutdown_stage_workers(stage_tasks)

    async def _start_stage_workers(self) -> List[asyncio.Task]:
        """Start worker tasks for each pipeline stage"""
        tasks = []

        # File discovery worker
        tasks.append(asyncio.create_task(
            self._file_discovery_worker()
        ))

        # Function processing workers
        for i in range(self.config.max_concurrent_functions):
            tasks.append(asyncio.create_task(
                self._function_processing_worker(f"func-worker-{i}")
            ))

        # LLM processing workers
        for i in range(self.config.max_concurrent_llm_calls):
            tasks.append(asyncio.create_task(
                self._llm_processing_worker(f"llm-worker-{i}")
            ))

        # Result collection worker
        tasks.append(asyncio.create_task(
            self._result_collection_worker()
        ))

        return tasks

    async def _file_discovery_worker(self) -> None:
        """Worker for file discovery stage"""
        try:
            while not self._cancellation_event.is_set():
                try:
                    packet = await asyncio.wait_for(
                        self.file_discovery_queue.get(),
                        timeout=1.0
                    )

                    async for result_packet in self.file_discoverer.process(packet):
                        await self.function_processing_queue.put(result_packet)
                        await self._update_statistics(packet)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in file discovery worker: {e}")
                    await self._notify_observers_error(packet, e)

        except asyncio.CancelledError:
            self.logger.info("File discovery worker cancelled")

    async def _function_processing_worker(self, worker_name: str) -> None:
        """Worker for function processing stage"""
        try:
            while not self._cancellation_event.is_set():
                try:
                    packet = await asyncio.wait_for(
                        self.function_processing_queue.get(),
                        timeout=1.0
                    )

                    async for result_packet in self.function_processor.process(packet):
                        await self.llm_processing_queue.put(result_packet)
                        await self._update_statistics(packet)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in function processing worker {worker_name}: {e}")
                    await self._notify_observers_error(packet, e)

        except asyncio.CancelledError:
            self.logger.info(f"Function processing worker {worker_name} cancelled")

    async def _llm_processing_worker(self, worker_name: str) -> None:
        """Worker for LLM processing stage"""
        try:
            while not self._cancellation_event.is_set():
                try:
                    packet = await asyncio.wait_for(
                        self.llm_processing_queue.get(),
                        timeout=1.0
                    )

                    async for result_packet in self.llm_processor.process(packet):
                        await self.result_collection_queue.put(result_packet)
                        await self._update_statistics(packet)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in LLM processing worker {worker_name}: {e}")
                    await self._notify_observers_error(packet, e)

        except asyncio.CancelledError:
            self.logger.info(f"LLM processing worker {worker_name} cancelled")

    async def _result_collection_worker(self) -> None:
        """Worker for result collection stage"""
        try:
            while not self._cancellation_event.is_set():
                try:
                    packet = await asyncio.wait_for(
                        self.result_collection_queue.get(),
                        timeout=1.0
                    )

                    async for result_packet in self.result_collector.process(packet):
                        # This is the final stage - yield results to caller
                        await self._update_statistics(packet)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in result collection worker: {e}")
                    await self._notify_observers_error(packet, e)

        except asyncio.CancelledError:
            self.logger.info("Result collection worker cancelled")

    async def monitor_pipeline_results(self) -> AsyncIterator[StreamPacket]:
        """Monitor pipeline and yield final results"""
        last_activity = time.time()
        idle_timeout = 30.0  # 30 seconds of inactivity considered complete

        while not self._cancellation_event.is_set():
            try:
                # Check if all queues are empty and no recent activity
                current_time = time.time()
                time_since_last_activity = current_time - self.statistics.last_activity_time

                if (time_since_last_activity > idle_timeout and
                    await self._all_queues_empty()):
                    self.logger.info("Pipeline completed - all queues empty and idle timeout reached")
                    break

                # Yield any completed results from result collector
                # In a real implementation, this would interface with the result collector
                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in pipeline monitoring: {e}")
                break

    async def _monitor_pipeline_results(self) -> AsyncIterator[StreamPacket]:
        """Internal wrapper for pipeline monitoring"""
        async for packet in self.monitor_pipeline_results():
            yield packet

    async def _all_queues_empty(self) -> bool:
        """Check if all queues are empty"""
        return (
            await self.file_discovery_queue.size() == 0 and
            await self.function_processing_queue.size() == 0 and
            await self.llm_processing_queue.size() == 0 and
            await self.result_collection_queue.size() == 0
        )

    async def _update_statistics(self, packet: StreamPacket) -> None:
        """Update pipeline statistics"""
        self.statistics.packets_processed += 1
        self.statistics.packets_by_stage[packet.stage] += 1
        self.statistics.last_activity_time = time.time()

        # Notify observers of stage change if needed
        metrics = self._calculate_metrics()
        await self._notify_observers_stage_changed(packet.stage, metrics)

    def _calculate_metrics(self) -> StreamMetrics:
        """Calculate current pipeline metrics"""
        duration = time.time() - self.statistics.start_time
        throughput = self.statistics.packets_processed / max(duration, 1)

        return StreamMetrics(
            packets_processed=self.statistics.packets_processed,
            errors_count=self.statistics.errors_count,
            average_processing_time=duration / max(self.statistics.packets_processed, 1),
            current_throughput=throughput,
            memory_usage_mb=0  # Would be calculated in real implementation
        )

    async def _shutdown_stage_workers(self, tasks: List[asyncio.Task]) -> None:
        """Gracefully shutdown all stage workers"""
        self.logger.info("Shutting down pipeline stage workers")

        # Signal cancellation
        self._cancellation_event.set()

        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.info("All stage workers shutdown complete")

    async def shutdown(self) -> None:
        """Gracefully shutdown the streaming pipeline"""
        if self.is_shutdown:
            return

        self.logger.info("Shutting down streaming pipeline orchestrator")
        self.is_shutdown = True

        # Signal cancellation if running
        if self.is_running:
            self._cancellation_event.set()

        # Cleanup processors
        await self.file_discoverer.cleanup()
        await self.function_processor.cleanup()
        await self.llm_processor.cleanup()
        await self.result_collector.cleanup()

        # Close queues
        await self.file_discovery_queue.close()
        await self.function_processing_queue.close()
        await self.llm_processing_queue.close()
        await self.result_collection_queue.close()

        # Log final statistics
        duration = time.time() - self.statistics.start_time
        self.logger.info(
            f"Pipeline shutdown complete. Processed {self.statistics.packets_processed} packets "
            f"in {duration:.2f}s"
        )

    async def _notify_observers_packet_processed(self, packet: StreamPacket, processing_time: float):
        """Notify all observers of packet processing"""
        for observer in self.observers:
            try:
                await observer.on_packet_processed(packet, processing_time)
            except Exception as e:
                self.logger.error(f"Error notifying observer: {e}")

    async def _notify_observers_error(self, packet: Optional[StreamPacket], error: Exception):
        """Notify all observers of error occurrence"""
        self.statistics.errors_count += 1
        for observer in self.observers:
            try:
                if packet:
                    await observer.on_error_occurred(packet, error)
                else:
                    # Create dummy packet for error reporting
                    dummy_packet = StreamPacket(
                        stage=StreamStage.FILE_DISCOVERY,
                        data={},
                        timestamp=time.time(),
                        packet_id="error-packet"
                    )
                    await observer.on_error_occurred(dummy_packet, error)
            except Exception as e:
                self.logger.error(f"Error notifying observer of error: {e}")

    async def _notify_observers_stage_changed(self, stage: StreamStage, metrics: StreamMetrics):
        """Notify all observers of stage change"""
        for observer in self.observers:
            try:
                await observer.on_stage_changed(stage, metrics)
            except Exception as e:
                self.logger.error(f"Error notifying observer of stage change: {e}")

    @property
    def metrics_report(self) -> Dict[str, Any]:
        """Get comprehensive metrics report"""
        return {
            "statistics": {
                "packets_processed": self.statistics.packets_processed,
                "packets_by_stage": self.statistics.packets_by_stage,
                "errors_count": self.statistics.errors_count,
                "running_time": time.time() - self.statistics.start_time
            },
            "config": {
                "max_concurrent_files": self.config.max_concurrent_files,
                "max_concurrent_functions": self.config.max_concurrent_functions,
                "max_concurrent_llm_calls": self.config.max_concurrent_llm_calls,
                "max_queue_size": self.config.max_queue_size
            },
            "current_metrics": self._calculate_metrics()
        }