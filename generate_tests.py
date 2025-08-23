#!/usr/bin/env python3
"""
Unified test generation script with configuration support
"""

import sys
import os
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser.compilation_db import CompilationDatabaseParser
from src.analyzer.function_analyzer import FunctionAnalyzer
from src.generator.test_generator import TestGenerator
from src.utils.libclang_config import ensure_libclang_configured
from src.utils.config_loader import ConfigLoader


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
            print(f"❌ Configuration file not found: {self.config_path}")
            print("Please create config/test_generation.yaml or specify a different config file.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ Error parsing configuration file: {e}")
            sys.exit(1)
    
    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get configuration for a specific project"""
        projects = self.config.get('projects', {})
        if project_name not in projects:
            available_projects = list(projects.keys())
            print(f"❌ Project '{project_name}' not found in configuration.")
            print(f"Available projects: {', '.join(available_projects)}")
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


def analyze_project_functions(project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze functions in the specified project"""
    print(f"🔍 Analyzing project: {project_config.get('description', 'Unknown')}")
    print("=" * 60)
    
    # Configure libclang
    ensure_libclang_configured()
    
    project_root = project_config['path']
    comp_db_path = project_config['comp_db']
    
    # Parse compilation database
    print("1. Parsing compilation database...")
    parser = CompilationDatabaseParser(comp_db_path)
    compilation_units = parser.parse()
    print(f"   Found {len(compilation_units)} compilation units")
    
    # Analyze functions
    print("2. Analyzing functions...")
    analyzer = FunctionAnalyzer(project_root)
    
    functions_with_context = []
    filter_config = project_config.get('filter', {})
    
    for unit in compilation_units:
        file_path = unit['file']
        print(f"   Analyzing {file_path}")
        
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
                
                print(f"     ✓ {func['name']}: {func['return_type']} function "
                      f"with {len(func['parameters'])} parameters")
    
    return functions_with_context


def should_include_function(func: Dict[str, Any], filter_config: Dict[str, Any], 
                           project_config: Dict[str, Any]) -> bool:
    """Determine if a function should be included based on filtering rules"""
    function_name = func.get('name', '')
    file_path = func.get('file', '')
    
    # Skip standard library functions
    if filter_config.get('skip_std_lib', True):
        if any(path in file_path for path in ['/usr/include', '/usr/lib', '/include/c++']):
            return False
    
    # Skip compiler builtins and internal functions
    if filter_config.get('skip_compiler_builtins', True):
        if function_name.startswith('__') or function_name.startswith('_'):
            return False
    
    # Skip operators and special functions
    if filter_config.get('skip_operators', True):
        if function_name.startswith('operator') or function_name in ['main', 'malloc', 'free']:
            return False
    
    # Check project-specific function configurations
    project_functions = project_config.get('functions', {})
    if project_functions:
        # If specific functions are configured, only include those
        return function_name in project_functions
    
    # Apply custom include/exclude patterns
    include_patterns = filter_config.get('custom_include_patterns', [])
    exclude_patterns = filter_config.get('custom_exclude_patterns', [])
    
    if include_patterns and not any(pattern in function_name for pattern in include_patterns):
        return False
    
    if any(pattern in function_name for pattern in exclude_patterns):
        return False
    
    return True


def generate_tests_with_config(functions_with_context: List[Dict[str, Any]], 
                              project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate tests using configured LLM provider"""
    llm_provider = project_config.get('llm_provider', 'deepseek')
    model = project_config.get('model', 'deepseek-coder')
    output_dir = project_config.get('output_dir', './generated_tests')
    
    # Check if LLM provider is available
    api_key = ConfigLoader.get_api_key(llm_provider)
    if not api_key:
        llm_config = ConfigLoader.get_llm_config(llm_provider)
        print(f"❌ {llm_provider.upper()} API key not found.")
        print(f"Please set {llm_config['api_key_env']} environment variable.")
        return []
    
    print(f"\n3. Generating tests with {llm_provider} ({model})...")
    
    # Initialize test generator
    test_generator = TestGenerator(
        llm_provider=llm_provider,
        api_key=api_key,
        model=model
    )
    
    print(f"Using output directory: {output_dir}")
    print(f"Generating tests for {len(functions_with_context)} functions...")
    
    # Generate tests
    results = test_generator.generate_tests(
        functions_with_context,
        output_dir=output_dir
    )
    
    return results


def print_results(results: List[Dict[str, Any]], project_config: Dict[str, Any]):
    """Print generation results"""
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n📊 Generation Results:")
    print(f"   Successful: {len(successful)}")
    print(f"   Failed: {len(failed)}")
    
    if successful:
        print(f"\n✅ Successful Tests:")
        for result in successful:
            print(f"   • {result['function_name']}")
            print(f"     Length: {result.get('test_length', 0)} chars")
            print(f"     Output: {result.get('output_path', 'unknown')}")
    
    if failed:
        print(f"\n❌ Failed Tests:")
        for result in failed:
            print(f"   • {result['function_name']}: {result.get('error', 'Unknown error')}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate tests using configuration")
    parser.add_argument("project", help="Project name from configuration")
    parser.add_argument("--config", default="config/test_generation.yaml", 
                       help="Path to configuration file")
    parser.add_argument("--profile", default="comprehensive", 
                       help="Execution profile (quick, comprehensive, custom)")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_manager = TestGenerationConfig(args.config)
        project_config = config_manager.get_project_config(args.project)
        
        # Analyze project functions
        functions_with_context = analyze_project_functions(project_config)
        
        if not functions_with_context:
            print("\n❌ No functions found to test!")
            return False
        
        # Generate tests
        results = generate_tests_with_config(functions_with_context, project_config)
        
        # Print results
        print_results(results, project_config)
        
        print(f"\n🎉 Test generation completed!")
        print(f"   Total functions processed: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)