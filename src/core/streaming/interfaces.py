"""
Core interfaces and abstractions for streaming test generation architecture.

This module defines the contracts for all streaming components following Clean Code principles
and Dependency Inversion patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio


class StreamStage(Enum):
    """Represents different stages in the streaming pipeline"""
    FILE_DISCOVERY = "file_discovery"
    FUNCTION_PROCESSING = "function_processing"
    LLM_PROCESSING = "llm_processing"
    RESULT_COLLECTION = "result_collection"
    COMPLETED = "completed"


@dataclass(frozen=True)
class StreamPacket:
    """Immutable data packet flowing through the streaming pipeline"""
    stage: StreamStage
    data: Dict[str, Any]
    timestamp: float
    packet_id: str

    def with_stage(self, new_stage: StreamStage) -> 'StreamPacket':
        """Create a new packet with different stage"""
        return StreamPacket(
            stage=new_stage,
            data=self.data,
            timestamp=self.timestamp,
            packet_id=self.packet_id
        )


@dataclass(frozen=True)
class FunctionStreamData:
    """Immutable function data for streaming processing"""
    file_path: str
    function_info: Dict[str, Any]
    compile_args: List[str]
    priority: int = 0

    def with_priority(self, priority: int) -> 'FunctionStreamData':
        """Create new data with different priority"""
        return FunctionStreamData(
            file_path=self.file_path,
            function_info=self.function_info,
            compile_args=self.compile_args,
            priority=priority
        )


@dataclass(frozen=True)
class StreamMetrics:
    """Immutable metrics for monitoring streaming performance"""
    packets_processed: int
    errors_count: int
    average_processing_time: float
    current_throughput: float
    memory_usage_mb: float


class StreamProcessor(ABC):
    """Abstract base class for all streaming processors"""

    @abstractmethod
    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        """
        Process a stream packet and yield zero or more output packets

        Args:
            packet: Input packet to process

        Yields:
            StreamPacket: Processed output packets
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources when processor is shutting down"""
        pass


class StreamObserver(ABC):
    """Abstract observer for monitoring stream processing"""

    @abstractmethod
    async def on_packet_processed(self, packet: StreamPacket, processing_time: float) -> None:
        """Called when a packet is processed"""
        pass

    @abstractmethod
    async def on_error_occurred(self, packet: StreamPacket, error: Exception) -> None:
        """Called when an error occurs during processing"""
        pass

    @abstractmethod
    async def on_stage_changed(self, stage: StreamStage, metrics: StreamMetrics) -> None:
        """Called when processing stage changes"""
        pass


class StreamQueue(ABC):
    """Abstract queue interface for streaming pipeline"""

    @abstractmethod
    async def put(self, packet: StreamPacket) -> None:
        """Put a packet into the queue"""
        pass

    @abstractmethod
    async def get(self) -> StreamPacket:
        """Get a packet from the queue"""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get current queue size"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the queue"""
        pass


class StreamingPipelineOrchestrator(ABC):
    """Abstract orchestrator for managing streaming pipeline"""

    @abstractmethod
    async def execute_streaming(
        self,
        compilation_units: List[Dict[str, Any]],
        observers: Optional[List[StreamObserver]] = None
    ) -> AsyncIterator[StreamPacket]:
        """
        Execute streaming test generation

        Args:
            compilation_units: List of compilation units to process
            observers: Optional observers for monitoring

        Yields:
            StreamPacket: Result packets as they become available
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the streaming pipeline"""
        pass


class StreamingConfiguration:
    """Configuration for streaming processing"""

    def __init__(
        self,
        max_queue_size: int = 100,
        max_concurrent_files: int = 3,
        max_concurrent_functions: int = 5,
        max_concurrent_llm_calls: int = 3,
        enable_prioritization: bool = True,
        timeout_seconds: int = 300,
        retry_attempts: int = 3,
        enable_metrics: bool = True
    ):
        self.max_queue_size = max_queue_size
        self.max_concurrent_files = max_concurrent_files
        self.max_concurrent_functions = max_concurrent_functions
        self.max_concurrent_llm_calls = max_concurrent_llm_calls
        self.enable_prioritization = enable_prioritization
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.enable_metrics = enable_metrics

    def validate(self) -> None:
        """Validate configuration parameters"""
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        if self.max_concurrent_files <= 0:
            raise ValueError("max_concurrent_files must be positive")
        if self.max_concurrent_functions <= 0:
            raise ValueError("max_concurrent_functions must be positive")
        if self.max_concurrent_llm_calls <= 0:
            raise ValueError("max_concurrent_llm_calls must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")


# Factory interface for creating streaming components
class StreamComponentFactory(ABC):
    """Factory interface for creating streaming components"""

    @abstractmethod
    def create_file_discoverer(self) -> StreamProcessor:
        """Create file discovery processor"""
        pass

    @abstractmethod
    def create_function_processor(self) -> StreamProcessor:
        """Create function processing processor"""
        pass

    @abstractmethod
    def create_llm_processor(self) -> StreamProcessor:
        """Create LLM processing processor"""
        pass

    @abstractmethod
    def create_result_collector(self) -> StreamProcessor:
        """Create result collection processor"""
        pass

    @abstractmethod
    def create_queue(self, name: str) -> StreamQueue:
        """Create a named queue"""
        pass

    @abstractmethod
    def create_orchestrator(self, config: StreamingConfiguration) -> StreamingPipelineOrchestrator:
        """Create pipeline orchestrator"""
        pass