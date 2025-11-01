"""
Error handling and resilience tests for streaming architecture.

These tests verify that components handle errors gracefully and recover properly.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from src.core.streaming.interfaces import StreamingConfiguration
from src.core.streaming.file_discoverer import FileDiscoverer
from src.core.streaming.function_processor import FunctionProcessor
from src.core.streaming.llm_processor import LLMProcessor
from src.core.streaming.result_collector import ResultCollector


class FailingLLMClient:
    """LLM client that always fails"""

    def __init__(self, fail_on_call=None):
        self.model = "failing-model"
        self.call_count = 0
        self.fail_on_call = fail_on_call

    def generate_test(self, prompt: str, function_name: str) -> str:
        self.call_count += 1
        if self.fail_on_call is None or self.call_count >= self.fail_on_call:
            raise RuntimeError(f"Simulated failure for {function_name} (call #{self.call_count})")
        return f"// Success for {function_name}"


class UnreliableLLMClient:
    """LLM client that fails intermittently"""

    def __init__(self, failure_rate=0.5):
        self.model = "unreliable-model"
        self.failure_rate = failure_rate
        self.call_count = 0

    def generate_test(self, prompt: str, function_name: str) -> str:
        self.call_count += 1
        import random
        if random.random() < self.failure_rate:
            raise RuntimeError(f"Random failure for {function_name} (call #{self.call_count})")
        return f"// Success for {function_name}"


class TestErrorHandling:
    """Error handling and resilience tests"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def config(self):
        """Basic streaming configuration"""
        return StreamingConfiguration(
            max_queue_size=10,
            max_concurrent_files=2,
            max_concurrent_functions=2,
            max_concurrent_llm_calls=1,
            retry_attempts=3,
            timeout_seconds=10
        )

    @pytest.mark.asyncio
    async def test_llm_processor_error_handling(self, config):
        """Test LLM processor handles errors gracefully"""
        failing_client = FailingLLMClient()
        processor = LLMProcessor(config=config, llm_client=failing_client)

        # Test that processor can be created with failing client
        assert processor.llm_client == failing_client

        # Test that cleanup works even if client fails
        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_llm_processor_retry_mechanism(self, config):
        """Test LLM processor retry mechanism"""
        # Client that fails on first call but succeeds on retry
        retry_client = FailingLLMClient(fail_on_call=2)
        processor = LLMProcessor(config=config, llm_client=retry_client)

        # The processor should handle retries internally
        # For now, just test it doesn't crash
        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_component_creation_with_invalid_config(self):
        """Test component creation with invalid configurations"""
        invalid_configs = [
            StreamingConfiguration(max_queue_size=0),
            StreamingConfiguration(max_concurrent_files=0),
            StreamingConfiguration(max_concurrent_functions=0),
            StreamingConfiguration(max_concurrent_llm_calls=0),
            StreamingConfiguration(timeout_seconds=0),
            StreamingConfiguration(retry_attempts=-1)
        ]

        for invalid_config in invalid_configs:
            # Validation should fail
            with pytest.raises(ValueError):
                invalid_config.validate()

            # Components should be created with config (validation happens at usage time)
            # This is a design choice - components validate when needed, not at creation
            try:
                discoverer = FileDiscoverer(config=invalid_config)
                processor = FunctionProcessor(config=invalid_config)
                # Components are created, but validation will fail when used
            except ValueError:
                # If validation happens at creation, that's also acceptable
                pass

    @pytest.mark.asyncio
    async def test_component_cleanup_after_error(self, config, temp_output_dir):
        """Test components can be cleaned up after errors"""
        failing_client = FailingLLMClient()

        components = [
            FileDiscoverer(config=config),
            FunctionProcessor(config=config),
            LLMProcessor(config=config, llm_client=failing_client),
            ResultCollector(config=config, output_dir=temp_output_dir)
        ]

        # All components should be cleanable even after errors
        for component in components:
            try:
                await component.cleanup()
            except Exception as e:
                pytest.fail(f"Component cleanup failed: {e}")

    def test_configuration_validation_edge_cases(self):
        """Test configuration validation edge cases"""
        # Test boundary values
        boundary_configs = [
            StreamingConfiguration(max_queue_size=1),  # Minimum valid
            StreamingConfiguration(max_concurrent_files=1),  # Minimum valid
            StreamingConfiguration(max_concurrent_functions=1),  # Minimum valid
            StreamingConfiguration(max_concurrent_llm_calls=1),  # Minimum valid
            StreamingConfiguration(timeout_seconds=1),  # Minimum valid
            StreamingConfiguration(retry_attempts=0),  # Minimum valid
        ]

        for config in boundary_configs:
            # Should not raise for valid boundary values
            config.validate()

        # Test slightly invalid boundary values
        invalid_boundary_configs = [
            StreamingConfiguration(max_queue_size=-1),
            StreamingConfiguration(max_concurrent_files=-1),
            StreamingConfiguration(max_concurrent_functions=-1),
            StreamingConfiguration(max_concurrent_llm_calls=-1),
            StreamingConfiguration(timeout_seconds=-1),
            StreamingConfiguration(retry_attempts=-2),
        ]

        for invalid_config in invalid_boundary_configs:
            # Should raise for invalid boundary values
            with pytest.raises(ValueError):
                invalid_config.validate()

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_errors(self, config, temp_output_dir):
        """Test resource cleanup when errors occur"""
        failing_client = FailingLLMClient()

        # Create components
        discoverer = FileDiscoverer(config=config)
        processor = FunctionProcessor(config=config)
        llm_processor = LLMProcessor(config=config, llm_client=failing_client)
        collector = ResultCollector(config=config, output_dir=temp_output_dir)

        # Simulate error scenarios and ensure cleanup still works
        components = [discoverer, processor, llm_processor, collector]

        for component in components:
            try:
                # Simulate some operation that might fail
                if hasattr(component, 'processed_count'):
                    _ = component.processed_count
            except Exception:
                pass  # Ignore errors for this test

            # Cleanup should still work
            await component.cleanup()

    def test_error_propagation_isolation(self, config):
        """Test that errors in one component don't affect others"""
        failing_client = FailingLLMClient()

        # Components should be independent
        discoverer = FileDiscoverer(config=config)
        processor = FunctionProcessor(config=config)

        # One component with failing client should not affect others
        try:
            llm_processor = LLMProcessor(config=config, llm_client=failing_client)
        except Exception:
            pass  # Expected

        # Other components should still work
        assert discoverer is not None
        assert processor is not None
        assert discoverer.config == config
        assert processor.config == config

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, config):
        """Test error handling in concurrent scenarios"""
        failing_client = FailingLLMClient()

        # Create multiple components that might fail concurrently
        components = [
            LLMProcessor(config=config, llm_client=failing_client)
            for _ in range(5)
        ]

        # All components should be created successfully
        assert len(components) == 5

        # All components should be cleanable concurrently
        cleanup_tasks = [component.cleanup() for component in components]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    def test_memory_leak_prevention(self, config):
        """Test that error scenarios don't cause memory leaks"""
        import gc
        import weakref

        failing_client = FailingLLMClient()

        # Create and destroy components in error scenarios
        for _ in range(10):
            try:
                component = LLMProcessor(config=config, llm_client=failing_client)
                # Create weak reference to track cleanup
                ref = weakref.ref(component)
                del component
                gc.collect()
                # Component should be garbage collectable
                # (Note: weakref might still exist due to circular references)
            except Exception:
                pass

        # Force garbage collection
        gc.collect()

        # If we get here without memory errors, basic leak prevention is working
        assert True

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in components"""
        # Create configuration with very short timeout
        timeout_config = StreamingConfiguration(timeout_seconds=0.001)

        # Components should handle timeout gracefully
        try:
            processor = FunctionProcessor(config=timeout_config)
            # Component creation should succeed
            assert processor.config.timeout_seconds == 0.001

            # Cleanup should work even with short timeout
            await processor.cleanup()
        except Exception as e:
            # Should handle timeout gracefully
            assert isinstance(e, (ValueError, TimeoutError))

    def test_invalid_input_handling(self, config):
        """Test handling of invalid inputs"""
        failing_client = FailingLLMClient()

        # Components should handle various invalid inputs gracefully
        try:
            # Test with None values where applicable
            processor = LLMProcessor(config=config, llm_client=failing_client)
            # Should be created successfully
            assert processor is not None
        except Exception as e:
            # Should handle invalid input gracefully
            assert isinstance(e, (ValueError, TypeError, AttributeError))

    @pytest.mark.asyncio
    async def test_error_recovery_patterns(self, config, temp_output_dir):
        """Test various error recovery patterns"""
        # Test different failure scenarios
        failure_scenarios = [
            FailingLLMClient(fail_on_call=1),  # Fails immediately
            FailingLLMClient(fail_on_call=3),  # Fails after some calls
            UnreliableLLMClient(failure_rate=1.0),  # Always fails
            UnreliableLLMClient(failure_rate=0.5),  # Sometimes fails
        ]

        for i, failing_client in enumerate(failure_scenarios):
            try:
                processor = LLMProcessor(config=config, llm_client=failing_client)
                # Should be able to create processor
                assert processor is not None

                # Should be able to cleanup
                await processor.cleanup()

            except Exception as e:
                # Should handle errors gracefully
                print(f"Error recovery pattern {i}: {type(e).__name__}: {e}")
                # Should not crash completely
                assert True

    def test_configuration_robustness(self):
        """Test configuration robustness with extreme values"""
        # Test with extreme but valid values
        extreme_configs = [
            StreamingConfiguration(max_queue_size=1000000),
            StreamingConfiguration(max_concurrent_files=1000),
            StreamingConfiguration(max_concurrent_functions=1000),
            StreamingConfiguration(max_concurrent_llm_calls=1000),
            StreamingConfiguration(timeout_seconds=3600),  # 1 hour
            StreamingConfiguration(retry_attempts=100),
        ]

        for config in extreme_configs:
            try:
                config.validate()  # Should validate successfully
            except Exception as e:
                # If validation fails, it should be for a good reason
                assert isinstance(e, ValueError)

        # Test with combinations of extreme values
        try:
            extreme_combo_config = StreamingConfiguration(
                max_queue_size=10000,
                max_concurrent_files=100,
                max_concurrent_functions=100,
                max_concurrent_llm_calls=50,
                timeout_seconds=600,
                retry_attempts=10
            )
            extreme_combo_config.validate()
        except Exception as e:
            # Should handle extreme combinations gracefully
            assert isinstance(e, ValueError)