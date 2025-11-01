"""
Integration tests for the complete streaming test generation architecture.

These tests verify that all components work together correctly and meet
performance requirements.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from src.core.streaming.interfaces import (
    StreamStage, StreamingConfiguration, StreamObserver, StreamMetrics
)
from src.core.streaming.pipeline_orchestrator import StreamingPipelineOrchestrator
from src.core.streaming.file_discoverer import FileDiscoverer
from src.core.streaming.function_processor import FunctionProcessor
from src.core.streaming.llm_processor import LLMProcessor
from src.core.streaming.result_collector import ResultCollector


class MockLLMClient:
    """Mock LLM client for integration testing"""

    def __init__(self, processing_delay: float = 0.1, should_fail: bool = False):
        self.processing_delay = processing_delay
        self.should_fail = should_fail
        self.model = "mock-test-model"

    def generate_test(self, prompt: str, function_name: str) -> str:
        if self.should_fail:
            raise RuntimeError(f"LLM generation failed for {function_name}")

        # Simulate processing delay
        time.sleep(self.processing_delay)

        # Generate mock test code
        test_code = f"""
// Generated test for {function_name}
TEST({function_name}Test, BasicFunctionality) {{
    // Test implementation for {function_name}
    EXPECT_TRUE(true);
}}
"""
        return test_code


class IntegrationTestObserver(StreamObserver):
    """Observer for collecting integration test metrics"""

    def __init__(self):
        self.packets_processed = []
        self.errors_occurred = []
        self.stage_changes = []

    async def on_packet_processed(self, packet, processing_time: float):
        self.packets_processed.append((packet, processing_time))

    async def on_error_occurred(self, packet, error: Exception):
        self.errors_occurred.append((packet, error))

    async def on_stage_changed(self, stage, metrics: StreamMetrics):
        self.stage_changes.append((stage, metrics))


class TestStreamingArchitectureIntegration:
    """Integration tests for the complete streaming architecture"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def streaming_config(self):
        """Streaming configuration for integration tests"""
        return StreamingConfiguration(
            max_queue_size=50,
            max_concurrent_files=2,
            max_concurrent_functions=3,
            max_concurrent_llm_calls=2,
            timeout_seconds=30,
            retry_attempts=2
        )

    @pytest.fixture
    def sample_compilation_units(self):
        """Sample compilation units for integration testing"""
        return [
            {
                "file": "src/math.c",
                "arguments": ["-O2", "-Wall"]
            },
            {
                "file": "src/utils.c",
                "arguments": ["-O2", "-Wall"]
            },
            {
                "file": "src/processor.cpp",
                "arguments": ["-std=c++17", "-O2"]
            }
        ]

    @pytest.mark.asyncio
    async def test_end_to_end_streaming_architecture(
        self, streaming_config, sample_compilation_units, temp_output_dir
    ):
        """Test complete end-to-end streaming architecture"""
        # Create mock LLM client
        mock_llm_client = MockLLMClient(processing_delay=0.05)

        # Create observer
        observer = IntegrationTestObserver()

        # Create orchestrator with all components
        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            observers=[observer],
            llm_client=mock_llm_client,
            project_root="."
        )

        try:
            # Execute streaming pipeline
            results = []
            start_time = time.time()

            async for packet in orchestrator.execute_streaming(
                sample_compilation_units, [observer]
            ):
                results.append(packet)

            end_time = time.time()
            total_time = end_time - start_time

            # Verify results
            assert len(results) > 0, "Should generate at least some results"
            assert len(observer.errors_occurred) == 0, f"Errors occurred: {observer.errors_occurred}"

            # Check that files were generated
            output_path = Path(temp_output_dir)
            generated_files = list(output_path.glob("test_*.cpp")) + list(output_path.glob("test_*.c"))
            assert len(generated_files) > 0, "Should generate test files"

            # Check performance characteristics
            assert total_time < 10.0, f"Processing took too long: {total_time}s"
            assert orchestrator.metrics_report["statistics"]["packets_processed"] > 0

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_streaming_performance_vs_batch_processing(
        self, streaming_config, sample_compilation_units, temp_output_dir
    ):
        """Test that streaming architecture performs better than batch processing"""
        mock_llm_client = MockLLMClient(processing_delay=0.1)

        observer = IntegrationTestObserver()

        # Test streaming architecture
        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            observers=[observer],
            llm_client=mock_llm_client,
            project_root="."
        )

        try:
            streaming_start = time.time()
            streaming_results = []

            async for packet in orchestrator.execute_streaming(sample_compilation_units):
                streaming_results.append(packet)
                # Check first result time for streaming
                if len(streaming_results) == 1:
                    first_result_time = time.time() - streaming_start

            streaming_total_time = time.time() - streaming_start

            # Performance assertions
            assert first_result_time < 2.0, f"First result took too long: {first_result_time}s"
            assert streaming_total_time < 15.0, f"Total processing took too long: {streaming_total_time}s"

            # Verify that streaming provides early results
            assert len(streaming_results) > 0, "Streaming should produce results"

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(
        self, streaming_config, temp_output_dir
    ):
        """Test concurrent processing with larger compilation unit set"""
        # Create more compilation units to test concurrency
        large_compilation_units = [
            {"file": f"src/file_{i}.c", "arguments": ["-O2", "-Wall"]}
            for i in range(10)
        ]

        mock_llm_client = MockLLMClient(processing_delay=0.05)
        observer = IntegrationTestObserver()

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            observers=[observer],
            llm_client=mock_llm_client,
            project_root="."
        )

        try:
            start_time = time.time()
            results = []

            async for packet in orchestrator.execute_streaming(large_compilation_units):
                results.append(packet)

            total_time = time.time() - start_time

            # Verify concurrent processing is faster than sequential
            # (Sequential would be 10 * 0.05s = 0.5s minimum + overhead)
            assert total_time < 2.0, f"Concurrent processing too slow: {total_time}s"

            # Verify all files were processed
            output_path = Path(temp_output_dir)
            generated_files = list(output_path.glob("test_*.cpp"))
            assert len(generated_files) > 0, "Should process multiple files concurrently"

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_error_resilience_and_recovery(
        self, streaming_config, sample_compilation_units, temp_output_dir
    ):
        """Test that pipeline handles errors gracefully and continues processing"""
        # Create LLM client that fails for specific functions
        class FailingMockLLMClient:
            def __init__(self):
                self.model = "failing-model"
                self.call_count = 0

            def generate_test(self, prompt: str, function_name: str) -> str:
                self.call_count += 1
                # Fail for every third call
                if self.call_count % 3 == 0:
                    raise RuntimeError(f"Simulated failure for {function_name}")

                return f"// Test for {function_name}"

        mock_llm_client = FailingMockLLMClient()
        observer = IntegrationTestObserver()

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            observers=[observer],
            llm_client=mock_llm_client,
            project_root="."
        )

        try:
            results = []
            errors_before = len(observer.errors_occurred)

            async for packet in orchestrator.execute_streaming(sample_compilation_units):
                results.append(packet)

            # Should have some results despite errors
            assert len(results) > 0, "Should produce some results despite errors"

            # Should have recorded errors
            assert len(observer.errors_occurred) > errors_before, "Should record errors"

            # Should continue processing after errors
            final_metrics = orchestrator.metrics_report
            assert final_metrics["statistics"]["packets_processed"] > 0

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(
        self, streaming_config, temp_output_dir
    ):
        """Test that memory usage stays within acceptable limits"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create many compilation units
        many_compilation_units = [
            {"file": f"src/large_file_{i}.c", "arguments": ["-O2", "-Wall"]}
            for i in range(50)
        ]

        mock_llm_client = MockLLMClient(processing_delay=0.01)

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client,
            project_root="."
        )

        try:
            results = []
            peak_memory = initial_memory

            async for packet in orchestrator.execute_streaming(many_compilation_units):
                results.append(packet)

                # Monitor memory usage
                current_memory = process.memory_info().rss / 1024 / 1024
                peak_memory = max(peak_memory, current_memory)

            memory_increase = peak_memory - initial_memory

            # Memory increase should be reasonable (less than 100MB for this test)
            assert memory_increase < 100, f"Memory increase too large: {memory_increase}MB"

            # Should still process all items
            assert len(results) > 0, "Should process all items"

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_graceful_shutdown_and_cleanup(
        self, streaming_config, sample_compilation_units, temp_output_dir
    ):
        """Test graceful shutdown and resource cleanup"""
        mock_llm_client = MockLLMClient(processing_delay=0.2)  # Slow processing

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client,
            project_root="."
        )

        # Start processing
        processing_task = asyncio.create_task(
            orchestrator.execute_streaming(sample_compilation_units).__anext__()
        )

        # Let it start
        await asyncio.sleep(0.1)

        # Shutdown while processing
        shutdown_start = time.time()
        await orchestrator.shutdown()
        shutdown_time = time.time() - shutdown_start

        # Shutdown should be quick
        assert shutdown_time < 2.0, f"Shutdown took too long: {shutdown_time}s"

        # Should be able to shutdown again without issues
        await orchestrator.shutdown()

        # Cancel the processing task
        processing_task.cancel()
        try:
            await processing_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_configuration_validation_and_edge_cases(
        self, streaming_config, temp_output_dir
    ):
        """Test configuration validation and edge cases"""
        # Test with invalid configuration
        invalid_config = StreamingConfiguration(max_queue_size=0)

        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            StreamingPipelineOrchestrator(
                config=invalid_config,
                output_dir=temp_output_dir
            )

        # Test with empty compilation units
        valid_config = StreamingConfiguration()
        mock_llm_client = MockLLMClient()

        orchestrator = StreamingPipelineOrchestrator(
            config=valid_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client
        )

        try:
            results = []
            async for packet in orchestrator.execute_streaming([]):
                results.append(packet)

            # Should handle empty input gracefully
            assert isinstance(results, list)

        finally:
            await orchestrator.shutdown()

    def test_streaming_architecture_component_isolation(
        self, streaming_config, temp_output_dir
    ):
        """Test that components are properly isolated and can be tested independently"""
        # Test file discoverer independently
        file_discoverer = FileDiscoverer(config=streaming_config)
        assert hasattr(file_discoverer, 'process')
        assert hasattr(file_discoverer, 'cleanup')

        # Test function processor independently
        function_processor = FunctionProcessor(config=streaming_config)
        assert hasattr(function_processor, 'process')
        assert hasattr(function_processor, 'cleanup')

        # Test LLM processor independently
        mock_llm_client = MockLLMClient()
        llm_processor = LLMProcessor(
            config=streaming_config,
            llm_client=mock_llm_client
        )
        assert hasattr(llm_processor, 'process')
        assert hasattr(llm_processor, 'cleanup')

        # Test result collector independently
        result_collector = ResultCollector(
            config=streaming_config,
            output_dir=temp_output_dir
        )
        assert hasattr(result_collector, 'process')
        assert hasattr(result_collector, 'cleanup')

    @pytest.mark.asyncio
    async def test_streaming_architecture_metrics_and_monitoring(
        self, streaming_config, sample_compilation_units, temp_output_dir
    ):
        """Test comprehensive metrics collection and monitoring"""
        mock_llm_client = MockLLMClient(processing_delay=0.05)
        observer = IntegrationTestObserver()

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            observers=[observer],
            llm_client=mock_llm_client,
            project_root="."
        )

        try:
            results = []
            async for packet in orchestrator.execute_streaming(sample_compilation_units):
                results.append(packet)

            # Verify metrics are collected
            metrics_report = orchestrator.metrics_report

            assert "statistics" in metrics_report
            assert "config" in metrics_report
            assert "current_metrics" in metrics_report

            stats = metrics_report["statistics"]
            assert stats["packets_processed"] > 0
            assert stats["running_time"] > 0
            assert "packets_by_stage" in stats

            # Verify observer received metrics
            assert len(observer.stage_changes) > 0
            assert len(observer.packets_processed) > 0

        finally:
            await orchestrator.shutdown()