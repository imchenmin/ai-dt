"""
Test cases for FileDiscoverer component following TDD principles.

These tests define expected behavior before implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from typing import AsyncIterator

from src.core.streaming.interfaces import (
    StreamStage, StreamPacket, StreamProcessor, StreamingConfiguration
)


class MockFileDiscoverer(StreamProcessor):
    """Mock FileDiscoverer for testing interface compliance"""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.discovered_files = []

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        if self.should_fail:
            raise RuntimeError("File discovery failed")

        compilation_units = packet.data.get("compilation_units", [])

        for unit in compilation_units:
            file_path = unit.get("file")
            if file_path and file_path.endswith(('.c', '.cpp', '.h', '.hpp')):
                self.discovered_files.append(file_path)

                yield StreamPacket(
                    stage=StreamStage.FUNCTION_PROCESSING,
                    data={
                        "file_path": file_path,
                        "compile_args": unit.get("arguments", []),
                        "original_packet": packet
                    },
                    timestamp=packet.timestamp,
                    packet_id=f"{packet.packet_id}-file-{len(self.discovered_files)}"
                )

    async def cleanup(self):
        pass


class TestFileDiscoverer:
    """Test FileDiscoverer component behavior"""

    @pytest.fixture
    def sample_compilation_units(self):
        """Sample compilation data for testing"""
        return [
            {"file": "src/main.c", "arguments": ["-O2", "-Wall"]},
            {"file": "src/utils.c", "arguments": ["-O2", "-Wall"]},
            {"file": "src/main.h", "arguments": []},
            {"file": "third_party/lib.c", "arguments": ["-O2"]},
            {"file": "Makefile", "arguments": []},  # Should be ignored
            {"file": "src/test.cpp", "arguments": ["-std=c++11"]}
        ]

    @pytest.fixture
    def initial_packet(self, sample_compilation_units):
        """Initial packet for file discovery"""
        return StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"compilation_units": sample_compilation_units},
            timestamp=1234567890.0,
            packet_id="discovery-start"
        )

    @pytest.mark.asyncio
    async def test_successful_file_discovery(self, initial_packet, sample_compilation_units):
        """Test successful discovery of C/C++ files"""
        discoverer = MockFileDiscoverer()

        results = []
        async for packet in discoverer.process(initial_packet):
            results.append(packet)

        # Should discover all C/C++ files except non-source files
        expected_files = ["src/main.c", "src/utils.c", "src/main.h", "third_party/lib.c", "src/test.cpp"]
        assert len(results) == len(expected_files)

        for i, expected_file in enumerate(expected_files):
            assert results[i].data["file_path"] == expected_file
            assert results[i].stage == StreamStage.FUNCTION_PROCESSING
            assert results[i].packet_id.startswith(initial_packet.packet_id)

    @pytest.mark.asyncio
    async def test_file_discovery_error_handling(self, initial_packet):
        """Test file discovery error handling"""
        discoverer = MockFileDiscoverer(should_fail=True)

        with pytest.raises(RuntimeError, match="File discovery failed"):
            async for _ in discoverer.process(initial_packet):
                pass

    @pytest.mark.asyncio
    async def test_empty_compilation_units(self):
        """Test handling of empty compilation units"""
        discoverer = MockFileDiscoverer()

        empty_packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"compilation_units": []},
            timestamp=1234567890.0,
            packet_id="empty-discovery"
        )

        results = []
        async for packet in discoverer.process(empty_packet):
            results.append(packet)

        assert len(results) == 0
        assert len(discoverer.discovered_files) == 0

    @pytest.mark.asyncio
    async def test_file_discovery_with_filters(self):
        """Test file discovery with include/exclude filters"""
        # This test will drive implementation of filtering functionality
        pytest.skip("Filtering implementation pending")

    @pytest.mark.asyncio
    async def test_file_discovery_concurrent_processing(self):
        """Test that file discovery can handle multiple concurrent requests"""
        pytest.skip("Concurrent processing implementation pending")

    @pytest.mark.asyncio
    async def test_file_discovery_with_invalid_data(self):
        """Test file discovery robustness with invalid input data"""
        discoverer = MockFileDiscoverer()

        invalid_packet = StreamPacket(
            stage=StreamStage.FILE_DISCOVERY,
            data={"invalid": "data"},  # Missing compilation_units
            timestamp=1234567890.0,
            packet_id="invalid-discovery"
        )

        # Should handle gracefully without crashing
        results = []
        async for packet in discoverer.process(invalid_packet):
            results.append(packet)

        assert len(results) == 0

    def test_file_discovery_immutability(self, initial_packet):
        """Test that file discovery doesn't modify input packets"""
        discoverer = MockFileDiscoverer()

        original_data = initial_packet.data.copy()

        # Process synchronously to test immutability
        asyncio.run(discoverer.process(initial_packet).__anext__())

        # Original packet should be unchanged
        assert initial_packet.data == original_data