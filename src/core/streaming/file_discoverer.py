"""
File discoverer component for streaming test generation.

This component is responsible for discovering C/C++ files from compilation units
and creating stream packets for function processing. It follows Clean Code principles
with single responsibility, dependency injection, and immutability.
"""

import asyncio
import time
from typing import AsyncIterator, List, Set, Dict, Any, Optional
from pathlib import Path

from .interfaces import (
    StreamProcessor, StreamPacket, StreamStage, StreamingConfiguration,
    StreamObserver
)
from src.utils.logging_utils import get_logger


class FileDiscoveryFilter:
    """Filter for determining which files should be processed"""

    def __init__(
        self,
        include_extensions: Optional[Set[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size_mb: Optional[int] = None
    ):
        """
        Initialize file discovery filter

        Args:
            include_extensions: File extensions to include (default: C/C++ files)
            exclude_patterns: Path patterns to exclude
            max_file_size_mb: Maximum file size in MB
        """
        self.include_extensions = include_extensions or {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx'}
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size_mb = max_file_size_mb

    def should_process_file(self, file_path: str) -> bool:
        """
        Determine if a file should be processed based on filters

        Args:
            file_path: Path to the file

        Returns:
            True if file should be processed, False otherwise
        """
        path = Path(file_path)

        # Check extension
        if path.suffix.lower() not in self.include_extensions:
            return False

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in str(path):
                return False

        # Check file size if specified
        if self.max_file_size_mb and path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                return False

        return True


class FileDiscoverer(StreamProcessor):
    """
    Stream processor for discovering C/C++ files from compilation units.

    This processor takes compilation unit data and emits individual file packets
    for downstream function processing. It handles filtering and prioritization
    while maintaining immutability of input data.
    """

    def __init__(
        self,
        config: StreamingConfiguration,
        filter: Optional[FileDiscoveryFilter] = None,
        observers: Optional[List[StreamObserver]] = None
    ):
        """
        Initialize file discoverer

        Args:
            config: Streaming configuration
            filter: Optional file filter (default: C/C++ files only)
            observers: Optional observers for monitoring
        """
        self.config = config
        self.filter = filter or FileDiscoveryFilter()
        self.observers = observers or []
        self.logger = get_logger(__name__)
        self._discovered_count = 0
        self._start_time = time.time()

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        """
        Process compilation units and emit file packets

        Args:
            packet: Input packet containing compilation units

        Yields:
            StreamPacket: One packet per discovered file
        """
        if packet.stage != StreamStage.FILE_DISCOVERY:
            self.logger.warning(f"Unexpected packet stage: {packet.stage}")
            return

        try:
            compilation_units = packet.data.get("compilation_units", [])
            if not compilation_units:
                self.logger.info("No compilation units found in packet")
                return

            self.logger.info(f"Processing {len(compilation_units)} compilation units")

            # Process files concurrently if configured
            if self.config.max_concurrent_files > 1:
                async for file_packet in self._process_concurrent(compilation_units, packet):
                    yield file_packet
            else:
                async for file_packet in self._process_sequential(compilation_units, packet):
                    yield file_packet

        except Exception as e:
            self.logger.error(f"Error in file discovery: {e}")
            await self._notify_observers_error(packet, e)
            raise

    async def _process_sequential(
        self,
        compilation_units: List[Dict[str, Any]],
        source_packet: StreamPacket
    ) -> AsyncIterator[StreamPacket]:
        """Process compilation units sequentially"""
        for unit in compilation_units:
            async for file_packet in self._process_compilation_unit(unit, source_packet):
                yield file_packet

    async def _process_concurrent(
        self,
        compilation_units: List[Dict[str, Any]],
        source_packet: StreamPacket
    ) -> AsyncIterator[StreamPacket]:
        """Process compilation units concurrently"""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_files)

        async def process_unit(unit: Dict[str, Any]) -> List[StreamPacket]:
            async with semaphore:
                packets = []
                async for packet in self._process_compilation_unit(unit, source_packet):
                    packets.append(packet)
                return packets

        # Create tasks for all compilation units
        tasks = [process_unit(unit) for unit in compilation_units]

        # Wait for all tasks and yield results as they complete
        for completed_task in asyncio.as_completed(tasks):
            try:
                packets = await completed_task
                for packet in packets:
                    yield packet
            except Exception as e:
                self.logger.error(f"Error processing compilation unit concurrently: {e}")

    async def _process_compilation_unit(
        self,
        compilation_unit: Dict[str, Any],
        source_packet: StreamPacket
    ) -> AsyncIterator[StreamPacket]:
        """
        Process a single compilation unit

        Args:
            compilation_unit: Compilation unit data
            source_packet: Original packet for context

        Yields:
            StreamPacket: File packet if file should be processed
        """
        file_path = compilation_unit.get("file")
        if not file_path:
            return

        # Apply filter
        if not self.filter.should_process_file(file_path):
            self.logger.debug(f"Skipping filtered file: {file_path}")
            return

        start_time = time.time()
        self._discovered_count += 1

        # Create immutable file packet
        file_packet = StreamPacket(
            stage=StreamStage.FUNCTION_PROCESSING,
            data={
                "file_path": file_path,
                "compile_args": compilation_unit.get("arguments", []),
                "compilation_unit": compilation_unit,
                "source_packet_id": source_packet.packet_id,
                "discovery_sequence": self._discovered_count
            },
            timestamp=start_time,
            packet_id=f"{source_packet.packet_id}-file-{self._discovered_count}"
        )

        # Notify observers
        processing_time = time.time() - start_time
        await self._notify_observers_packet_processed(file_packet, processing_time)

        self.logger.debug(f"Discovered file: {file_path} (#{self._discovered_count})")
        yield file_packet

    async def cleanup(self):
        """Cleanup resources and log final statistics"""
        duration = time.time() - self._start_time
        self.logger.info(
            f"File discovery completed: {self._discovered_count} files "
            f"in {duration:.2f}s ({self._discovered_count/duration:.2f} files/sec)"
        )

        # No specific cleanup needed for this component
        pass

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
    def discovered_count(self) -> int:
        """Get the number of files discovered so far"""
        return self._discovered_count