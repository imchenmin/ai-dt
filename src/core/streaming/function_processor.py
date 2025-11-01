"""
Function processor component for streaming test generation.

This component is responsible for extracting functions from C/C++ files and creating
function stream packets for LLM processing. It integrates with the existing analyzer
components while providing streaming capabilities.
"""

import asyncio
import time
from typing import AsyncIterator, List, Dict, Any, Optional, Set
from pathlib import Path

from .interfaces import (
    StreamProcessor, StreamPacket, StreamStage, StreamingConfiguration,
    FunctionStreamData, StreamObserver
)
from src.utils.logging_utils import get_logger
from src.utils.libclang_config import ensure_libclang_configured
from src.analyzer.clang_analyzer import ClangAnalyzer
from src.analyzer.function_analyzer import FunctionAnalyzer


class FunctionProcessingFilter:
    """Filter for determining which functions should be processed"""

    def __init__(
        self,
        skip_static: bool = True,
        skip_test_functions: bool = True,
        min_complexity: int = 0,
        max_complexity: Optional[int] = None,
        name_patterns: Optional[Set[str]] = None
    ):
        """
        Initialize function processing filter

        Args:
            skip_static: Skip static functions
            skip_test_functions: Skip functions with test-related names
            min_complexity: Minimum function complexity (parameter count)
            max_complexity: Maximum function complexity
            name_patterns: Specific function name patterns to include
        """
        self.skip_static = skip_static
        self.skip_test_functions = skip_test_functions
        self.min_complexity = min_complexity
        self.max_complexity = max_complexity
        self.name_patterns = name_patterns or set()

    def should_process_function(self, function_info: Dict[str, Any]) -> bool:
        """
        Determine if a function should be processed based on filters

        Args:
            function_info: Function information dictionary

        Returns:
            True if function should be processed, False otherwise
        """
        function_name = function_info.get("name", "")

        # Skip static functions if configured
        if self.skip_static and function_info.get("is_static", False):
            return False

        # Skip test functions if configured
        if self.skip_test_functions and self._is_test_function(function_name):
            return False

        # Check complexity
        param_count = len(function_info.get("parameters", []))
        if param_count < self.min_complexity:
            return False

        if self.max_complexity and param_count > self.max_complexity:
            return False

        # Check name patterns if specified
        if self.name_patterns and not any(pattern in function_name for pattern in self.name_patterns):
            return False

        return True

    def _is_test_function(self, function_name: str) -> bool:
        """Check if function name indicates it's a test function"""
        test_patterns = ["test_", "Test", "_test", "TEST", "spec", "Spec"]
        return any(pattern in function_name for pattern in test_patterns)


