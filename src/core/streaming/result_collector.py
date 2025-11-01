"""
Result collector component for streaming test generation.

This component is responsible for collecting, organizing, and saving generated test
results to the filesystem. It provides proper file organization, aggregation,
and final reporting capabilities.
"""

import asyncio
import time
from typing import AsyncIterator, Dict, Any, Optional, List, Set
from pathlib import Path
import json

from .interfaces import (
    StreamProcessor, StreamPacket, StreamStage, StreamingConfiguration,
    FunctionStreamData, StreamObserver, StreamMetrics
)
from src.utils.logging_utils import get_logger
from src.test_generation.models import GenerationResult
from src.utils.file_organizer import TestFileOrganizer


class TestSuiteAggregator:
    """Aggregates test results by suite"""

    def __init__(self):
        self.suites: Dict[str, List[GenerationResult]] = {}
        self.function_counts: Dict[str, int] = {}

    def add_result(self, result: GenerationResult) -> None:
        """Add a generation result to the appropriate suite"""
        suite_name = result.task.suite_name
        if suite_name not in self.suites:
            self.suites[suite_name] = []
            self.function_counts[suite_name] = 0

        self.suites[suite_name].append(result)
        self.function_counts[suite_name] += 1

    def get_suite_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics for each suite"""
        summary = {}
        for suite_name, results in self.suites.items():
            successful = sum(1 for r in results if r.success)
            total = len(results)
            total_test_length = sum(r.test_length for r in results if r.success)

            summary[suite_name] = {
                "total_functions": total,
                "successful_generations": successful,
                "failed_generations": total - successful,
                "success_rate": successful / total if total > 0 else 0,
                "total_test_length": total_test_length,
                "average_test_length": total_test_length / successful if successful > 0 else 0
            }

        return summary

    def get_all_results(self) -> List[GenerationResult]:
        """Get all results across all suites"""
        all_results = []
        for results in self.suites.values():
            all_results.extend(results)
        return all_results


class ResultCollector(StreamProcessor):
    """
    Stream processor for collecting and organizing test generation results.

    This processor takes generation result packets and saves them to the filesystem
    while maintaining proper organization, aggregation, and reporting capabilities.
    """

    def __init__(
        self,
        config: StreamingConfiguration,
        output_dir: str,
        observers: Optional[List[StreamObserver]] = None,
        file_organizer: Optional[TestFileOrganizer] = None
    ):
        """
        Initialize result collector

        Args:
            config: Streaming configuration
            output_dir: Directory to save test files
            observers: Optional observers for monitoring
            file_organizer: Optional file organizer for advanced organization
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.observers = observers or []
        self.logger = get_logger(__name__)

        # Initialize components
        self.file_organizer = file_organizer or TestFileOrganizer(str(self.output_dir))
        self.suite_aggregator = TestSuiteAggregator()

        # Statistics
        self._collected_count = 0
        self._saved_count = 0
        self._failed_count = 0
        self._start_time = time.time()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def process(self, packet: StreamPacket) -> AsyncIterator[StreamPacket]:
        """
        Process result packet and save test files

        Args:
            packet: Input packet containing generation result

        Yields:
            StreamPacket: Result packet with file path information
        """
        if packet.stage != StreamStage.RESULT_COLLECTION:
            self.logger.warning(f"Unexpected packet stage: {packet.stage}")
            return

        try:
            generation_result = packet.data.get("generation_result")
            if not generation_result:
                self.logger.warning("No generation_result found in packet")
                return

            self._collected_count += 1

            # Add to suite aggregator
            self.suite_aggregator.add_result(generation_result)

            # Save test file if generation was successful
            output_path = None
            if generation_result.success and generation_result.test_code.strip():
                output_path = await self._save_test_file(generation_result, packet)
                if output_path:
                    self._saved_count += 1
                else:
                    self._failed_count += 1
            else:
                self._failed_count += 1
                self.logger.warning(
                    f"Skipping save for failed generation: {generation_result.function_name}"
                )

            # Create final result packet
            final_packet = StreamPacket(
                stage=StreamStage.COMPLETED,
                data={
                    "generation_result": generation_result,
                    "output_path": str(output_path) if output_path else None,
                    "collection_status": "success" if output_path else "failed",
                    "collection_sequence": self._collected_count,
                    "source_packet_id": packet.packet_id
                },
                timestamp=time.time(),
                packet_id=f"{packet.packet_id}-collected-{self._collected_count}"
            )

            # Notify observers
            await self._notify_observers_packet_processed(final_packet, 0.0)

            self.logger.debug(
                f"Collected result for: {generation_result.function_name} "
                f"(#{self._collected_count}, saved: {output_path is not None})"
            )
            yield final_packet

        except Exception as e:
            self.logger.error(f"Error in result collection: {e}")
            await self._notify_observers_error(packet, e)
            raise

    async def _save_test_file(
        self,
        generation_result: GenerationResult,
        source_packet: StreamPacket
    ) -> Optional[Path]:
        """
        Save test code to filesystem

        Args:
            generation_result: Generation result with test code
            source_packet: Source packet for context

        Returns:
            Path to saved file, or None if save failed
        """
        try:
            # Generate filename
            filename = self._generate_filename(generation_result)
            output_path = self.output_dir / filename

            # Handle filename conflicts
            if output_path.exists():
                output_path = self._resolve_filename_conflict(output_path)

            # Write test file with header
            test_content = self._format_test_content(generation_result, source_packet)

            # Write file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, output_path.write_text, test_content, 'utf-8')

            self.logger.debug(f"Saved test file: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to save test file for {generation_result.function_name}: {e}")
            return None

    def _generate_filename(self, generation_result: GenerationResult) -> str:
        """Generate filename for test file"""
        function_name = generation_result.function_name
        language = generation_result.task.language

        # Use language-appropriate extension
        extension = ".cpp" if language == "cpp" else ".c"
        return f"test_{function_name}{extension}"

    def _resolve_filename_conflict(self, original_path: Path) -> Path:
        """Resolve filename conflicts by adding numeric suffix"""
        base_name = original_path.stem
        extension = original_path.suffix
        parent = original_path.parent

        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def _format_test_content(
        self,
        generation_result: GenerationResult,
        source_packet: StreamPacket
    ) -> str:
        """
        Format test content with proper headers and metadata

        Args:
            generation_result: Generation result
            source_packet: Source packet for additional context

        Returns:
            Formatted test content
        """
        function_info = generation_result.task.function_info
        function_name = function_info.get("name", "unknown")
        source_file = function_info.get("file", "unknown")
        language = generation_result.task.language

        # Generate header comment
        header_lines = [
            f"// Generated test for {function_name}",
            f"// Source file: {source_file}",
            f"// Generated by: ai-dt streaming architecture",
            f"// Generation time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"// Model: {generation_result.model}",
            ""
        ]

        # Add includes based on language
        if language == "cpp":
            header_lines.extend([
                "#include <gtest/gtest.h>",
                "#include <mockcpp/mockcpp.hpp>",
                ""
            ])
        else:
            header_lines.extend([
                "#include <gtest/gtest.h>",
                "#include <mockcpp/mockcpp.hpp>",
                ""
            ])

        # Add function-related includes if available
        if source_file and source_file != "unknown":
            header_line = f'#include "{source_file}"'
            if not header_line in header_lines:
                header_lines.append(header_line)

        # Combine header with generated test code
        formatted_content = "\n".join(header_lines) + "\n\n"
        formatted_content += generation_result.test_code

        # Add footer if needed
        if not formatted_content.endswith("\n"):
            formatted_content += "\n"

        return formatted_content

    async def generate_aggregated_report(self) -> Optional[Path]:
        """
        Generate aggregated report of all collected results

        Returns:
            Path to generated report file, or None if failed
        """
        try:
            report_data = {
                "generation_summary": {
                    "total_functions": self._collected_count,
                    "successful_generations": self._saved_count,
                    "failed_generations": self._failed_count,
                    "success_rate": self._saved_count / max(self._collected_count, 1),
                    "processing_time": time.time() - self._start_time
                },
                "suite_summary": self.suite_aggregator.get_suite_summary(),
                "generated_files": self._get_generated_files_list()
            }

            report_path = self.output_dir / "generation_report.json"

            # Write report asynchronously
            loop = asyncio.get_event_loop()
            report_json = json.dumps(report_data, indent=2)
            await loop.run_in_executor(None, report_path.write_text, report_json, 'utf-8')

            self.logger.info(f"Generated aggregated report: {report_path}")
            return report_path

        except Exception as e:
            self.logger.error(f"Failed to generate aggregated report: {e}")
            return None

    def _get_generated_files_list(self) -> List[Dict[str, Any]]:
        """Get list of all generated test files"""
        files = []
        for result in self.suite_aggregator.get_all_results():
            if result.success:
                files.append({
                    "function_name": result.function_name,
                    "suite_name": result.task.suite_name,
                    "target_filepath": result.task.target_filepath,
                    "test_length": result.test_length,
                    "model": result.model
                })
        return files

    async def cleanup(self):
        """Cleanup resources and log final statistics"""
        duration = time.time() - self._start_time

        # Generate final report
        await self.generate_aggregated_report()

        self.logger.info(
            f"Result collection completed: {self._saved_count}/{self._collected_count} files saved "
            f"in {duration:.2f}s"
        )
        self.logger.info(
            f"Collection Statistics: "
            f"Success Rate: {self._saved_count/max(self._collected_count, 1)*100:.1f}%, "
            f"Throughput: {self._collected_count/duration:.2f} files/sec"
        )

        # Log suite summaries
        suite_summary = self.suite_aggregator.get_suite_summary()
        if suite_summary:
            self.logger.info("Suite Summary:")
            for suite_name, stats in suite_summary.items():
                self.logger.info(
                    f"  {suite_name}: {stats['successful_generations']}/{stats['total_functions']} "
                    f"({stats['success_rate']*100:.1f}% success)"
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
    def collected_count(self) -> int:
        """Get the number of results collected so far"""
        return self._collected_count

    @property
    def saved_count(self) -> int:
        """Get the number of files saved so far"""
        return self._saved_count

    @property
    def success_rate(self) -> float:
        """Get the success rate of file saving"""
        return self._saved_count / max(self._collected_count, 1)

    @property
    def suite_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics for all suites"""
        return self.suite_aggregator.get_suite_summary()