"""
Test Generation Service - Orchestrates the test generation process
with proper separation of concerns and dependency injection.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.libclang_config import ensure_libclang_configured
from src.utils.config_loader import ConfigLoader
from src.utils.config_manager import config_manager
from src.utils.logging_utils import setup_logging, get_logger, log_generation_stats, close_logging
from src.utils.error_handler import with_error_handling, error_handler

logger = get_logger(__name__)


class TestGenerationService:
    """Service for orchestrating test generation with proper dependency injection"""
    
    def __init__(self, 
                 parser: Optional[CompilationDatabaseParser] = None,
                 analyzer: Optional[FunctionAnalyzer] = None,
                 generator: Optional[TestGenerator] = None):
        """Initialize service with optional dependencies for testing"""
        self.parser = parser
        self.analyzer = analyzer
        self.generator = generator
    
    @with_error_handling(context="output directory generation")
    def generate_output_directory(self, project_path: str, base_output_dir: str = "./experiment/generated_tests") -> str:
        """Generate output directory based on project name and timestamp"""
        project_name = Path(project_path).name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_dir = Path(base_output_dir) / f"{project_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generated output directory: {output_dir}")
        return str(output_dir)
    
    def should_include_function(self, func: Dict[str, Any], filter_config: Dict[str, Any], 
                               project_config: Dict[str, Any]) -> bool:
        """Determine if a function should be included based on filtering rules"""
        function_name = func.get('name', '')
        file_path = func.get('file', '')
        project_path = project_config.get('path', '')
        function_body = func.get('body', '')
        
        # Only include functions defined within the project directory
        if project_path:
            abs_project_path = str(Path(project_path).absolute())
            abs_file_path = str(Path(file_path).absolute())
            if not abs_file_path.startswith(abs_project_path):
                return False
        
        # Skip compiler builtins and internal functions
        if filter_config.get('skip_compiler_builtins', True):
            if function_name.startswith('__') or function_name.startswith('_'):
                return False
        
        # Skip operators and special functions
        if filter_config.get('skip_operators', True):
            if function_name.startswith('operator') or function_name in ['main']:
                return False
        
        # Skip inline functions
        if filter_config.get('skip_inline', True):
            if function_body and 'inline' in function_body:
                return False
        
        # Skip functions from third-party directories
        if filter_config.get('skip_third_party', True):
            if '/third_party/' in file_path or '/vendor/' in file_path:
                return False
        
        # Apply custom include/exclude patterns
        include_patterns = filter_config.get('custom_include_patterns', [])
        exclude_patterns = filter_config.get('custom_exclude_patterns', [])
        
        if include_patterns and not any(pattern in function_name for pattern in include_patterns):
            return False
        
        if any(pattern in function_name for pattern in exclude_patterns):
            return False
        
        return True
    
    @with_error_handling(context="project function analysis")
    def analyze_project_functions(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze functions in the specified project"""
        logger.info(f"Analyzing project: {project_config.get('description', 'Unknown')}")
        
        # Configure libclang
        ensure_libclang_configured()
        
        project_root = project_config['path']
        comp_db_path = project_config['comp_db']
        
        # Get include/exclude patterns from config
        include_patterns = project_config.get('include_patterns')
        exclude_patterns = project_config.get('exclude_patterns')
        
        # Parse compilation database with optional filtering
        logger.info("Parsing compilation database...")
        parser = self.parser or CompilationDatabaseParser(comp_db_path)
        compilation_units = parser.parse(include_patterns=include_patterns, exclude_patterns=exclude_patterns)
        logger.info(f"Found {len(compilation_units)} compilation units")
        
        if include_patterns:
            logger.info(f"Including patterns: {include_patterns}")
        if exclude_patterns:
            logger.info(f"Excluding patterns: {exclude_patterns}")
        
        # Analyze functions
        logger.info("Analyzing functions...")
        analyzer = self.analyzer or FunctionAnalyzer(project_root)
        
        functions_with_context = []
        filter_config = project_config.get('filter', {})
        
        for unit in compilation_units:
            file_path = unit['file']
            logger.info(f"Analyzing {file_path}")
            
            functions = analyzer.analyze_file(file_path, unit['arguments'])
            
            for func in functions:
                if self.should_include_function(func, filter_config, project_config):
                    # Get complete context
                    context = analyzer._analyze_function_context(
                        func, unit['arguments'], compilation_units
                    )
                    
                    functions_with_context.append({
                        'function': func,
                        'context': context
                    })
                    
                    logger.info(f"Found testable function: {func['name']}: {func['return_type']} function with {len(func['parameters'])} parameters")
        
        return functions_with_context
    
    @with_error_handling(context="test generation with config")
    def generate_tests_with_config(self, functions_with_context: List[Dict[str, Any]], 
                                  project_config: Dict[str, Any],
                                  prompt_only: bool = False) -> List[Dict[str, Any]]:
        """Generate tests using configured LLM provider"""
        start_time = datetime.now()
        
        llm_provider = project_config.get('llm_provider', 'deepseek')
        model = project_config.get('model', 'deepseek-coder')
        base_output_dir = project_config.get('output_dir', './experiment/generated_tests')
        
        # Generate output directory based on project name and timestamp
        project_path = project_config['path']
        output_dir = self.generate_output_directory(project_path, base_output_dir)
        
        # Setup enhanced logging with file output to experiment directory
        setup_logging(output_dir=output_dir, log_level=logging.INFO)
        
        # In prompt-only mode, we don't need a real API key and will use the mock client.
        if not prompt_only:
            api_key = ConfigLoader.get_api_key(llm_provider)
            if not api_key:
                llm_config = ConfigLoader.get_llm_config(llm_provider)
                logger.error(f"{llm_provider.upper()} API key not found.")
                logger.info(f"Please set {llm_config['api_key_env']} environment variable.")
                return []
        else:
            logger.info("Running in prompt-only mode. LLM calls will be skipped.")
            api_key = None # No key needed for mock client
        
        logger.info(f"Generating tests with {llm_provider if not prompt_only else 'mock'} ({model})...")
        
        # Initialize test generator with error handling configuration
        error_config = project_config.get('error_handling', {})
        generator = self.generator or TestGenerator(
            llm_provider=llm_provider if not prompt_only else "mock",
            api_key=api_key,
            model=model,
            max_retries=error_config.get('max_retries', 3),
            retry_delay=error_config.get('retry_delay', 1.0)
        )
        
        logger.info(f"Using output directory: {output_dir}")
        logger.info(f"Generating tests for {len(functions_with_context)} functions...")
        
        # Generate tests
        project_name = Path(project_path).name
        max_workers = project_config.get('max_workers', 3)
        
        # Create project config dictionary for the new API
        project_config_dict = {
            "name": project_name,
            "output_dir": output_dir,
            "unit_test_directory_path": project_config.get("unit_test_directory_path")
        }
        
        results = generator.generate_tests(
            functions_with_context,
            project_config_dict,
            max_workers=max_workers
        )
        
        # Log generation statistics
        successful = len([r for r in results if r['success']])
        failed = len([r for r in results if not r['success']])
        log_generation_stats(start_time, len(functions_with_context), successful, failed)
        
        # Close file handlers
        close_logging()
        
        return results
    
    def print_results(self, results: List[Dict[str, Any]], project_config: Dict[str, Any]):
        """Print generation results"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        logger.info(f"Generation Results:")
        logger.info(f"  Successful: {len(successful)}")
        logger.info(f"  Failed: {len(failed)}")
        
        if successful:
            logger.info("Successful Tests:")
            for result in successful:
                logger.info(f"  • {result['function_name']}")
                logger.info(f"    Length: {result.get('test_length', 0)} chars")
                logger.info(f"    Output: {result.get('output_path', 'unknown')}")
        
        if failed:
            logger.info("Failed Tests:")
            for result in failed:
                logger.info(f"  • {result['function_name']}: {result.get('error', 'Unknown error')}")