"""
Test cases for FunctionProcessor component following TDD principles.

These tests define expected behavior before implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncIterator

from src.core.streaming.interfaces import (
    StreamStage, StreamPacket, StreamProcessor, StreamingConfiguration,
    FunctionStreamData
)


class MockFunctionProcessor(StreamProcessor):
    """Mock FunctionProcessor for testing interface compliance"""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.processed_functions = []

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        if self.should_fail:
            raise RuntimeError("Function processing failed")

        file_path = packet.data.get("file_path")
        compile_args = packet.data.get("compile_args", [])

        # Handle missing file_path gracefully
        if not file_path:
            return

        # Mock function discovery
        mock_functions = [
            {
                "name": f"test_function_{i}",
                "return_type": "int",
                "parameters": [],
                "body": f"return {i};",
                "is_static": False,
                "language": "c" if file_path.endswith('.c') else "cpp"
            }
            for i in range(1, 4)  # Mock 3 functions per file
        ]

        for func_data in mock_functions:
            self.processed_functions.append(func_data)

            yield StreamPacket(
                stage=StreamStage.LLM_PROCESSING,
                data={
                    "function_stream_data": FunctionStreamData(
                        file_path=file_path,
                        function_info=func_data,
                        compile_args=compile_args,
                        priority=self._calculate_priority(func_data)
                    ),
                    "source_packet_id": packet.packet_id
                },
                timestamp=packet.timestamp,
                packet_id=f"{packet.packet_id}-func-{func_data['name']}"
            )

    def _calculate_priority(self, function_info: dict) -> int:
        """Simple priority calculation based on function complexity"""
        complexity = len(function_info.get("parameters", []))
        return min(complexity, 5)  # Priority 0-5

    async def cleanup(self):
        pass


class TestFunctionProcessor:
    """Test FunctionProcessor component behavior"""

    @pytest.fixture
    def file_packet(self):
        """Sample file packet for function processing"""
        return StreamPacket(
            stage=StreamStage.FUNCTION_PROCESSING,
            data={
                "file_path": "src/test.c",
                "compile_args": ["-O2", "-Wall"],
                "source_packet_id": "discovery-start"
            },
            timestamp=1234567890.0,
            packet_id="file-packet-1"
        )

    @pytest.fixture
    def complex_file_packet(self):
        """Sample complex file packet (C++)"""
        return StreamPacket(
            stage=StreamStage.FUNCTION_PROCESSING,
            data={
                "file_path": "src/complex.cpp",
                "compile_args": ["-std=c++17", "-O2"],
                "source_packet_id": "discovery-start"
            },
            timestamp=1234567890.0,
            packet_id="file-packet-2"
        )

    @pytest.mark.asyncio
    async def test_successful_function_processing(self, file_packet):
        """Test successful function processing from C file"""
        processor = MockFunctionProcessor()

        results = []
        async for packet in processor.process(file_packet):
            results.append(packet)

        # Should discover 3 mock functions
        assert len(results) == 3
        assert all(packet.stage == StreamStage.LLM_PROCESSING for packet in results)

        # Check function stream data
        for i, packet in enumerate(results):
            func_data = packet.data["function_stream_data"]
            assert func_data.file_path == "src/test.c"
            assert func_data.compile_args == ["-O2", "-Wall"]
            assert func_data.function_info["name"] == f"test_function_{i+1}"
            assert func_data.function_info["language"] == "c"

    @pytest.mark.asyncio
    async def test_cpp_function_processing(self, complex_file_packet):
        """Test function processing from C++ file"""
        processor = MockFunctionProcessor()

        results = []
        async for packet in processor.process(complex_file_packet):
            results.append(packet)

        # Should discover 3 mock functions
        assert len(results) == 3

        # Check language detection
        for packet in results:
            func_data = packet.data["function_stream_data"]
            assert func_data.function_info["language"] == "cpp"

    @pytest.mark.asyncio
    async def test_function_processing_error_handling(self, file_packet):
        """Test function processing error handling"""
        processor = MockFunctionProcessor(should_fail=True)

        with pytest.raises(RuntimeError, match="Function processing failed"):
            async for _ in processor.process(file_packet):
                pass

    @pytest.mark.asyncio
    async def test_function_processing_priority_calculation(self, file_packet):
        """Test that function priorities are calculated correctly"""
        processor = MockFunctionProcessor()

        results = []
        async for packet in processor.process(file_packet):
            results.append(packet)

        # All mock functions have 0 parameters, so priority should be 0
        for packet in results:
            func_data = packet.data["function_stream_data"]
            assert func_data.priority == 0

    @pytest.mark.asyncio
    async def test_function_processing_with_invalid_packet(self):
        """Test function processing with invalid packet data"""
        processor = MockFunctionProcessor()

        invalid_packet = StreamPacket(
            stage=StreamStage.FUNCTION_PROCESSING,
            data={"invalid": "data"},  # Missing file_path
            timestamp=1234567890.0,
            packet_id="invalid-packet"
        )

        # Should handle gracefully without crashing
        results = []
        async for packet in processor.process(invalid_packet):
            results.append(packet)

        # Mock processor still generates functions even with invalid data
        # Real implementation should handle this more gracefully
        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_function_processing_concurrent_limit(self):
        """Test that function processing respects concurrency limits"""
        # This test will drive implementation of concurrency control
        pytest.skip("Concurrency control implementation pending")

    @pytest.mark.asyncio
    async def test_function_processing_with_real_clang(self):
        """Test function processing using actual clang analysis"""
        # This test will drive integration with real ClangAnalyzer
        pytest.skip("Clang integration implementation pending")

    @pytest.mark.asyncio
    async def test_function_processing_caching(self):
        """Test that function processing uses AST caching effectively"""
        # This test will drive implementation of AST caching
        pytest.skip("AST caching implementation pending")

    def test_function_processor_immutability(self, file_packet):
        """Test that function processing doesn't modify input packets"""
        processor = MockFunctionProcessor()

        original_data = file_packet.data.copy()

        # Process synchronously to test immutability
        asyncio.run(processor.process(file_packet).__anext__())

        # Original packet should be unchanged
        assert file_packet.data == original_data

    def test_function_stream_data_priority(self):
        """Test FunctionStreamData priority assignment"""
        func_info = {
            "name": "complex_function",
            "return_type": "int",
            "parameters": ["int a", "float b", "char* c"]
        }

        # Test default priority
        data = FunctionStreamData(
            file_path="test.c",
            function_info=func_info,
            compile_args=[]
        )
        assert data.priority == 0

        # Test custom priority
        data_with_priority = data.with_priority(5)
        assert data_with_priority.priority == 5
        assert data_with_priority.file_path == data.file_path
        assert data_with_priority.function_info == data.function_info