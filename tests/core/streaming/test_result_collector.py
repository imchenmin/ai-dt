"""
Test cases for ResultCollector component following TDD principles.

These tests define expected behavior before implementation.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncIterator, List, Dict, Any

from src.core.streaming.interfaces import (
    StreamStage, StreamPacket, StreamProcessor, StreamingConfiguration,
    FunctionStreamData, StreamMetrics, StreamObserver
)
from src.test_generation.models import GenerationResult, GenerationTask


class MockResultCollector(StreamProcessor):
    """Mock ResultCollector for testing interface compliance"""

    def __init__(self, should_fail: bool = False, output_dir: str = None):
        self.should_fail = should_fail
        self.output_dir = output_dir
        self.collected_results = []
        self.saved_files = []

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        if self.should_fail:
            raise RuntimeError("Result collection failed")

        generation_result = packet.data.get("generation_result")
        if not generation_result:
            return

        self.collected_results.append(generation_result)

        # Mock file saving
        if self.output_dir:
            output_path = Path(self.output_dir) / f"test_{generation_result.function_name}.cpp"
            self.saved_files.append(str(output_path))

        # Create final result packet
        final_packet = StreamPacket(
            stage=StreamStage.COMPLETED,
            data={
                "generation_result": generation_result,
                "output_path": self.saved_files[-1] if self.saved_files else None,
                "collection_status": "success",
                "source_packet_id": packet.packet_id
            },
            timestamp=packet.timestamp,
            packet_id=f"{packet.packet_id}-collected"
        )

        yield final_packet

    async def cleanup(self):
        pass


class TestResultCollector:
    """Test ResultCollector component behavior"""

    @pytest.fixture
    def result_packet(self):
        """Sample result packet for collection"""
        function_info = {
            "name": "calculate_sum",
            "return_type": "int",
            "parameters": [
                {"name": "a", "type": "int"},
                {"name": "b", "type": "int"}
            ]
        }

        function_data = FunctionStreamData(
            file_path="src/math.c",
            function_info=function_info,
            compile_args=["-O2", "-Wall"],
            priority=2
        )

        task = GenerationTask(
            function_info=function_info,
            context={},
            target_filepath="test_calculate_sum.cpp",
            suite_name="MathTestSuite"
        )

        result = GenerationResult(
            task=task,
            success=True,
            test_code="""
