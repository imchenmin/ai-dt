"""
Migration adapter for transitioning from legacy to streaming architecture.

This adapter provides a compatibility layer that allows users to gradually
migrate from the legacy test generation to the streaming architecture.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncIterator
from pathlib import Path

from .streaming_service import StreamingTestGenerationService
from src.utils.logging_utils import get_logger
from src.test_generation.service import TestGenerationService as LegacyService


class MigrationAdapter:
    """
    Adapter for gradual migration from legacy to streaming architecture.

    This adapter determines which architecture to use based on configuration
    and provides a unified interface for both approaches.
    """

    def __init__(self, config_path: str = "config/test_generation.yaml"):
        """
        Initialize migration adapter

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.logger = get_logger(__name__)
        self._config = self._load_config()
        self._streaming_enabled = self._should_use_streaming()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}

    def _should_use_streaming(self) -> bool:
        """Determine if streaming architecture should be used"""
        # Check global streaming setting
        streaming_config = self._config.get('streaming', {})
        if streaming_config.get('enabled', False):
            return True

        # Check profile-specific streaming setting
        # (This would be set when a specific profile is selected)
        return False

    def create_service(self, force_streaming: bool = None) -> Any:
        """
        Create appropriate service based on configuration

        Args:
            force_streaming: Force streaming (None = use config)

        Returns:
            Legacy service or streaming service instance
        """
        use_streaming = force_streaming if force_streaming is not None else self._streaming_enabled

        if use_streaming:
            self.logger.info("Using streaming test generation service")
            return StreamingTestGenerationService()
        else:
            self.logger.info("Using legacy test generation service")
            return LegacyService()

    async def generate_tests(
        self,
        project_path: str,
        compile_commands: str,
        output_dir: str = "./experiment/generated_tests",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_workers: int = 3,
        use_streaming: Optional[bool] = None,
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate tests using appropriate architecture

        Args:
            project_path: Project root directory
            compile_commands: Path to compile_commands.json
            output_dir: Output directory
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            max_workers: Number of concurrent workers (legacy only)
            use_streaming: Force streaming (None = use config)
            progress_callback: Progress callback function
            **kwargs: Additional arguments

        Returns:
            List of generation results
        """
        use_streaming_arch = use_streaming if use_streaming is not None else self._streaming_enabled

        if use_streaming_arch:
            return await self._generate_tests_streaming(
                project_path, compile_commands, output_dir,
                include_patterns, exclude_patterns, progress_callback, **kwargs
            )
        else:
            return await self._generate_tests_legacy(
                project_path, compile_commands, output_dir,
                include_patterns, exclude_patterns, max_workers, **kwargs
            )

    async def _generate_tests_streaming(
        self,
        project_path: str,
        compile_commands: str,
        output_dir: str,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
        progress_callback: Optional[callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate tests using streaming architecture"""
        service = StreamingTestGenerationService()
        results = []

        try:
            async for result in service.generate_tests_streaming(
                project_path=project_path,
                compile_commands_path=compile_commands,
                output_dir=output_dir,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                observers=[],
                progress_callback=progress_callback
            ):
                results.append(result)

        finally:
            await service.shutdown()

        return results

    async def _generate_tests_legacy(
        self,
        project_path: str,
        compile_commands: str,
        output_dir: str,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
        max_workers: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate tests using legacy architecture"""
        service = LegacyService()

        # Create project config for legacy service
        project_config = {
            'path': project_path,
            'comp_db': compile_commands,
            'include_patterns': include_patterns,
            'exclude_patterns': exclude_patterns,
            'description': f'Legacy mode project: {project_path}',
            'output_dir': output_dir
        }

        # Analyze functions
        functions_with_context = service.analyze_project_functions(project_config)

        if not functions_with_context:
            self.logger.error("No functions found to test!")
            return []

        # Generate tests
        results = service.generate_tests_with_config(functions_with_context, project_config)

        return [result.to_dict() for result in results]


class StreamingComparisonRunner:
    """
    Utility for comparing legacy vs streaming architectures.

    This is useful for validation and performance comparison during migration.
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    async def run_comparison(
        self,
        project_path: str,
        compile_commands: str,
        output_dir_base: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run both architectures and compare results

        Args:
            project_path: Project path
            compile_commands: Compile commands file
            output_dir_base: Base output directory
            include_patterns: Include patterns
            exclude_patterns: Exclude patterns

        Returns:
            Comparison results
        """
        self.logger.info("Starting architecture comparison...")

        # Create output directories
        legacy_dir = Path(output_dir_base) / "legacy_results"
        streaming_dir = Path(output_dir_base) / "streaming_results"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        streaming_dir.mkdir(parents=True, exist_ok=True)

        # Run legacy architecture
        self.logger.info("Running legacy architecture...")
        legacy_start = time.time()
        legacy_results = await self._run_legacy(
            project_path, compile_commands, str(legacy_dir),
            include_patterns, exclude_patterns
        )
        legacy_time = time.time() - legacy_start

        # Run streaming architecture
        self.logger.info("Running streaming architecture...")
        streaming_start = time.time()
        streaming_results = await self._run_streaming(
            project_path, compile_commands, str(streaming_dir),
            include_patterns, exclude_patterns
        )
        streaming_time = time.time() - streaming_start

        # Compare results
        comparison = self._compare_results(
            legacy_results, streaming_results,
            legacy_time, streaming_time
        )

        # Save comparison report
        self._save_comparison_report(comparison, output_dir_base)

        return comparison

    async def _run_legacy(
        self, project_path: str, compile_commands: str, output_dir: str,
        include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Run legacy architecture"""
        adapter = MigrationAdapter()
        adapter._streaming_enabled = False  # Force legacy mode

        return await adapter.generate_tests(
            project_path=project_path,
            compile_commands=compile_commands,
            output_dir=output_dir,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            use_streaming=False
        )

    async def _run_streaming(
        self, project_path: str, compile_commands: str, output_dir: str,
        include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Run streaming architecture"""
        adapter = MigrationAdapter()
        adapter._streaming_enabled = True  # Force streaming mode

        return await adapter.generate_tests(
            project_path=project_path,
            compile_commands=compile_commands,
            output_dir=output_dir,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            use_streaming=True
        )

    def _compare_results(
        self,
        legacy_results: List[Dict[str, Any]],
        streaming_results: List[Dict[str, Any]],
        legacy_time: float,
        streaming_time: float
    ) -> Dict[str, Any]:
        """Compare results from both architectures"""
        # Extract successful results
        legacy_successful = [r for r in legacy_results if r.get('success', False)]
        streaming_successful = [r for r in streaming_results if r.get('success', False)]

        # Get function names
        legacy_functions = {r.get('function_name') for r in legacy_successful}
        streaming_functions = {r.get('function_name') for r in streaming_successful}

        # Calculate metrics
        common_functions = legacy_functions & streaming_functions
        legacy_only = legacy_functions - streaming_functions
        streaming_only = streaming_functions - legacy_functions

        return {
            'performance': {
                'legacy_time': legacy_time,
                'streaming_time': streaming_time,
                'speed_improvement': ((legacy_time - streaming_time) / legacy_time * 100) if legacy_time > 0 else 0,
                'streaming_faster': streaming_time < legacy_time
            },
            'results': {
                'legacy_total': len(legacy_results),
                'legacy_successful': len(legacy_successful),
                'streaming_total': len(streaming_results),
                'streaming_successful': len(streaming_successful),
                'common_functions': len(common_functions),
                'legacy_only': len(legacy_only),
                'streaming_only': len(streaming_only)
            },
            'compatibility': {
                'success_rate_agreement': (
                    len(common_functions) / max(len(legacy_functions) + len(streaming_functions), 1) * 100
                ),
                'compatible': len(common_functions) > 0
            },
            'details': {
                'legacy_only_functions': list(legacy_only),
                'streaming_only_functions': list(streaming_only)
            }
        }

    def _save_comparison_report(self, comparison: Dict[str, Any], output_dir_base: str):
        """Save comparison report to file"""
        import json
        from datetime import datetime

        report_path = Path(output_dir_base) / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_path, 'w') as f:
                json.dump(comparison, f, indent=2)
            self.logger.info(f"Comparison report saved to: {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to save comparison report: {e}")