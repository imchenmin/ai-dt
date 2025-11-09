"""
LLM processor component for streaming test generation.

This component is responsible for generating test cases using LLM APIs.
It integrates with the existing LLM client while providing streaming capabilities
with proper rate limiting, retry logic, and error handling.
"""

import asyncio
import time
from typing import AsyncIterator, Dict, Any, Optional, List
from dataclasses import dataclass

from .interfaces import (
    StreamProcessor, StreamPacket, StreamStage, StreamingConfiguration,
    FunctionStreamData, StreamObserver
)
from src.utils.logging_utils import get_logger
from src.llm.client import LLMClient
from src.llm.models import LLMConfig
from src.test_generation.models import GenerationResult, GenerationTask
from src.test_generation.components import PromptGenerator


@dataclass
class LLMProcessingMetrics:
    """Metrics for LLM processing performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    tokens_used: int = 0
    api_calls_made: int = 0


class LLMRateLimiter:
    """Rate limiter for LLM API calls"""

    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 100000):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
            tokens_per_minute: Maximum tokens per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times = []
        self.token_usage = []
        self.lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 1000) -> None:
        """
        Acquire permission to make an API call

        Args:
            estimated_tokens: Estimated token usage for this request
        """
        async with self.lock:
            now = time.time()
            minute_ago = now - 60

            # Clean old entries
            self.request_times = [t for t in self.request_times if t > minute_ago]
            self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > minute_ago]

            # Check request rate limit
            if len(self.request_times) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            # Check token rate limit
            current_tokens = sum(tokens for _, tokens in self.token_usage)
            if current_tokens + estimated_tokens > self.tokens_per_minute:
                # Simple token rate limiting - wait if over limit
                await asyncio.sleep(1.0)

            # Record this request
            self.request_times.append(now)
            self.token_usage.append((now, estimated_tokens))


class LLMProcessor(StreamProcessor):
    """
    Stream processor for generating test cases using LLM APIs.

    This processor takes function packets and emits result packets with generated
    test code. It handles rate limiting, retries, and proper error recovery while
    maintaining streaming semantics.
    """

    def __init__(
        self,
        config: StreamingConfiguration,
        llm_client: Optional[LLMClient] = None,
        llm_config: Optional[LLMConfig] = None,
        observers: Optional[List[StreamObserver]] = None,
        rate_limiter: Optional[LLMRateLimiter] = None
    ):
        """
        Initialize LLM processor

        Args:
            config: Streaming configuration
            llm_client: Optional LLM client (created if not provided)
            llm_config: Optional LLM configuration
            observers: Optional observers for monitoring
            rate_limiter: Optional rate limiter
        """
        self.config = config
        self.observers = observers or []
        self.logger = get_logger(__name__)
        self.rate_limiter = rate_limiter or LLMRateLimiter()
        self.metrics = LLMProcessingMetrics()

        # Initialize LLM client
        if llm_client:
            self.llm_client = llm_client
        elif llm_config:
            self.llm_client = LLMClient.create_from_config(llm_config)
        else:
            raise ValueError("Either llm_client or llm_config must be provided")

        # Initialize prompt generator
        self.prompt_generator = PromptGenerator()

        self._processed_count = 0
        self._start_time = time.time()

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        """
        Process function packet and generate test cases

        Args:
            packet: Input packet containing function information

        Yields:
            StreamPacket: Result packet with generated test code
        """
        if packet.stage != StreamStage.LLM_PROCESSING:
            self.logger.warning(f"Unexpected packet stage: {packet.stage}")
            return

        try:
            function_data = packet.data.get("function_stream_data")
            if not function_data:
                self.logger.warning("No function_stream_data found in packet")
                return

            # Generate test case with retry logic
            result = await self._generate_test_with_retry(function_data)

            if result:
                self._processed_count += 1

                # Create result packet
                result_packet = StreamPacket(
                    stage=StreamStage.RESULT_COLLECTION,
                    data={
                        "generation_result": result,
                        "function_stream_data": function_data,
                        "source_packet_id": packet.packet_id,
                        "processing_sequence": self._processed_count
                    },
                    timestamp=time.time(),
                    packet_id=f"{packet.packet_id}-llm-result-{function_data.function_info.get('name', 'unknown')}"
                )

                # Notify observers
                processing_time = time.time() - start_time
                await self._notify_observers_packet_processed(result_packet, processing_time)

                self.logger.debug(
                    f"Generated test for: {result.function_name} "
                    f"(#{self._processed_count}, {result.test_length} chars)"
                )
                yield result_packet
            else:
                self.logger.error(f"Failed to generate test for function after retries")

        except Exception as e:
            self.logger.error(f"Error in LLM processing: {e}")
            await self._notify_observers_error(packet, e)
            raise

    async def _generate_test_with_retry(self, function_data: FunctionStreamData) -> Optional[GenerationResult]:
        """
        Generate test case with retry logic

        Args:
            function_data: Function information

        Returns:
            GenerationResult if successful, None otherwise
        """
        last_error = None

        for attempt in range(self.config.retry_attempts + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire()

                # Generate test case
                result = await self._generate_single_test(function_data, attempt + 1)

                if result:
                    self.metrics.successful_requests += 1
                    return result
                else:
                    last_error = Exception("Empty result from LLM")

            except Exception as e:
                last_error = e
                self.metrics.failed_requests += 1
                self.logger.warning(f"LLM attempt {attempt + 1} failed: {e}")

                # Don't retry on certain errors
                if self._should_not_retry(e):
                    break

                # Exponential backoff
                if attempt < self.config.retry_attempts:
                    backoff_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                    await asyncio.sleep(backoff_time)

        self.logger.error(f"All retry attempts failed for function: {function_data.function_info.get('name', 'unknown')}")
        return None

    async def _generate_single_test(self, function_data: FunctionStreamData, attempt: int) -> Optional[GenerationResult]:
        """
        Generate a single test case

        Args:
            function_data: Function information
            attempt: Current attempt number

        Returns:
            GenerationResult if successful
        """
        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Create generation task (similar to existing orchestrator)
            task = self.prompt_generator.prepare_task(
                function_data.function_info,
                {},  # Context would be populated in real implementation
                None  # Unit test directory
            )

            # Generate prompt
            prompt = self.prompt_generator.generate_prompt(task)

            # Call LLM API
            loop = asyncio.get_event_loop()
            llm_response = await loop.run_in_executor(
                None,
                self.llm_client.generate_test,
                prompt,
                2000,  # max_tokens
                0.3,  # temperature
                function_data.function_info.get("language", "c")  # language
            )

            processing_time = time.time() - start_time
            self.metrics.total_processing_time += processing_time
            self.metrics.api_calls_made += 1

            # Create generation task
            task = GenerationTask(
                function_info=function_data.function_info,
                context={},
                target_filepath=f"test_{function_data.function_info.get('name', 'unknown')}.cpp",
                suite_name=f"{function_data.function_info.get('name', 'unknown')}TestSuite"
            )

            # Handle response from generate_test (backward compatible API)
            if isinstance(llm_response, dict):
                test_code = llm_response.get('test_code', '')
                success = llm_response.get('success', False)
                model = llm_response.get('model', 'unknown')
            else:
                test_code = llm_response or ''
                success = bool(test_code.strip())
                model = self.llm_client.model if hasattr(self.llm_client, 'model') else "unknown"

            # Create generation result
            result = GenerationResult(
                task=task,
                success=success,
                test_code=test_code,
                prompt=prompt,
                model=model,
                prompt_length=len(prompt),
                test_length=len(test_code),
                file_info={"attempt": attempt, "file_path": function_data.file_path}
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.metrics.total_processing_time += processing_time
            raise e

    def _should_not_retry(self, error: Exception) -> bool:
        """
        Determine if an error should not be retried

        Args:
            error: Exception that occurred

        Returns:
            True if error should not be retried
        """
        error_str = str(error).lower()

        # Don't retry on authentication errors, invalid requests, etc.
        no_retry_errors = [
            "authentication",
            "authorization",
            "invalid request",
            "invalid api key",
            "quota exceeded",
            "model not found"
        ]

        return any(no_retry_error in error_str for no_retry_error in no_retry_errors)

    async def _process_functions_concurrent(
        self,
        function_packets: List[StreamPacket]
    ) -> AsyncIterator[StreamPacket]:
        """Process multiple functions concurrently"""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_llm_calls)

        async def process_single_function(packet: StreamPacket) -> Optional[StreamPacket]:
            async with semaphore:
                try:
                    async for result in self.process(packet):
                        return result
                except Exception as e:
                    self.logger.error(f"Error processing function concurrently: {e}")
                    return None

        # Create tasks for all function packets
        tasks = [process_single_function(packet) for packet in function_packets]

        # Wait for all tasks and yield results as they complete
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            if result:
                yield result

    async def cleanup(self):
        """Cleanup resources and log final statistics"""
        duration = time.time() - self._start_time

        # Update metrics
        if self.metrics.total_requests > 0:
            self.metrics.average_processing_time = self.metrics.total_processing_time / self.metrics.total_requests

        self.logger.info(
            f"LLM processing completed: {self._processed_count} tests generated "
            f"in {duration:.2f}s"
        )
        self.logger.info(
            f"LLM Metrics: {self.metrics.successful_requests}/{self.metrics.total_requests} successful, "
            f"avg time: {self.metrics.average_processing_time:.2f}s, "
            f"API calls: {self.metrics.api_calls_made}"
        )

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

    @property
    def metrics_report(self) -> Dict[str, Any]:
        """Get comprehensive metrics report"""
        return {
            "processed_count": self._processed_count,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": self.metrics.successful_requests / max(self.metrics.total_requests, 1),
            "average_processing_time": self.metrics.average_processing_time,
            "total_processing_time": self.metrics.total_processing_time,
            "api_calls_made": self.metrics.api_calls_made,
            "throughput": self._processed_count / max(time.time() - self._start_time, 1)
        }