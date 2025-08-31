#!/usr/bin/env python3
"""
Main entry point for AI-Driven Test Generator
Unified command-line interface for all test generation scenarios
"""

import argparse
import logging
import sys
from typing import Dict, Any, List, Optional

from src.test_generation.service import TestGenerationService
from src.utils.config_manager import config_manager
from src.utils.logging_utils import get_logger

# Setup basic logging initially
logging.basicConfig(level=logging.INFO)
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
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)