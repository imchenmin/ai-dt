"""
Comparison mode implementation for architecture comparison.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


# TODO: Import when implemented
# from src.core.streaming.comparison_runner import StreamingComparisonRunner


class ComparisonModeHandler:
    """Handler for comparison mode between architectures"""

    def __init__(self):
        pass

    async def run_comparison_mode(
        self,
        project_path: str,
        output_dir: str,
        compile_commands: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """
        Run comparison mode between legacy and streaming architectures

        Args:
            project_path: Path to the project
            output_dir: Base output directory
            compile_commands: Path to compile_commands.json
            include_patterns: Patterns to include
            exclude_patterns: Patterns to exclude
        """
        logger.info(f"Starting architecture comparison for: {project_path}")

        # For now, log a placeholder
        logger.info("Comparison mode is not yet fully implemented")
        logger.info("This will compare legacy vs streaming architectures")

        # TODO: Implement actual comparison when StreamingComparisonRunner is available
        # comparison_dir = f"{output_dir}_comparison"
        # runner = StreamingComparisonRunner()
        #
        # try:
        #     comparison = await runner.run_comparison(
        #         project_path=project_path,
        #         compile_commands=compile_commands,
        #         output_dir_base=comparison_dir,
        #         include_patterns=include_patterns,
        #         exclude_patterns=exclude_patterns
        #     )
        #
        #     self._log_comparison_results(comparison, comparison_dir)
        #
        # except Exception as e:
        #     logger.error(f"Comparison failed: {e}")

    def _log_comparison_results(
        self,
        comparison: Dict[str, Any],
        comparison_dir: str
    ) -> None:
        """Log comparison results"""
        logger.info("Architecture Comparison Results:")
        logger.info("=" * 50)

        perf = comparison['performance']
        logger.info(f"Performance:")
        logger.info(f"  Legacy time: {perf['legacy_time']:.2f}s")
        logger.info(f"  Streaming time: {perf['streaming_time']:.2f}s")
        logger.info(f"  Speed improvement: {perf['speed_improvement']:.1f}%")
        logger.info(f"  Streaming faster: {perf['streaming_faster']}")

        results = comparison['results']
        logger.info(f"Results:")
        logger.info(f"  Legacy: {results['legacy_successful']}/{results['legacy_total']} successful")
        logger.info(f"  Streaming: {results['streaming_successful']}/{results['streaming_total']} successful")
        logger.info(f"  Common functions: {results['common_functions']}")
        logger.info(f"  Legacy only: {results['legacy_only']}")
        logger.info(f"  Streaming only: {results['streaming_only']}")

        compat = comparison['compatibility']
        logger.info(f"Compatibility:")
        logger.info(f"  Success rate agreement: {compat['success_rate_agreement']:.1f}%")
        logger.info(f"  Compatible: {compat['compatible']}")

        logger.info(f"Detailed report saved to: {comparison_dir}")