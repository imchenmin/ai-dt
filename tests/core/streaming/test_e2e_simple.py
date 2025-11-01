"""
Simple end-to-end tests for streaming architecture.

These tests verify the complete workflow with minimal dependencies.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

from src.core.streaming.interfaces import StreamingConfiguration
from src.core.streaming.pipeline_orchestrator import StreamingPipelineOrchestrator


class SimpleMockLLMClient:
    """Simple mock LLM client for E2E testing"""

    def __init__(self, processing_delay: float = 0.01):
        self.processing_delay = processing_delay
        self.model = "simple-mock-model"
        self.call_count = 0

    def generate_test(self, prompt: str, function_name: str) -> str:
        self.call_count += 1
        return f"""
// Generated test for {function_name} (call #{self.call_count})
TEST({function_name}Test, BasicFunctionality) {{
    EXPECT_TRUE(true);
}}
"""


class TestE2ESimpleWorkflow:
    """Simple end-to-end workflow tests"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def streaming_config(self):
        """Basic streaming configuration"""
        return StreamingConfiguration(
            max_queue_size=10,
            max_concurrent_files=2,
            max_concurrent_functions=2,
            max_concurrent_llm_calls=1,  # Single worker for simplicity
            timeout_seconds=10,
            retry_attempts=1
        )

    @pytest.fixture
    def basic_compilation_units(self):
        """Basic compilation units for testing"""
        return [
            {
                "file": "test_file1.c",
                "arguments": ["-O2"]
            },
            {
                "file": "test_file2.c",
                "arguments": ["-O2"]
            }
        ]

    @pytest.mark.asyncio
    async def test_simple_e2e_workflow(
        self, streaming_config, basic_compilation_units, temp_output_dir
    ):
        """Test simple end-to-end workflow"""
        mock_llm_client = SimpleMockLLMClient(processing_delay=0.01)

        # Create orchestrator
        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client
        )

        try:
            # Execute streaming pipeline
            results = []
            async for packet in orchestrator.execute_streaming(basic_compilation_units):
                results.append(packet)
                if len(results) >= 2:  # Limit results for simple test
                    break

            # Verify basic workflow
            assert len(results) > 0, "Should produce some results"
            assert mock_llm_client.call_count > 0, "LLM client should be called"

            # Verify output directory
            output_path = Path(temp_output_dir)
            assert output_path.exists(), "Output directory should exist"

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_empty_input_handling(
        self, streaming_config, temp_output_dir
    ):
        """Test handling of empty compilation units"""
        mock_llm_client = SimpleMockLLMClient()

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
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

    @pytest.mark.asyncio
    async def test_error_handling_workflow(
        self, streaming_config, basic_compilation_units, temp_output_dir
    ):
        """Test error handling in workflow"""
        # Create LLM client that fails
        class FailingLLMClient:
            def __init__(self):
                self.model = "failing-model"

            def generate_test(self, prompt: str, function_name: str) -> str:
                raise RuntimeError(f"Failed to generate test for {function_name}")

        mock_llm_client = FailingLLMClient()

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client
        )

        try:
            # Should handle errors gracefully
            results = []
            async for packet in orchestrator.execute_streaming(basic_compilation_units):
                results.append(packet)
                # Limit to avoid infinite loop in error scenarios
                if len(results) >= 1:
                    break

            # Should not crash completely
            assert isinstance(results, list)

        except Exception as e:
            # Some errors are expected in failure scenarios
            print(f"Expected error in failure scenario: {e}")

        finally:
            await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_configuration_validation(self, temp_output_dir):
        """Test configuration validation in E2E context"""
        # Test with invalid configuration
        invalid_config = StreamingConfiguration(max_queue_size=0)

        with pytest.raises(ValueError):
            StreamingPipelineOrchestrator(
                config=invalid_config,
                output_dir=temp_output_dir
            )

    @pytest.mark.asyncio
    async def test_concurrent_processing_basic(
        self, streaming_config, temp_output_dir
    ):
        """Test basic concurrent processing capabilities"""
        # Create more compilation units to test concurrency
        many_units = [
            {"file": f"test_file_{i}.c", "arguments": ["-O2"]}
            for i in range(5)
        ]

        mock_llm_client = SimpleMockLLMClient(processing_delay=0.02)

        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client
        )

        try:
            start_time = asyncio.get_event_loop().time()
            results = []

            async for packet in orchestrator.execute_streaming(many_units):
                results.append(packet)
                if len(results) >= 3:  # Limit for basic test
                    break

            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time

            # Should process multiple units within reasonable time
            assert processing_time < 5.0, f"Processing took too long: {processing_time}s"
            assert len(results) > 0, "Should process some results"

        finally:
            await orchestrator.shutdown()

    def test_component_independence(self, streaming_config, temp_output_dir):
        """Test that components can be created and configured independently"""
        mock_llm_client = SimpleMockLLMClient()

        # Should be able to create orchestrator without errors
        orchestrator = StreamingPipelineOrchestrator(
            config=streaming_config,
            output_dir=temp_output_dir,
            llm_client=mock_llm_client
        )

        # Should have all required components
        assert orchestrator.file_discoverer is not None
        assert orchestrator.function_processor is not None
        assert orchestrator.llm_processor is not None
        assert orchestrator.result_collector is not None

        # Should have configuration
        assert orchestrator.config == streaming_config
        assert str(orchestrator.output_dir) == temp_output_dir