// Test for calculate_sum
TEST(MathTestSuite, CalculateSumTest) {
    EXPECT_EQ(calculate_sum(2, 3), 5);
    EXPECT_EQ(calculate_sum(-1, 1), 0);
}
""",
            prompt="Generate test for calculate_sum function",
            model="test-model",
            test_length=120
        )

        return StreamPacket(
            stage=StreamStage.RESULT_COLLECTION,
            data={
                "generation_result": result,
                "function_stream_data": function_data,
                "source_packet_id": "llm-packet-1"
            },
            timestamp=1234567890.0,
            packet_id="result-packet-1"
        )

    @pytest.fixture
    def failed_result_packet(self):
        """Sample failed result packet"""
        function_info = {"name": "failing_function"}

        task = GenerationTask(
            function_info=function_info,
            context={},
            target_filepath="test_failing_function.cpp",
            suite_name="FailTestSuite"
        )

        result = GenerationResult(
            task=task,
            success=False,
            test_code="",
            prompt="Generate test for failing_function",
            model="test-model",
            error="LLM generation failed"
        )

        return StreamPacket(
            stage=StreamStage.RESULT_COLLECTION,
            data={
                "generation_result": result,
                "function_stream_data": FunctionStreamData(
                    file_path="src/fail.c",
                    function_info=function_info,
                    compile_args=[]
                ),
                "source_packet_id": "llm-packet-failed"
            },
            timestamp=1234567890.0,
            packet_id="result-packet-failed"
        )

    @pytest.mark.asyncio
    async def test_successful_result_collection(self, result_packet):
        """Test successful collection of generation results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = MockResultCollector(output_dir=temp_dir)

            results = []
            async for packet in collector.process(result_packet):
                results.append(packet)

            assert len(results) == 1
            assert results[0].stage == StreamStage.COMPLETED
            assert results[0].data["collection_status"] == "success"

            # Check result preservation
            collected_result = results[0].data["generation_result"]
            assert collected_result.success is True
            assert collected_result.function_name == "calculate_sum"

            # Check file path assignment
            output_path = results[0].data["output_path"]
            assert output_path is not None
            assert output_path.endswith("test_calculate_sum.cpp")

    @pytest.mark.asyncio
    async def test_failed_result_collection(self, failed_result_packet):
        """Test collection of failed generation results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = MockResultCollector(output_dir=temp_dir)

            results = []
            async for packet in collector.process(failed_result_packet):
                results.append(packet)

            assert len(results) == 1
            collected_result = results[0].data["generation_result"]
            assert collected_result.success is False
            assert "LLM generation failed" in collected_result.error

    @pytest.mark.asyncio
    async def test_result_collection_error_handling(self, result_packet):
        """Test result collection error handling"""
        collector = MockResultCollector(should_fail=True)

        with pytest.raises(RuntimeError, match="Result collection failed"):
            async for _ in collector.process(result_packet):
                pass

    @pytest.mark.asyncio
    async def test_result_collection_with_missing_data(self):
        """Test result collection with missing generation result"""
        collector = MockResultCollector()

        invalid_packet = StreamPacket(
            stage=StreamStage.RESULT_COLLECTION,
            data={"invalid": "data"},  # Missing generation_result
            timestamp=1234567890.0,
            packet_id="invalid-packet"
        )

        # Should handle gracefully without crashing
        results = []
        async for packet in collector.process(invalid_packet):
            results.append(packet)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_batch_result_collection(self):
        """Test collection of multiple results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = MockResultCollector(output_dir=temp_dir)

            # Create multiple result packets
            packets = []
            for i in range(3):
                function_info = {"name": f"function_{i}"}
                task = GenerationTask(
                    function_info=function_info,
                    context={},
                    target_filepath=f"test_function_{i}.cpp",
                    suite_name=f"TestSuite{i}"
                )

                result = GenerationResult(
                    task=task,
                    success=True,
                    test_code=f"// Test for function_{i}",
                    model="test-model"
                )

                packet = StreamPacket(
                    stage=StreamStage.RESULT_COLLECTION,
                    data={
                        "generation_result": result,
                        "function_stream_data": FunctionStreamData(
                            file_path=f"src/file_{i}.c",
                            function_info=function_info,
                            compile_args=[]
                        )
                    },
                    timestamp=1234567890.0 + i,
                    packet_id=f"result-packet-{i}"
                )
                packets.append(packet)

            # Process all packets
            all_results = []
            for packet in packets:
                async for result in collector.process(packet):
                    all_results.append(result)

            assert len(all_results) == 3
            assert len(collector.collected_results) == 3
            assert len(collector.saved_files) == 3

    @pytest.mark.asyncio
    async def test_result_collection_file_organization(self):
        """Test that result collection organizes files properly"""
        # This test will drive implementation of proper file organization
        pytest.skip("File organization implementation pending")

    @pytest.mark.asyncio
    async def test_result_collection_aggregation(self):
        """Test that result collection can aggregate results by suite"""
        # This test will drive implementation of result aggregation
        pytest.skip("Result aggregation implementation pending")

    @pytest.mark.asyncio
    async def test_result_collection_with_real_file_operations(self):
        """Test result collection with actual file I/O operations"""
        # This test will drive implementation of real file saving
        pytest.skip("Real file operations implementation pending")

    def test_result_collector_immutability(self, result_packet):
        """Test that result collection doesn't modify input packets"""
        collector = MockResultCollector()

        original_data = result_packet.data.copy()

        # Process synchronously to test immutability
        asyncio.run(collector.process(result_packet).__anext__())

        # Original packet should be unchanged
        assert result_packet.data == original_data

    @pytest.mark.asyncio
    async def test_result_collection_metrics(self, result_packet):
        """Test that result collection collects proper metrics"""
        collector = MockResultCollector()

        results = []
        async for packet in collector.process(result_packet):
            results.append(packet)

        # Check that collection is recorded
        assert len(collector.collected_results) == 1
        assert collector.collected_results[0].success is True

    def test_output_path_generation(self):
        """Test output path generation for different scenarios"""
        test_cases = [
            ("calculate_sum", "test_calculate_sum.cpp"),
            ("process_data", "test_process_data.cpp"),
            ("complex_function_name", "test_complex_function_name.cpp")
        ]

        for function_name, expected_filename in test_cases:
            function_info = {"name": function_name}
            task = GenerationTask(
                function_info=function_info,
                context={},
                target_filepath=expected_filename,
                suite_name="TestSuite"
            )

            result = GenerationResult(task=task, success=True, test_code="// test")

            assert result.function_name == function_name

    @pytest.mark.asyncio
    async def test_result_collection_with_duplicates(self):
        """Test handling of duplicate function results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = MockResultCollector(output_dir=temp_dir)

            # Create two packets for the same function
            function_info = {"name": "duplicate_function"}
            task = GenerationTask(
                function_info=function_info,
                context={},
                target_filepath="test_duplicate_function.cpp",
                suite_name="TestSuite"
            )

            result1 = GenerationResult(
                task=task,
                success=True,
                test_code="// First test",
                model="test-model"
            )

            result2 = GenerationResult(
                task=task,
                success=True,
                test_code="// Second test",
                model="test-model"
            )

            packet1 = StreamPacket(
                stage=StreamStage.RESULT_COLLECTION,
                data={"generation_result": result1},
                timestamp=1234567890.0,
                packet_id="packet-1"
            )

            packet2 = StreamPacket(
                stage=StreamStage.RESULT_COLLECTION,
                data={"generation_result": result2},
                timestamp=1234567891.0,
                packet_id="packet-2"
            )

            # Process both packets
            all_results = []
            async for result in collector.process(packet1):
                all_results.append(result)
            async for result in collector.process(packet2):
                all_results.append(result)

            # Should handle both results
            assert len(all_results) == 2
            assert len(collector.collected_results) == 2

            # Results should be different
            assert collector.collected_results[0].test_code != collector.collected_results[1].test_code