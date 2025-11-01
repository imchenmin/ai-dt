#!/usr/bin/env python3
"""
Main entry point for AI-Driven Test Generator
Unified command-line interface for all test generation scenarios
"""

import argparse
import logging
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.test_generation.service import TestGenerationService
from src.utils.config_manager import config_manager
from src.utils.logging_utils import get_logger, setup_logging
from src.api.server import APIServer
from src.core.streaming.streaming_service import StreamingTestGenerationService
from src.core.streaming.migration_adapter import MigrationAdapter

# Setup enhanced logging with timestamps
setup_logging()
logger = get_logger(__name__)


class TestGenerationConfig:
    """Load and manage test generation configuration"""
    
    def __init__(self, config_path: str = "config/test_generation.yaml"):
        self.config_path = config_path
        # Reinitialize config manager with custom path if needed
        if config_path != "config/test_generation.yaml":
            global config_manager
            config_manager = config_manager.__class__(config_path)
    
    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get configuration for a specific project"""
        try:
            return config_manager.get_project_config(project_name)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration"""
        try:
            return config_manager.get_llm_config(provider)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
    
    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Get execution profile configuration"""
        try:
            return config_manager.get_profile_config(profile_name)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)

def generate_tests_simple_mode(project_path: str, output_dir: str, compile_commands: str,
                               include_patterns: List[str] = None, exclude_patterns: List[str] = None):
    """Simple mode: generate tests without configuration"""
    # Create a minimal project config for simple mode
    project_config = {
        'path': project_path,
        'comp_db': compile_commands,
        'include_patterns': include_patterns,
        'exclude_patterns': exclude_patterns,
        'description': f'Simple mode project: {project_path}',
        'output_dir': output_dir
    }
    
    service = TestGenerationService()
    
    # Analyze functions
    functions_with_context = service.analyze_project_functions(project_config)
    
    if not functions_with_context:
        logger.error("No functions found to test!")
        return
    
    # Generate tests
    results = service.generate_tests_with_config(functions_with_context, project_config)
    
    # Print results
    service.print_results(results, project_config)


def generate_tests_single_file(project_path: str, file_path: str, output_dir: str, 
                               compile_commands: str, prompt_only: bool = False):
    """Generate tests for a single file only"""
    # Create a project config for single file mode
    project_config = {
        'path': project_path,
        'comp_db': compile_commands,
        'include_patterns': [file_path],
        'description': f'Single file mode: {file_path}',
        'output_dir': output_dir
    }
    
    service = TestGenerationService()
    
    # Analyze functions
    functions_with_context = service.analyze_project_functions(project_config)
    
    if not functions_with_context:
        logger.error("No testable functions found in the specified file")
        return
    
    # Generate tests
    results = service.generate_tests_with_config(functions_with_context, project_config, prompt_only)
    
    # Print results
    service.print_results(results, project_config)


def start_api_server(host: str = "0.0.0.0", port: int = 8000,
                     provider: str = "openai", reload: bool = False):
    """Start the API server"""
    logger.info(f"Starting API server with provider: {provider}")
    server = APIServer(host=host, port=port, default_provider=provider)
    server.run(reload=reload)


def start_streaming_mode(
    project_path: str,
    output_dir: str,
    compile_commands: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    force_streaming: bool = False,
    max_concurrent: int = 3,
    enable_progress: bool = False
):
    """Start streaming test generation mode"""
    logger.info(f"Starting streaming test generation for: {project_path}")

    async def run_streaming():
        # Create streaming service
        service = StreamingTestGenerationService()

        # Configure streaming parameters
        config = {
            'max_concurrent_llm_calls': max_concurrent,
            'timeout_seconds': 300,
            'retry_attempts': 3
        }

        # Progress callback
        progress_callback = None
        if enable_progress:
            def progress_callback(result, summary):
                logger.info(
                    f"Progress: {summary['successful_packets']} completed, "
                    f"throughput: {summary['throughput']:.2f} packets/sec"
                )
            progress_callback = progress_callback

        try:
            results = []
            start_time = time.time()

            # Run streaming generation
            async for result in service.generate_tests_streaming(
                project_path=project_path,
                compile_commands_path=compile_commands,
                output_dir=output_dir,
                config=config,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                progress_callback=progress_callback
            ):
                results.append(result)

                # Report first result time
                if len(results) == 1:
                    first_result_time = time.time() - start_time
                    logger.info(f"First result generated in {first_result_time:.2f}s")

            end_time = time.time()
            total_time = end_time - start_time

            # Print final results
            successful = [r for r in results if r.get('success', False)]
            failed = [r for r in results if not r.get('success', False)]

            logger.info(f"Streaming test generation completed in {total_time:.2f}s")
            logger.info(f"Results: {len(successful)} successful, {len(failed)} failed")

            if successful:
                logger.info("Successfully generated tests for:")
                for result in successful:
                    function_name = result.get('function_name', 'unknown')
                    logger.info(f"  • {function_name}")

            if failed:
                logger.warning("Failed to generate tests for:")
                for result in failed:
                    function_name = result.get('function_name', 'unknown')
                    error = result.get('error', 'Unknown error')
                    logger.warning(f"  • {function_name}: {error}")

        finally:
            await service.shutdown()

    # Run the async function
    asyncio.run(run_streaming())


def start_comparison_mode(
    project_path: str,
    output_dir: str,
    compile_commands: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
):
    """Start comparison mode between architectures"""
    logger.info(f"Starting architecture comparison for: {project_path}")

    comparison_dir = f"{output_dir}_comparison"

    async def run_comparison():
        runner = StreamingComparisonRunner()

        try:
            comparison = await runner.run_comparison(
                project_path=project_path,
                compile_commands=compile_commands,
                output_dir_base=comparison_dir,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )

            # Print comparison results
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

        except Exception as e:
            logger.error(f"Comparison failed: {e}")

    # Run the async function
    asyncio.run(run_comparison())


def main():
    parser = argparse.ArgumentParser(description="AI-Driven C/C++ Test Generator")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--simple", action="store_true",
                          help="Simple mode: specify project directly")
    mode_group.add_argument("--config", metavar="PROJECT_NAME",
                          help="Configuration mode: use project from config file")
    mode_group.add_argument("--list-projects", action="store_true",
                          help="List available projects from configuration")
    mode_group.add_argument("--single-file", metavar="FILE_PATH",
                          help="Single file mode: analyze only the specified file")
    mode_group.add_argument("--api-server", action="store_true",
                          help="Start API server mode: expose LLM client as OpenAI-compatible API")
    mode_group.add_argument("--streaming", action="store_true",
                          help="Streaming mode: use new streaming architecture for improved performance")
    mode_group.add_argument("--compare", action="store_true",
                          help="Comparison mode: run both architectures and compare results")
    
    # Simple mode arguments
    parser.add_argument("-p", "--project", help="Project root directory (simple mode)")
    parser.add_argument("-o", "--output", default="./experiment/generated_tests", 
                      help="Output directory (simple mode)")
    parser.add_argument("--compile-commands", default="compile_commands.json", 
                      help="Path to compile_commands.json (simple mode)")
    parser.add_argument("--include", nargs='+', 
                      help="Include only files/folders matching these patterns (simple mode)")
    parser.add_argument("--exclude", nargs='+', 
                      help="Exclude files/folders matching these patterns (simple mode)")
    
    # Configuration mode arguments
    parser.add_argument("--config-file", default="config/test_generation.yaml",
                      help="Path to configuration file (config mode)")
    parser.add_argument("--profile", default="comprehensive",
                      help="Execution profile (quick, comprehensive, custom)")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Only generate prompts and skip LLM requests.")
    
    # API server arguments
    parser.add_argument("--host", default="0.0.0.0",
                      help="API server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                      help="API server port (default: 8000)")
    parser.add_argument("--provider", default="openai",
                      help="Default LLM provider for API server (default: openai)")
    parser.add_argument("--reload", action="store_true",
                      help="Enable auto-reload for development")

    # Streaming mode arguments
    parser.add_argument("--force-streaming", action="store_true",
                      help="Force use of streaming architecture (override config)")
    parser.add_argument("--max-concurrent", type=int, default=3,
                      help="Maximum concurrent LLM calls (streaming mode only)")
    parser.add_argument("--progress", action="store_true",
                      help="Enable real-time progress reporting")

    args = parser.parse_args()
    
    try:
        if args.list_projects:
            # List available projects using the new config manager
            projects = config_manager.list_projects()
            print("Available projects:")
            for project_name, description in projects.items():
                print(f"  {project_name}: {description}")
            return True
        
        elif args.config:
            # Configuration mode
            config_manager_obj = TestGenerationConfig(args.config_file)
            project_config = config_manager_obj.get_project_config(args.config)
            
            # Get profile configuration and merge with project config
            profile_config = config_manager_obj.get_profile_config(args.profile)
            merged_config = {**project_config, **profile_config}
            
            # Analyze project functions
            service = TestGenerationService()
            functions_with_context = service.analyze_project_functions(project_config)
            
            if not functions_with_context:
                logger.error("No functions found to test!")
                return False
            
            # Generate tests
            results = service.generate_tests_with_config(
                functions_with_context, 
                merged_config,
                prompt_only=args.prompt_only
            )
            
            # Print results
            service.print_results(results, project_config)
            
            logger.info("Test generation completed!")
            logger.info(f"Total functions processed: {len(results)}")
            
            return True
            
        elif args.simple:
            # Simple mode
            if not args.project:
                parser.error("--simple mode requires --project argument")
            
            generate_tests_simple_mode(
                project_path=args.project,
                output_dir=args.output,
                compile_commands=args.compile_commands,
                include_patterns=args.include,
                exclude_patterns=args.exclude
            )
            return True
            
        elif args.single_file:
            # Single file mode
            if not args.project:
                parser.error("--single-file mode requires --project argument")
            
            generate_tests_single_file(
                project_path=args.project,
                file_path=args.single_file,
                output_dir=args.output,
                compile_commands=args.compile_commands,
                prompt_only=args.prompt_only
            )
            return True
            
        elif args.streaming:
            # Streaming mode
            start_streaming_mode(
                project_path=args.project,
                output_dir=args.output,
                compile_commands=args.compile_commands,
                include_patterns=args.include,
                exclude_patterns=args.exclude,
                force_streaming=args.force_streaming,
                max_concurrent=args.max_concurrent,
                enable_progress=args.progress
            )
            return True

        elif args.compare:
            # Comparison mode
            start_comparison_mode(
                project_path=args.project,
                output_dir=args.output,
                compile_commands=args.compile_commands,
                include_patterns=args.include,
                exclude_patterns=args.exclude
            )
            return True

        elif args.api_server:
            # API server mode
            start_api_server(
                host=args.host,
                port=args.port,
                provider=args.provider,
                reload=args.reload
            )
            return True
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)