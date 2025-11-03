"""
Streaming mode implementation for test generation.
"""

import asyncio
import time
from typing import List, Optional, Dict, Any, Callable

from src.core.streaming.streaming_service import StreamingTestGenerationService
from src.utils.logging_utils import get_logger
from src.utils.retry_utils import retry, LLM_RETRY_CONFIG, CircuitBreaker


logger = get_logger(__name__)


class StreamingModeHandler:
    """Handler for streaming test generation mode"""

    def __init__(self):
        self.service = None

    async def _setup_progress_callback(
        self,
        enable_progress: bool
    ) -> Optional[Callable]:
        """Setup progress callback if enabled"""
        if not enable_progress:
            return None

        def progress_callback(result, summary):
            logger.info(
                f"Progress: {summary['successful_packets']} completed, "
                f"throughput: {summary['throughput']:.2f} packets/sec"
            )

        return progress_callback

    async def _process_results(
        self,
        results_stream,
        start_time: float
    ) -> Dict[str, Any]:
        """Process and collect streaming results"""
        results = []

        async for result in results_stream:
            results.append(result)

            # Report first result time
            if len(results) == 1:
                first_result_time = time.time() - start_time
                logger.info(f"First result generated in {first_result_time:.2f}s")

        return results

    def _log_final_results(
        self,
        results: List[Dict[str, Any]],
        total_time: float
    ) -> None:
        """Log final generation results"""
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]

        logger.info(f"Streaming test generation completed in {total_time:.2f}s")
        logger.info(f"Results: {len(successful)} successful, {len(failed)} failed")

        if successful:
            logger.info("Successfully generated tests for:")
            for result in successful:
                function_name = result.get('function_name', 'unknown')
                logger.info(f"  • {function_name}")

        if failed:
            logger.warning("Failed to generate tests for:")
            for result in failed:
                function_name = result.get('function_name', 'unknown')
                error = result.get('error', 'Unknown error')
                logger.warning(f"  • {function_name}: {error}")

    @CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
    @retry(config=LLM_RETRY_CONFIG)
    async def run_streaming_mode(
        self,
        project_path: str,
        output_dir: str,
        compile_commands: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_concurrent: int = 3,
        enable_progress: bool = False,
        **config_overrides
    ) -> None:
        """
        Run streaming test generation mode

        Args:
            project_path: Path to the project
            output_dir: Output directory for generated tests
            compile_commands: Path to compile_commands.json
            include_patterns: Patterns to include
            exclude_patterns: Patterns to exclude
            max_concurrent: Maximum concurrent LLM calls
            enable_progress: Enable progress reporting
            config_overrides: Additional config overrides
        """
        logger.info(f"Starting streaming test generation for: {project_path}")

        # Create streaming service
        self.service = StreamingTestGenerationService()

        # Configure streaming parameters with enhanced retry config
        config = {
            'max_concurrent_llm_calls': max_concurrent,
            'timeout_seconds': 300,
            'retry_attempts': LLM_RETRY_CONFIG.max_attempts,
            'retry_delay': LLM_RETRY_CONFIG.base_delay,
            'retry_backoff_multiplier': LLM_RETRY_CONFIG.backoff_multiplier,
            **config_overrides
        }

        # Setup progress callback
        progress_callback = await self._setup_progress_callback(enable_progress)

        try:
            start_time = time.time()

            # Run streaming generation with error isolation
            try:
                results_stream = self.service.generate_tests_streaming(
                    project_path=project_path,
                    compile_commands_path=compile_commands,
                    output_dir=output_dir,
                    config=config,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                    progress_callback=progress_callback
                )

                # Process results
                results = await self._process_results(results_stream, start_time)

                # Calculate total time and log results
                end_time = time.time()
                total_time = end_time - start_time
                self._log_final_results(results, total_time)

            except Exception as e:
                logger.error(f"Streaming generation failed: {e}")
                # Attempt to continue with partial results if available
                raise

        finally:
            if self.service:
                await self.service.shutdown()

    async def shutdown(self) -> None:
        """Cleanup resources"""
        if self.service:
            await self.service.shutdown()