class FunctionProcessor(StreamProcessor):
    """
    Stream processor for extracting functions from C/C++ files.

    This processor takes file packets and emits individual function packets
    for downstream LLM processing. It integrates with existing analysis components
    while maintaining streaming semantics and immutability.
    """

    def __init__(
        self,
        config: StreamingConfiguration,
        filter: Optional[FunctionProcessingFilter] = None,
        observers: Optional[List[StreamObserver]] = None,
        project_root: Optional[str] = None
    ):
        """
        Initialize function processor

        Args:
            config: Streaming configuration
            filter: Optional function filter
            observers: Optional observers for monitoring
            project_root: Project root path for resolving relative paths
        """
        self.config = config
        self.filter = filter or FunctionProcessingFilter()
        self.observers = observers or []
        self.project_root = project_root or "."
        self.logger = get_logger(__name__)
        self._processed_count = 0
        self._start_time = time.time()

        # Initialize analyzer components
        ensure_libclang_configured()
        self.clang_analyzer = ClangAnalyzer()
        self.function_analyzer = FunctionAnalyzer(self.project_root)

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        """
        Process file packet and emit function packets

        Args:
            packet: Input packet containing file information

        Yields:
            StreamPacket: One packet per discovered function
        """
        if packet.stage != StreamStage.FUNCTION_PROCESSING:
            self.logger.warning(f"Unexpected packet stage: {packet.stage}")
            return

        try:
            file_path = packet.data.get("file_path")
            compile_args = packet.data.get("compile_args", [])

            if not file_path:
                self.logger.warning("No file_path found in packet")
                return

            # Resolve full path
            full_path = self._resolve_file_path(file_path)
            if not Path(full_path).exists():
                self.logger.warning(f"File not found: {full_path}")
                return

            self.logger.debug(f"Processing functions in: {full_path}")

            # Extract functions using existing analyzer
            functions = await self._extract_functions_async(full_path, compile_args)

            # Apply filtering and create packets
            filtered_functions = [
                func for func in functions
                if self.filter.should_process_function(func)
            ]

            self.logger.info(f"Found {len(functions)} functions, {len(filtered_functions)} after filtering")

            # Process functions with concurrency control if configured
            if self.config.max_concurrent_functions > 1 and len(filtered_functions) > 1:
                async for func_packet in self._process_functions_concurrent(
                    filtered_functions, full_path, compile_args, packet
                ):
                    yield func_packet
            else:
                async for func_packet in self._process_functions_sequential(
                    filtered_functions, full_path, compile_args, packet
                ):
                    yield func_packet

        except Exception as e:
            self.logger.error(f"Error processing functions for {packet.data.get('file_path', 'unknown')}: {e}")
            await self._notify_observers_error(packet, e)
            raise

    async def _extract_functions_async(self, file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """
        Extract functions from file asynchronously

        Args:
            file_path: Path to the file
            compile_args: Compilation arguments

        Returns:
            List of function information dictionaries
        """
        # Run blocking clang analysis in thread pool
        loop = asyncio.get_event_loop()
        try:
            functions = await loop.run_in_executor(
                None,
                self.function_analyzer.analyze_file,
                file_path,
                compile_args
            )
            return functions
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return []

    async def _process_functions_sequential(
        self,
        functions: List[Dict[str, Any]],
        file_path: str,
        compile_args: List[str],
        source_packet: StreamPacket
    ) -> AsyncIterator[StreamPacket]:
        """Process functions sequentially"""
        for func in functions:
            async for func_packet in self._create_function_packet(
                func, file_path, compile_args, source_packet
            ):
                yield func_packet

    async def _process_functions_concurrent(
        self,
        functions: List[Dict[str, Any]],
        file_path: str,
        compile_args: List[str],
        source_packet: StreamPacket
    ) -> AsyncIterator[StreamPacket]:
        """Process functions concurrently"""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_functions)

        async def process_function(func: Dict[str, Any]) -> List[StreamPacket]:
            async with semaphore:
                packets = []
                async for packet in self._create_function_packet(
                    func, file_path, compile_args, source_packet
                ):
                    packets.append(packet)
                return packets

        # Create tasks for all functions
        tasks = [process_function(func) for func in functions]

        # Wait for all tasks and yield results as they complete
        for completed_task in asyncio.as_completed(tasks):
            try:
                packets = await completed_task
                for packet in packets:
                    yield packet
            except Exception as e:
                self.logger.error(f"Error processing function concurrently: {e}")

    async def _create_function_packet(
        self,
        function_info: Dict[str, Any],
        file_path: str,
        compile_args: List[str],
        source_packet: StreamPacket
    ) -> AsyncIterator[StreamPacket]:
        """
        Create a function packet for LLM processing

        Args:
            function_info: Function information dictionary
            file_path: Source file path
            compile_args: Compilation arguments
            source_packet: Original packet for context

        Yields:
            StreamPacket: Function packet for LLM processing
        """
        start_time = time.time()
        self._processed_count += 1

        # Calculate priority based on function complexity
        priority = self._calculate_function_priority(function_info)

        # Create immutable function stream data
        function_data = FunctionStreamData(
            file_path=file_path,
            function_info=function_info,
            compile_args=compile_args,
            priority=priority
        )

        # Create function packet
        function_packet = StreamPacket(
            stage=StreamStage.LLM_PROCESSING,
            data={
                "function_stream_data": function_data,
                "source_packet_id": source_packet.packet_id,
                "processing_sequence": self._processed_count
            },
            timestamp=start_time,
            packet_id=f"{source_packet.packet_id}-func-{function_info.get('name', 'unknown')}-{self._processed_count}"
        )

        # Notify observers
        processing_time = time.time() - start_time
        await self._notify_observers_packet_processed(function_packet, processing_time)

        self.logger.debug(
            f"Processed function: {function_info.get('name')} "
            f"(priority: {priority}, #{self._processed_count})"
        )
        yield function_packet

    def _calculate_function_priority(self, function_info: Dict[str, Any]) -> int:
        """
        Calculate processing priority for a function

        Args:
            function_info: Function information dictionary

        Returns:
            Integer priority (higher = more complex)
        """
        # Simple heuristic based on parameter count and function characteristics
        param_count = len(function_info.get("parameters", []))

        # Increase priority for complex functions
        if function_info.get("return_type") == "void*":
            param_count += 1
        if "pointer" in function_info.get("return_type", "").lower():
            param_count += 1

        return min(param_count, 10)  # Cap at 10

    def _resolve_file_path(self, file_path: str) -> str:
        """Resolve file path relative to project root"""
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(self.project_root) / path
        return str(path.resolve())

    async def cleanup(self):
        """Cleanup resources and log final statistics"""
        duration = time.time() - self._start_time
        self.logger.info(
            f"Function processing completed: {self._processed_count} functions "
            f"in {duration:.2f}s ({self._processed_count/duration:.2f} functions/sec)"
        )

        # Cleanup analyzer resources
        if hasattr(self.clang_analyzer, 'cleanup'):
            await self.clang_analyzer.cleanup()

    async def _notify_observers_packet_processed(self, packet: StreamPacket, processing_time: float):
        """Notify all observers of packet processing"""
        for observer in self.observers:
            try:
                await observer.on_packet_processed(packet, processing_time)
            except Exception as e:
                self.logger.error(f"Error notifying observer: {e}")

    async def _notify_observers_error(self, packet: StreamPacket, error: Exception):
        """Notify all observers of error occurrence"""
        for observer in self.observers:
            try:
                await observer.on_error_occurred(packet, error)
            except Exception as e:
                self.logger.error(f"Error notifying observer of error: {e}")

    @property
    def processed_count(self) -> int:
        """Get the number of functions processed so far"""
        return self._processed_count