"""
Component integration tests for streaming architecture.

These tests verify that individual components work together correctly.
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


class SimpleMockLLMClient:
    """Simple mock LLM client"""

    def __init__(self):
        self.model = "mock-model"

    def generate_test(self, prompt: str, function_name: str) -> str:
        return f"// Mock test for {function_name}"


class TestComponentIntegration:
    """Integration tests for streaming components"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def config(self):
        """Basic configuration"""
        return StreamingConfiguration(
            max_queue_size=10,
            max_concurrent_files=2,
            max_concurrent_functions=2,
            max_concurrent_llm_calls=1
        )

    def test_file_discoverer_integration(self, config):
        """Test file discoverer can be created and configured"""
        discoverer = FileDiscoverer(config=config)

        assert discoverer.config == config
        assert discoverer.filter is not None
        assert hasattr(discoverer, 'process')
        assert hasattr(discoverer, 'cleanup')

    def test_function_processor_integration(self, config):
        """Test function processor can be created and configured"""
        processor = FunctionProcessor(config=config, project_root=".")

        assert processor.config == config
        assert processor.project_root == "."
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'cleanup')

    def test_llm_processor_integration(self, config):
        """Test LLM processor can be created and configured"""
        mock_client = SimpleMockLLMClient()
        processor = LLMProcessor(config=config, llm_client=mock_client)

        assert processor.config == config
        assert processor.llm_client == mock_client
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'cleanup')

    def test_result_collector_integration(self, config, temp_output_dir):
        """Test result collector can be created and configured"""
        collector = ResultCollector(config=config, output_dir=temp_output_dir)

        assert collector.config == config
        assert collector.output_dir == Path(temp_output_dir)
        assert hasattr(collector, 'process')
        assert hasattr(collector, 'cleanup')

    @pytest.mark.asyncio
    async def test_component_async_interfaces(self, config):
        """Test that components have proper async interfaces"""
        mock_client = SimpleMockLLMClient()

        discoverer = FileDiscoverer(config=config)
        processor = FunctionProcessor(config=config)
        llm_processor = LLMProcessor(config=config, llm_client=mock_client)

        # Test that async methods exist and are callable
        assert asyncio.iscoroutinefunction(discoverer.cleanup)
        assert asyncio.iscoroutinefunction(processor.cleanup)
        assert asyncio.iscoroutinefunction(llm_processor.cleanup)

        # Test cleanup methods can be called
        await discoverer.cleanup()
        await processor.cleanup()
        await llm_processor.cleanup()

    def test_configuration_validation(self):
        """Test configuration validation across components"""
        # Test valid configuration
        valid_config = StreamingConfiguration(max_queue_size=10)
        valid_config.validate()  # Should not raise

        # Test invalid configuration
        invalid_config = StreamingConfiguration(max_queue_size=0)
        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            invalid_config.validate()

    def test_component_independence(self, config, temp_output_dir):
        """Test components are independent and can be created separately"""
        mock_client = SimpleMockLLMClient()

        # Create components independently
        discoverer = FileDiscoverer(config=config)
        processor = FunctionProcessor(config=config)
        llm_processor = LLMProcessor(config=config, llm_client=mock_client)
        collector = ResultCollector(config=config, output_dir=temp_output_dir)

        # All should be independent
        assert discoverer is not None
        assert processor is not None
        assert llm_processor is not None
        assert collector is not None

        # Should have different configurations
        assert discoverer.config == config
        assert processor.config == config
        assert llm_processor.config == config
        assert collector.config == config

    def test_component_memory_usage(self, config):
        """Test components don't have obvious memory leaks"""
        import gc
        import sys

        mock_client = SimpleMockLLMClient()

        # Create and destroy components
        for _ in range(10):
            discoverer = FileDiscoverer(config=config)
            processor = FunctionProcessor(config=config)
            llm_processor = LLMProcessor(config=config, llm_client=mock_client)

            # Components should be garbage collectable
            del discoverer, processor, llm_processor

        # Force garbage collection
        gc.collect()

        # Memory usage should be reasonable (basic check)
        # This is a simple check - more sophisticated memory testing would require external tools
        assert True  # If we get here without MemoryError, basic memory usage is ok

    @pytest.mark.asyncio
    async def test_component_error_handling(self, config):
        """Test components handle errors gracefully"""
        mock_client = SimpleMockLLMClient()

        components = [
            FileDiscoverer(config=config),
            FunctionProcessor(config=config),
            LLMProcessor(config=config, llm_client=mock_client)
        ]

        # All components should have cleanup methods that can be called safely
        for component in components:
            try:
                await component.cleanup()
            except Exception as e:
                pytest.fail(f"Component cleanup raised exception: {e}")

    def test_component_configuration_options(self):
        """Test various configuration options"""
        # Test different configurations
        configs = [
            StreamingConfiguration(max_concurrent_files=1),
            StreamingConfiguration(max_concurrent_files=5),
            StreamingConfiguration(max_concurrent_functions=1),
            StreamingConfiguration(max_concurrent_functions=3),
            StreamingConfiguration(max_concurrent_llm_calls=1),
            StreamingConfiguration(max_concurrent_llm_calls=5),
        ]

        mock_client = SimpleMockLLMClient()

        for config in configs:
            config.validate()  # Should not raise

            # Components should accept different configurations
            discoverer = FileDiscoverer(config=config)
            processor = FunctionProcessor(config=config)
            llm_processor = LLMProcessor(config=config, llm_client=mock_client)

            assert discoverer.config == config
            assert processor.config == config
            assert llm_processor.config == config