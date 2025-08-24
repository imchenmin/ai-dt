#!/usr/bin/env python3
"""
Main entry point for AI-Driven Test Generator
Unified command-line interface for all test generation scenarios
"""

import argparse
import logging
import sys
import yaml
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.libclang_config import ensure_libclang_configured
from src.utils.config_loader import ConfigLoader
from src.utils.logging_utils import setup_logging, get_logger, log_generation_stats, close_logging

# Setup basic logging initially
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


def generate_output_directory(project_path: str, base_output_dir: str = "./experiment/generated_tests") -> str:
    """Generate output directory based on project name and timestamp"""
    project_name = Path(project_path).name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_dir = Path(base_output_dir) / f"{project_name}_{timestamp}"
    
    # Create the directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generated output directory: {output_dir}")
    return str(output_dir)


class TestGenerationConfig:
    """Load and manage test generation configuration"""
    
    def __init__(self, config_path: str = "config/test_generation.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            logger.info("Please create config/test_generation.yaml or specify a different config file.")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get configuration for a specific project"""
        projects = self.config.get('projects', {})
        if project_name not in projects:
            available_projects = list(projects.keys())
            logger.error(f"Project '{project_name}' not found in configuration.")
            logger.info(f"Available projects: {', '.join(available_projects)}")
            sys.exit(1)
        
        # Merge with defaults
        project_config = projects[project_name].copy()
        defaults = self.config.get('defaults', {})
        
        # Apply defaults for missing keys
        for key, value in defaults.items():
            if key not in project_config:
                project_config[key] = value
        
        return project_config
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration"""
        providers = self.config.get('llm_providers', {})
        if provider not in providers:
            raise ValueError(f"LLM provider '{provider}' not configured")
        return providers[provider]
    
    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Get execution profile configuration"""
        profiles = self.config.get('profiles', {})
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found")
        return profiles[profile_name]


def should_include_function(func: Dict[str, Any], filter_config: Dict[str, Any], 
                           project_config: Dict[str, Any]) -> bool:
    """Determine if a function should be included based on filtering rules"""
    function_name = func.get('name', '')
    file_path = func.get('file', '')
    project_path = project_config.get('path', '')
    function_body = func.get('body', '')
    
    # Only include functions defined within the project directory
    if project_path:
        from pathlib import Path
        # Convert both paths to absolute for comparison
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
    
    # Skip inline functions (both standard library and project inline functions)
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


def analyze_project_functions(project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze functions in the specified project"""
    logger.info(f"Analyzing project: {project_config.get('description', 'Unknown')}")
    
    # Configure libclang
    ensure_libclang_configured()
    
    project_root = project_config['path']
    comp_db_path = project_config['comp_db']
    
    # Parse compilation database
    logger.info("Parsing compilation database...")
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    logger.info(f"Found {len(compilation_units)} compilation units")
    
    # Analyze functions
    logger.info("Analyzing functions...")
    analyzer = FunctionAnalyzer(project_root)
    
    functions_with_context = []
    filter_config = project_config.get('filter', {})
    
    for unit in compilation_units:
        file_path = unit['file']
        logger.info(f"Analyzing {file_path}")
        
        functions = analyzer.analyze_file(file_path, unit['arguments'])
        
        for func in functions:
            if should_include_function(func, filter_config, project_config):
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


def generate_tests_with_config(functions_with_context: List[Dict[str, Any]], 
                              project_config: Dict[str, Any],
                              prompt_only: bool = False) -> List[Dict[str, Any]]:
    """Generate tests using configured LLM provider"""
    start_time = datetime.datetime.now()
    
    llm_provider = project_config.get('llm_provider', 'deepseek')
    model = project_config.get('model', 'deepseek-coder')
    base_output_dir = project_config.get('output_dir', './experiment/generated_tests')
    
    # Generate output directory based on project name and timestamp
    project_path = project_config['path']
    output_dir = generate_output_directory(project_path, base_output_dir)
    
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
    
    # Initialize test generator
    test_generator = TestGenerator(
        llm_provider=llm_provider if not prompt_only else "mock",
        api_key=api_key,
        model=model
    )
    
    logger.info(f"Using output directory: {output_dir}")
    logger.info(f"Generating tests for {len(functions_with_context)} functions...")
    
    # Generate tests
    project_name = Path(project_path).name
    results = test_generator.generate_tests(
        functions_with_context,
        output_dir=output_dir,
        project_name=project_name
    )
    
    # Log generation statistics
    successful = len([r for r in results if r['success']])
    failed = len([r for r in results if not r['success']])
    log_generation_stats(start_time, len(functions_with_context), successful, failed)
    
    # Close file handlers
    close_logging()
    
    return results


def print_results(results: List[Dict[str, Any]], project_config: Dict[str, Any]):
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


def generate_tests_simple_mode(project_path: str, output_dir: str, compile_commands: str):
    """Simple mode: generate tests without configuration"""
    start_time = datetime.datetime.now()
    
    # Generate output directory based on project name and timestamp
    auto_output_dir = generate_output_directory(project_path, output_dir)
    
    # Setup enhanced logging with file output to experiment directory
    setup_logging(output_dir=auto_output_dir, log_level=logging.INFO)
    
    logger.info("Running in simple mode...")
    
    # Configure libclang
    ensure_libclang_configured()
    
    # Parse compilation database
    parser = CompilationDatabaseParser(compile_commands)
    compilation_units = parser.parse()
    
    # Analyze functions
    function_analyzer = FunctionAnalyzer(project_path)
    testable_functions = []
    
    for unit in compilation_units:
        functions = function_analyzer.analyze_file(unit['file'], unit['arguments'])
        
        # Add context information to each function
        for func in functions:
            func['context'] = function_analyzer._analyze_function_context(
                func, unit['arguments'], compilation_units
            )
        
        testable_functions.extend(functions)
    
    # Generate tests
    test_generator = TestGenerator()
    successful = 0
    failed = 0
    
    for function in testable_functions:
        test_result = test_generator.generate_test(function, function['context'])
        
        # Save generated test
        if test_result['success']:
            output_path = Path(auto_output_dir) / f"test_{function['name']}.cpp"
            output_path.write_text(test_result['test_code'])
            logger.info(f"Generated test for {function['name']} at {output_path}")
            successful += 1
        else:
            logger.error(f"Failed to generate test for {function['name']}: {test_result['error']}")
            failed += 1
    
    # Log generation statistics
    log_generation_stats(start_time, len(testable_functions), successful, failed)
    
    # Close file handlers
    close_logging()


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
    
    # Simple mode arguments
    parser.add_argument("-p", "--project", help="Project root directory (simple mode)")
    parser.add_argument("-o", "--output", default="./experiment/generated_tests", 
                      help="Output directory (simple mode)")
    parser.add_argument("--compile-commands", default="compile_commands.json", 
                      help="Path to compile_commands.json (simple mode)")
    
    # Configuration mode arguments
    parser.add_argument("--config-file", default="config/test_generation.yaml",
                      help="Path to configuration file (config mode)")
    parser.add_argument("--profile", default="comprehensive",
                      help="Execution profile (quick, comprehensive, custom)")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Only generate prompts and skip LLM requests.")
    
    args = parser.parse_args()
    
    try:
        if args.list_projects:
            # List available projects
            config_manager = TestGenerationConfig(args.config_file)
            projects = config_manager.config.get('projects', {})
            print("Available projects:")
            for project_name, project_config in projects.items():
                description = project_config.get('description', 'No description')
                print(f"  {project_name}: {description}")
            return True
        
        elif args.config:
            # Configuration mode
            config_manager = TestGenerationConfig(args.config_file)
            project_config = config_manager.get_project_config(args.config)
            
            # Analyze project functions
            functions_with_context = analyze_project_functions(project_config)
            
            if not functions_with_context:
                logger.error("No functions found to test!")
                return False
            
            # Generate tests
            results = generate_tests_with_config(
                functions_with_context, 
                project_config,
                prompt_only=args.prompt_only
            )
            
            # Print results
            print_results(results, project_config)
            
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
                compile_commands=args.compile_commands
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