"""
Performance benchmark tests for streaming architecture.

These tests establish performance baselines and measure key metrics.
"""

import pytest
import asyncio
import time
import tempfile
from pathlib import Path

from src.core.streaming.interfaces import StreamingConfiguration
from src.core.streaming.file_discoverer import FileDiscoverer
from src.core.streaming.function_processor import FunctionProcessor
from src.core.streaming.llm_processor import LLMProcessor
from src.core.streaming.result_collector import ResultCollector


class BenchmarkLLMClient:
    """LLM client for performance testing"""

    def __init__(self, processing_delay: float = 0.01):
        self.processing_delay = processing_delay
        self.model = "benchmark-model"
        self.call_count = 0

    def generate_test(self, prompt: str, function_name: str) -> str:
        self.call_count += 1
        time.sleep(self.processing_delay)  # Simulate processing time
        return f"// Benchmark test for {function_name} (call #{self.call_count})"


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def performance_config(self):
        """Performance-optimized configuration"""
        return StreamingConfiguration(
            max_queue_size=100,
            max_concurrent_files=5,
            max_concurrent_functions=10,
            max_concurrent_llm_calls=5,
            timeout_seconds=60,
            retry_attempts=1
        )

    def test_component_creation_performance(self, performance_config, temp_output_dir):
        """Benchmark component creation time"""
        mock_client = BenchmarkLLMClient()

        creation_times = {}

        # Benchmark FileDiscoverer creation
        start = time.time()
        discoverer = FileDiscoverer(config=performance_config)
        creation_times['file_discoverer'] = time.time() - start

        # Benchmark FunctionProcessor creation
        start = time.time()
        processor = FunctionProcessor(config=performance_config)
        creation_times['function_processor'] = time.time() - start

        # Benchmark LLMProcessor creation
        start = time.time()
        llm_processor = LLMProcessor(config=performance_config, llm_client=mock_client)
        creation_times['llm_processor'] = time.time() - start

        # Benchmark ResultCollector creation
        start = time.time()
        collector = ResultCollector(config=performance_config, output_dir=temp_output_dir)
        creation_times['result_collector'] = time.time() - start

        # Assertions - all components should create quickly
        for component, creation_time in creation_times.items():
            assert creation_time < 0.1, f"{component} creation too slow: {creation_time}s"

        # Total creation time should be reasonable
        total_creation_time = sum(creation_times.values())
        assert total_creation_time < 0.5, f"Total component creation too slow: {total_creation_time}s"

    def test_configuration_validation_performance(self):
        """Benchmark configuration validation"""
        configs = [
            StreamingConfiguration(max_queue_size=10),
            StreamingConfiguration(max_queue_size=100),
            StreamingConfiguration(max_queue_size=1000),
            StreamingConfiguration(max_concurrent_files=1),
            StreamingConfiguration(max_concurrent_files=10),
            StreamingConfiguration(max_concurrent_functions=1),
            StreamingConfiguration(max_concurrent_functions=20),
            StreamingConfiguration(max_concurrent_llm_calls=1),
            StreamingConfiguration(max_concurrent_llm_calls=10),
        ]

        validation_times = []
        for config in configs:
            start = time.time()
            config.validate()
            validation_time = time.time() - start
            validation_times.append(validation_time)

        # All validations should be very fast
        avg_validation_time = sum(validation_times) / len(validation_times)
        assert avg_validation_time < 0.01, f"Configuration validation too slow: {avg_validation_time}s"

        # Max validation time should be reasonable
        max_validation_time = max(validation_times)
        assert max_validation_time < 0.05, f"Max configuration validation too slow: {max_validation_time}s"

    @pytest.mark.asyncio
    async def test_cleanup_performance(self, performance_config, temp_output_dir):
        """Benchmark component cleanup performance"""
        mock_client = BenchmarkLLMClient()

        components = [
            FileDiscoverer(config=performance_config),
            FunctionProcessor(config=performance_config),
            LLMProcessor(config=performance_config, llm_client=mock_client),
            ResultCollector(config=performance_config, output_dir=temp_output_dir)
        ]

        cleanup_times = []
        for component in components:
            start = time.time()
            await component.cleanup()
            cleanup_time = time.time() - start
            cleanup_times.append(cleanup_time)

        # All cleanups should be fast
        avg_cleanup_time = sum(cleanup_times) / len(cleanup_times)
        assert avg_cleanup_time < 0.1, f"Average cleanup too slow: {avg_cleanup_time}s"

        # Max cleanup time should be reasonable
        max_cleanup_time = max(cleanup_times)
        assert max_cleanup_time < 0.5, f"Max cleanup too slow: {max_cleanup_time}s"

    def test_memory_usage_baseline(self, performance_config, temp_output_dir):
        """Establish baseline memory usage"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        mock_client = BenchmarkLLMClient()

        # Create all components
        components = [
            FileDiscoverer(config=performance_config),
            FunctionProcessor(config=performance_config),
            LLMProcessor(config=performance_config, llm_client=mock_client),
            ResultCollector(config=performance_config, output_dir=temp_output_dir)
        ]

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Memory usage should be reasonable for these components
        assert memory_increase < 50, f"Memory usage too high: {memory_increase}MB"

        # Clean up
        del components

    def test_throughput_benchmarks(self):
        """Benchmark processing throughput"""
        mock_client = BenchmarkLLMClient(processing_delay=0.001)  # Very fast for benchmarking

        # Simulate processing multiple items
        items_to_process = 100
        start_time = time.time()

        for i in range(items_to_process):
            mock_client.generate_test(f"prompt_{i}", f"function_{i}")

        end_time = time.time()
        total_time = end_time - start_time
        throughput = items_to_process / total_time

        # Should be able to process items quickly
        assert throughput > 50, f"Throughput too low: {throughput} items/sec"

    def test_concurrent_processing_benchmark(self):
        """Benchmark concurrent processing capabilities"""
        import threading
        import queue

        mock_client = BenchmarkLLMClient(processing_delay=0.01)
        result_queue = queue.Queue()

        def worker(worker_id):
            """Worker function for concurrent processing"""
            for i in range(10):
                result = mock_client.generate_test(f"prompt_{worker_id}_{i}", f"function_{worker_id}_{i}")
                result_queue.put((worker_id, i, result))

        # Create multiple workers
        num_workers = 5
        workers = []

        start_time = time.time()

        # Start workers
        for i in range(num_workers):
            worker_thread = threading.Thread(target=worker, args=(i,))
            workers.append(worker_thread)
            worker_thread.start()

        # Wait for all workers to complete
        for worker in workers:
            worker.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Check results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # Should have processed all items
        expected_results = num_workers * 10
        assert len(results) == expected_results, f"Expected {expected_results} results, got {len(results)}"

        # Concurrent processing should be faster than sequential
        sequential_time = expected_results * 0.01  # Each item takes 0.01s
        assert total_time < sequential_time * 0.8, f"Concurrent processing not efficient: {total_time}s vs {sequential_time}s sequential"

    def test_large_configuration_handling(self):
        """Benchmark handling of large configurations"""
        # Create configuration with large values
        large_config = StreamingConfiguration(
            max_queue_size=10000,
            max_concurrent_files=100,
            max_concurrent_functions=200,
            max_concurrent_llm_calls=50
        )

        # Benchmark validation
        start = time.time()
        large_config.validate()
        validation_time = time.time() - start

        # Should handle large configurations quickly
        assert validation_time < 0.1, f"Large configuration validation too slow: {validation_time}s"

        # Benchmark component creation with large config
        mock_client = BenchmarkLLMClient()
        start = time.time()
        discoverer = FileDiscoverer(config=large_config)
        creation_time = time.time() - start

        assert creation_time < 0.1, f"Component creation with large config too slow: {creation_time}s"

    @pytest.mark.asyncio
    async def test_scaling_benchmark(self, temp_output_dir):
        """Benchmark how components scale with load"""
        mock_client = BenchmarkLLMClient(processing_delay=0.001)

        # Test different scales
        scales = [1, 10, 50, 100]
        creation_times = []

        for scale in scales:
            config = StreamingConfiguration(
                max_concurrent_files=min(scale, 10),
                max_concurrent_functions=min(scale, 20),
                max_concurrent_llm_calls=min(scale, 5)
            )

            start = time.time()
            component = LLMProcessor(config=config, llm_client=mock_client)
            creation_time = time.time() - start
            creation_times.append(creation_time)

            await component.cleanup()

        # Creation time should scale reasonably
        # Time for scale 100 should not be more than 10x time for scale 1
        time_ratio = creation_times[-1] / creation_times[0]
        assert time_ratio < 10, f"Poor scaling: {time_ratio}x slower for 100x scale"

    def test_error_handling_performance(self):
        """Benchmark error handling performance"""
        class FailingLLMClient:
            def __init__(self):
                self.model = "failing-model"

            def generate_test(self, prompt: str, function_name: str) -> str:
                raise RuntimeError("Simulated failure")

        mock_client = FailingLLMClient()
        config = StreamingConfiguration()

        # Benchmark error handling
        start = time.time()
        try:
            processor = LLMProcessor(config=config, llm_client=mock_client)
            # Component creation should not fail due to client issues
        except Exception:
            pass
        creation_time = time.time() - start

        # Error handling should be fast
        assert creation_time < 0.1, f"Error handling too slow: {creation_time}s"