"""
Test cases for streaming interfaces following TDD principles.

These tests define the expected behavior of streaming components before implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncIterator

from src.core.streaming.interfaces import (
    StreamStage, StreamPacket, StreamProcessor, StreamObserver,
    StreamQueue, StreamingPipelineOrchestrator, StreamingConfiguration,
    FunctionStreamData, StreamMetrics, StreamComponentFactory
)


class TestStreamPacket:
    """Test StreamPacket immutability and behavior"""

    def test_stream_packet_creation(self):
        """Test packet creation with valid data"""
        data = {"file_path": "test.c", "function": "test_func"}
        packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data=data,
            timestamp=1234567890.0,
            packet_id="test-packet-1"
        )

        assert packet.stage == StreamStage.FILE_DISCOVERY
        assert packet.data == data
        assert packet.timestamp == 1234567890.0
        assert packet.packet_id == "test-packet-1"

    def test_stream_packet_with_stage(self):
        """Test creating packet with different stage"""
        original = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"test": "data"},
            timestamp=1234567890.0,
            packet_id="test-1"
        )

        new_packet = original.with_stage(StreamStage.FUNCTION_PROCESSING)

        # Should have new stage but same data
        assert new_packet.stage == StreamStage.FUNCTION_PROCESSING
        assert new_packet.data == original.data
        assert new_packet.timestamp == original.timestamp
        assert new_packet.packet_id == original.packet_id

    def test_stream_packet_immutability(self):
        """Test that packet is immutable"""
        packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"test": "data"},
            timestamp=1234567890.0,
            packet_id="test-1"
        )

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            packet.stage = StreamStage.FUNCTION_PROCESSING

        with pytest.raises(AttributeError):
            packet.data = {"new": "data"}


class TestFunctionStreamData:
    """Test FunctionStreamData immutability and behavior"""

    def test_function_stream_data_creation(self):
        """Test creation with valid function data"""
        function_info = {
            "name": "test_function",
            "return_type": "int",
            "parameters": []
        }
        data = FunctionStreamData(
            file_path="test.c",
            function_info=function_info,
            compile_args=["-O2", "-Wall"]
        )

        assert data.file_path == "test.c"
        assert data.function_info == function_info
        assert data.compile_args == ["-O2", "-Wall"]
        assert data.priority == 0

    def test_function_stream_data_with_priority(self):
        """Test creating data with different priority"""
        original = FunctionStreamData(
            file_path="test.c",
            function_info={"name": "test"},
            compile_args=["-O2"],
            priority=0
        )

        new_data = original.with_priority(5)

        assert new_data.priority == 5
        assert new_data.file_path == original.file_path
        assert new_data.function_info == original.function_info
        assert new_data.compile_args == original.compile_args


class TestStreamingConfiguration:
    """Test StreamingConfiguration validation and behavior"""

    def test_valid_configuration(self):
        """Test creating valid configuration"""
        config = StreamingConfiguration(
            max_queue_size=50,
            max_concurrent_files=2,
            max_concurrent_functions=4,
            max_concurrent_llm_calls=2
        )

        assert config.max_queue_size == 50
        assert config.max_concurrent_files == 2
        assert config.max_concurrent_functions == 4
        assert config.max_concurrent_llm_calls == 2

    def test_default_configuration(self):
        """Test default configuration values"""
        config = StreamingConfiguration()

        assert config.max_queue_size == 100
        assert config.max_concurrent_files == 3
        assert config.max_concurrent_functions == 5
        assert config.max_concurrent_llm_calls == 3
        assert config.enable_prioritization is True
        assert config.timeout_seconds == 300
        assert config.retry_attempts == 3
        assert config.enable_metrics is True

    def test_configuration_validation_invalid_values(self):
        """Test configuration rejects invalid values"""
        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            config = StreamingConfiguration(max_queue_size=0)
            config.validate()

        with pytest.raises(ValueError, match="max_concurrent_files must be positive"):
            config = StreamingConfiguration(max_concurrent_files=-1)
            config.validate()

        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            config = StreamingConfiguration(timeout_seconds=0)
            config.validate()

        with pytest.raises(ValueError, match="retry_attempts must be non-negative"):
            config = StreamingConfiguration(retry_attempts=-1)
            config.validate()

    def test_configuration_validation_valid_values(self):
        """Test configuration accepts valid values"""
        config = StreamingConfiguration(
            max_queue_size=1,
            max_concurrent_files=1,
            max_concurrent_functions=1,
            max_concurrent_llm_calls=1,
            timeout_seconds=1,
            retry_attempts=0
        )

        # Should not raise exception
        config.validate()


class MockStreamProcessor(StreamProcessor):
    """Mock implementation of StreamProcessor for testing"""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.processed_packets = []
        self.cleanup_called = False

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        self.processed_packets.append(packet)

        if self.should_fail:
            raise RuntimeError("Mock processor failure")

        # Simple transformation: advance to next stage
        next_stage = {
            StreamStage.FILE_DISCOVERY: StreamStage.FUNCTION_PROCESSING,
            StreamStage.FUNCTION_PROCESSING: StreamStage.LLM_PROCESSING,
            StreamStage.LLM_PROCESSING: StreamStage.RESULT_COLLECTION,
            StreamStage.RESULT_COLLECTION: StreamStage.COMPLETED
        }.get(packet.stage, StreamStage.COMPLETED)

        yield packet.with_stage(next_stage)

    async def cleanup(self):
        self.cleanup_called = True


class TestStreamProcessor:
    """Test StreamProcessor interface contract"""

    @pytest.mark.asyncio
    async def test_processor_successful_processing(self):
        """Test successful packet processing"""
        processor = MockStreamProcessor()

        packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"test": "data"},
            timestamp=1234567890.0,
            packet_id="test-1"
        )

        results = []
        async for result in processor.process(packet):
            results.append(result)

        assert len(results) == 1
        assert results[0].stage == StreamStage.FUNCTION_PROCESSING
        assert results[0].data == packet.data
        assert packet in processor.processed_packets

    @pytest.mark.asyncio
    async def test_processor_error_handling(self):
        """Test processor error handling"""
        processor = MockStreamProcessor(should_fail=True)

        packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"test": "data"},
            timestamp=1234567890.0,
            packet_id="test-1"
        )

        with pytest.raises(RuntimeError, match="Mock processor failure"):
            async for _ in processor.process(packet):
                pass

    @pytest.mark.asyncio
    async def test_processor_cleanup(self):
        """Test processor cleanup"""
        processor = MockStreamProcessor()
        await processor.cleanup()

        assert processor.cleanup_called is True


class MockStreamObserver(StreamObserver):
    """Mock implementation of StreamObserver for testing"""

    def __init__(self):
        self.packets_processed = []
        self.errors_occurred = []
        self.stage_changes = []

    async def on_packet_processed(self, packet: StreamPacket, processing_time: float):
        self.packets_processed.append((packet, processing_time))

    async def on_error_occurred(self, packet: StreamPacket, error: Exception):
        self.errors_occurred.append((packet, error))

    async def on_stage_changed(self, stage: StreamStage, metrics: StreamMetrics):
        self.stage_changes.append((stage, metrics))


class TestStreamObserver:
    """Test StreamObserver interface contract"""

    @pytest.mark.asyncio
    async def test_observer_packet_processing_notification(self):
        """Test observer receives packet processing notifications"""
        observer = MockStreamObserver()

        packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"test": "data"},
            timestamp=1234567890.0,
            packet_id="test-1"
        )

        await observer.on_packet_processed(packet, 0.5)

        assert len(observer.packets_processed) == 1
        assert observer.packets_processed[0][0] == packet
        assert observer.packets_processed[0][1] == 0.5

    @pytest.mark.asyncio
    async def test_observer_error_notification(self):
        """Test observer receives error notifications"""
        observer = MockStreamObserver()

        packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"test": "data"},
            timestamp=1234567890.0,
            packet_id="test-1"
        )
        error = RuntimeError("Test error")

        await observer.on_error_occurred(packet, error)

        assert len(observer.errors_occurred) == 1
        assert observer.errors_occurred[0][0] == packet
        assert observer.errors_occurred[0][1] == error

    @pytest.mark.asyncio
    async def test_observer_stage_change_notification(self):
        """Test observer receives stage change notifications"""
        observer = MockStreamObserver()

        metrics = StreamMetrics(
            packets_processed=10,
            errors_count=1,
            average_processing_time=0.5,
            current_throughput=20.0,
            memory_usage_mb=128.0
        )

        await observer.on_stage_changed(StreamStage.FUNCTION_PROCESSING, metrics)

        assert len(observer.stage_changes) == 1
        assert observer.stage_changes[0][0] == StreamStage.FUNCTION_PROCESSING
        assert observer.stage_changes[0][1] == metrics


class TestStreamMetrics:
    """Test StreamMetrics creation and immutability"""

    def test_stream_metrics_creation(self):
        """Test creating valid metrics"""
        metrics = StreamMetrics(
            packets_processed=100,
            errors_count=5,
            average_processing_time=0.75,
            current_throughput=25.0,
            memory_usage_mb=256.0
        )

        assert metrics.packets_processed == 100
        assert metrics.errors_count == 5
        assert metrics.average_processing_time == 0.75
        assert metrics.current_throughput == 25.0
        assert metrics.memory_usage_mb == 256.0


class TestStreamComponentFactory:
    """Test StreamComponentFactory interface contract"""

    def test_factory_interface_methods_exist(self):
        """Test that factory interface defines all required methods"""
        # This is a compile-time test to ensure interface completeness
        # In a real scenario, this would be caught by type checkers

        class TestFactory(StreamComponentFactory):
            def create_file_discoverer(self) -> StreamProcessor:
                pass

            def create_function_processor(self) -> StreamProcessor:
                pass

            def create_llm_processor(self) -> StreamProcessor:
                pass

            def create_result_collector(self) -> StreamProcessor:
                pass

            def create_queue(self, name: str) -> StreamQueue:
                pass

            def create_orchestrator(self, config: StreamingConfiguration) -> StreamingPipelineOrchestrator:
                pass

        # Should be able to instantiate without errors
        factory = TestFactory()
        assert factory is not None


# Integration test scenarios that will drive implementation
class TestStreamingPipelineScenarios:
    """High-level integration test scenarios for streaming pipeline"""

    @pytest.mark.asyncio
    async def test_end_to_end_single_function_streaming(self):
        """Test complete streaming pipeline for a single function"""
        # This test will drive the implementation of the full pipeline
        # It should work once all components are implemented

        pytest.skip("Implementation pending - will drive component development")

    @pytest.mark.asyncio
    async def test_concurrent_function_processing(self):
        """Test streaming pipeline with multiple functions concurrently"""
        pytest.skip("Implementation pending - will drive component development")

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self):
        """Test pipeline resilience to errors in individual components"""
        pytest.skip("Implementation pending - will drive component development")

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test that pipeline collects and reports performance metrics"""
        pytest.skip("Implementation pending - will drive component development")

    @pytest.mark.asyncio
    async def test_graceful_shutdown_and_cleanup(self):
        """Test graceful pipeline shutdown with resource cleanup"""
        pytest.skip("Implementation pending - will drive component development")