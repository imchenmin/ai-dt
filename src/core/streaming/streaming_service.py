"""
Streaming test generation service - high-level interface for streaming architecture.

This service provides a clean, user-friendly interface for using the streaming
test generation architecture while maintaining compatibility with existing systems.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncIterator

from .interfaces import StreamingConfiguration, StreamObserver, StreamMetrics
from .pipeline_orchestrator import StreamingPipelineOrchestrator
from src.llm.client import LLMClient
from src.llm.factory import LLMProviderFactory
from src.utils.logging_utils import get_logger
from src.parser.compilation_db import CompilationDatabaseParser
from src.utils.config_manager import ConfigManager


class StreamingProgressObserver(StreamObserver):
    """Observer for collecting and reporting streaming progress"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.start_time = time.time()
        self.packets_processed = []
        self.errors = []
        self.stage_changes = []
        self._last_progress_time = time.time()
        self._progress_interval = 5.0  # Report progress every 5 seconds

    async def on_packet_processed(self, packet, processing_time: float) -> None:
        """Track packet processing"""
        self.packets_processed.append((packet, processing_time))

        # Periodic progress reporting
        current_time = time.time()
        if current_time - self._last_progress_time >= self._progress_interval:
            await self._report_progress()
            self._last_progress_time = current_time

    async def on_error_occurred(self, packet, error: Exception) -> None:
        """Track errors"""
        self.errors.append((packet, error))
        self.logger.warning(f"Streaming error: {error}")

    async def on_stage_changed(self, stage, metrics: StreamMetrics) -> None:
        """Track stage changes"""
        self.stage_changes.append((stage, metrics))
        self.logger.info(f"Pipeline stage: {stage.value}")

    async def _report_progress(self) -> None:
        """Report current progress"""
        elapsed = time.time() - self.start_time
        total_processed = len(self.packets_processed)
        successful = len([p for p in self.packets_processed if hasattr(p[0], 'data')])

        self.logger.info(
            f"Progress: {total_processed} packets processed, "
            f"{successful} successful, {len(self.errors)} errors, "
            f"elapsed: {elapsed:.1f}s"
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        elapsed = time.time() - self.start_time
        successful = len(self.packets_processed) - len(self.errors)

        return {
            "elapsed_time": elapsed,
            "total_packets": len(self.packets_processed),
            "successful_packets": successful,
            "error_count": len(self.errors),
            "throughput": len(self.packets_processed) / max(elapsed, 1),
            "success_rate": successful / max(len(self.packets_processed), 1),
            "stage_changes": len(self.stage_changes)
        }


class StreamingTestGenerationService:
    """
    High-level service for streaming test generation.

    This service provides a simplified interface for using the streaming architecture
    while handling the complexity of pipeline setup, configuration, and monitoring.
    """

    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 config_manager: Optional[ConfigManager] = None):
        """
        Initialize streaming service

        Args:
            llm_client: Optional LLM client (will be created if not provided)
            config_manager: Optional config manager (will be created if not provided)
        """
        self.llm_client = llm_client
        self.config_manager = config_manager or ConfigManager()
        self.logger = get_logger(__name__)
        self._orchestrator = None

    async def generate_tests_streaming(
        self,
        project_path: str,
        compile_commands_path: str,
        output_dir: str,
        config: Optional[Dict[str, Any]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        observers: Optional[List[StreamObserver]] = None,
        progress_callback: Optional[callable] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate tests using streaming architecture

        Args:
            project_path: Path to the project directory
            compile_commands_path: Path to compile_commands.json
            output_dir: Output directory for generated tests
            config: Optional streaming configuration
            include_patterns: Optional file patterns to include
            exclude_patterns: Optional file patterns to exclude
            observers: Optional observers for monitoring
            progress_callback: Optional callback for progress updates

        Yields:
            Dict containing generation result information
        """
        self.logger.info(f"Starting streaming test generation for: {project_path}")

        # Setup LLM client if not provided
        if not self.llm_client:
            self.llm_client = await self._create_llm_client()

        # Setup streaming configuration
        streaming_config = self._create_streaming_config(config)

        # Setup observers
        progress_observer = StreamingProgressObserver()
        all_observers = [progress_observer]
        if observers:
            all_observers.extend(observers)

        # Parse compilation database
        compilation_units = await self._parse_compilation_database(
            compile_commands_path, include_patterns, exclude_patterns
        )

        if not compilation_units:
            self.logger.warning("No compilation units found")
            return

        self.logger.info(f"Found {len(compilation_units)} compilation units")

        # Create and configure orchestrator
        self._orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=output_dir,
            observers=all_observers,
            llm_client=self.llm_client,
            project_root=project_path
        )

        try:
            # Execute streaming pipeline
            async for result_packet in self._orchestrator.execute_streaming(
                compilation_units, all_observers
            ):
                # Convert packet to result dictionary
                result_dict = self._packet_to_result_dict(result_packet)

                # Call progress callback if provided
                if progress_callback:
                    await self._call_progress_callback(progress_callback, result_dict, progress_observer.get_summary())

                yield result_dict

        finally:
            # Cleanup
            if self._orchestrator:
                await self._orchestrator.shutdown()

            # Log final summary
            summary = progress_observer.get_summary()
            self.logger.info(
                f"Streaming test generation completed: "
                f"{summary['successful_packets']}/{summary['total_packets']} successful, "
                f"duration: {summary['elapsed_time']:.2f}s, "
                f"throughput: {summary['throughput']:.2f} packets/sec"
            )

    async def _create_llm_client(self) -> LLMClient:
        """Create LLM client from configuration"""
        try:
            # Get default LLM provider from config
            llm_provider = self.config_manager.get_default_llm_provider()
            api_key = self.config_manager.get_api_key_for_provider(llm_provider)

            if not api_key:
                self.logger.warning(f"No API key found for {llm_provider}, using mock client")
                return LLMClient.create_mock_client()

            # Create real client
            llm_config = self.config_manager.get_llm_provider_config(llm_provider)
            return LLMClient.create_from_config(llm_config)

        except Exception as e:
            self.logger.error(f"Failed to create LLM client: {e}")
            self.logger.info("Using mock client for testing")
            return LLMClient.create_mock_client()

    def _create_streaming_config(self, config: Optional[Dict[str, Any]]) -> StreamingConfiguration:
        """Create streaming configuration from dict"""
        if config is None:
            config = {}

        return StreamingConfiguration(
            max_queue_size=config.get('max_queue_size', 100),
            max_concurrent_files=config.get('max_concurrent_files', 3),
            max_concurrent_functions=config.get('max_concurrent_functions', 5),
            max_concurrent_llm_calls=config.get('max_concurrent_llm_calls', 3),
            enable_prioritization=config.get('enable_prioritization', True),
            timeout_seconds=config.get('timeout_seconds', 300),
            retry_attempts=config.get('retry_attempts', 3),
            enable_metrics=config.get('enable_metrics', True)
        )

    async def _parse_compilation_database(
        self,
        compile_commands_path: str,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Parse compilation database with optional filtering"""
        try:
            parser = CompilationDatabaseParser(compile_commands_path)
            compilation_units = parser.parse(
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
            return compilation_units
        except Exception as e:
            self.logger.error(f"Failed to parse compilation database: {e}")
            return []

    def _packet_to_result_dict(self, packet) -> Dict[str, Any]:
        """Convert stream packet to result dictionary for backward compatibility"""
        if packet.stage.value == 'completed':
            generation_result = packet.data.get('generation_result')
            if generation_result:
                return {
                    'success': generation_result.success,
                    'function_name': generation_result.function_name,
                    'test_code': generation_result.test_code,
                    'test_length': generation_result.test_length,
                    'model': generation_result.model,
                    'output_path': packet.data.get('output_path'),
                    'processing_time': packet.timestamp,
                    'packet_id': packet.packet_id
                }

        # Return generic packet information
        return {
            'stage': packet.stage.value,
            'packet_id': packet.packet_id,
            'timestamp': packet.timestamp,
            'data': packet.data
        }

    async def _call_progress_callback(
        self,
        callback: callable,
        result: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> None:
        """Call progress callback safely"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(result, summary)
            else:
                callback(result, summary)
        except Exception as e:
            self.logger.error(f"Error in progress callback: {e}")

    async def shutdown(self):
        """Gracefully shutdown the service"""
        if self._orchestrator:
            await self._orchestrator.shutdown()
            self._orchestrator = None

    @classmethod
    def create_for_project(cls, project_config: Dict[str, Any]) -> 'StreamingTestGenerationService':
        """
        Create service instance for a specific project configuration

        Args:
            project_config: Project configuration dictionary

        Returns:
            Configured StreamingTestGenerationService instance
        """
        # Extract LLM configuration
        llm_provider = project_config.get('llm_provider', 'deepseek')

        # Create config manager
        config_manager = ConfigManager()

        # Create LLM client
        try:
            api_key = config_manager.get_api_key_for_provider(llm_provider)
            if api_key:
                llm_config = config_manager.get_llm_provider_config(llm_provider)
                llm_client = LLMClient.create_from_config(llm_config)
            else:
                llm_client = LLMClient.create_mock_client()
        except Exception:
            llm_client = LLMClient.create_mock_client()

        return cls(llm_client=llm_client, config_manager=config_manager)