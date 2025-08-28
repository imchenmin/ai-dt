"""
MCP Server for AI-DT Prompt Generation Service
Provides Model Context Protocol endpoints for VS Code Continue and other clients
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.analyzer.clang_analyzer import ClangAnalyzer
from src.parser.compilation_db import CompilationDatabaseParser
from src.utils.context_compressor import ContextCompressor
from src.utils.prompt_templates import PromptTemplates
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class AIDTMCPHandler:
    """MCP handler for AI-DT prompt generation service"""
    
    def __init__(self):
        self.analyzer = ClangAnalyzer()
        self.parser = None  # Will be initialized when needed with specific path
        self.compressor = ContextCompressor()
    
    async def handle_list_tools(self) -> List[Dict[str, Any]]:
        """Return available MCP tools"""
        return [
            {
                "name": "generate_test_prompt",
                "description": "Generate Google Test + MockCpp prompt for C/C++ function",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to source file"},
                        "function_name": {"type": "string", "description": "Function name to test"},
                        "project_root": {"type": "string", "description": "Project root directory"},
                        "compilation_db_path": {"type": "string", "description": "Path to compile_commands.json"}
                    },
                    "required": ["file_path", "function_name"]
                }
            },
            {
                "name": "analyze_function_dependencies",
                "description": "Analyze function dependencies and context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to source file"},
                        "function_name": {"type": "string", "description": "Function name to analyze"},
                        "project_root": {"type": "string", "description": "Project root directory"}
                    },
                    "required": ["file_path", "function_name"]
                }
            },
            {
                "name": "get_function_signature",
                "description": "Get function signature information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to source file"},
                        "function_name": {"type": "string", "description": "Function name"}
                    },
                    "required": ["file_path", "function_name"]
                }
            }
        ]
    
    async def handle_generate_test_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test prompt for a function"""
        try:
            file_path = params["file_path"]
            function_name = params["function_name"]
            project_root = params.get("project_root")
            comp_db_path = params.get("compilation_db_path")
            
            logger.info(f"Generating test prompt for {function_name} in {file_path}")
            
            # Parse compilation database if provided
            compile_args = []
            if comp_db_path and Path(comp_db_path).exists():
                # Initialize parser with the compilation database path
                parser = CompilationDatabaseParser(comp_db_path)
                compile_commands = parser.parse()
                file_commands = compile_commands.get(file_path, [])
                compile_args = file_commands
            
            # Analyze the file
            functions = self.analyzer.analyze_file(file_path, compile_args)
            
            # Find the target function
            target_function = None
            for func in functions:
                if func['name'] == function_name:
                    target_function = func
                    break
            
            if not target_function:
                return {
                    "error": f"Function {function_name} not found in {file_path}",
                    "available_functions": [f['name'] for f in functions]
                }
            
            # Get basic context without detailed dependencies
            basic_context = {
                'function': target_function,
                'dependencies': {
                    'called_functions': [],
                    'macros_used': [],
                    'macro_definitions': [],
                    'data_structures': [],
                    'include_directives': []
                }
            }
            
            # Compress context for LLM
            compressed_context = self.compressor.compress_function_context(
                target_function, basic_context
            )
            
            # Generate prompt
            prompt = self.compressor.format_for_llm_prompt(compressed_context)
            
            return {
                "prompt": prompt,
                "function_info": target_function,
                "dependencies": compressed_context['dependencies'],
                "language": target_function.get('language', 'c')
            }
            
        except Exception as e:
            logger.error(f"Error generating test prompt: {e}")
            return {"error": str(e)}
    
    async def handle_analyze_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze function dependencies"""
        try:
            file_path = params["file_path"]
            function_name = params["function_name"]
            
            logger.info(f"Analyzing dependencies for {function_name} in {file_path}")
            
            # Analyze the file with default args
            functions = self.analyzer.analyze_file(file_path, [])
            
            # Find the target function
            target_function = None
            for func in functions:
                if func['name'] == function_name:
                    target_function = func
                    break
            
            if not target_function:
                return {
                    "error": f"Function {function_name} not found in {file_path}",
                    "available_functions": [f['name'] for f in functions]
                }
            
            # Get dependencies - need to get the actual cursor from function definition map
            # For now, return basic function info without detailed dependencies
            dependencies = {
                'called_functions': [],
                'macros_used': [],
                'macro_definitions': [],
                'data_structures': [],
                'include_directives': []
            }
            
            return {
                "function": target_function,
                "dependencies": dependencies,
                "called_functions": dependencies.get('called_functions', []),
                "macros_used": dependencies.get('macros_used', []),
                "data_structures": dependencies.get('data_structures', [])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return {"error": str(e)}
    
    async def handle_get_signature(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get function signature"""
        try:
            file_path = params["file_path"]
            function_name = params["function_name"]
            
            logger.info(f"Getting signature for {function_name} in {file_path}")
            
            # Analyze the file
            functions = self.analyzer.analyze_file(file_path, [])
            
            # Find the target function
            target_function = None
            for func in functions:
                if func["name"] == function_name:
                    target_function = func
                    break
            
            if not target_function:
                return {
                    "error": f"Function {function_name} not found in {file_path}",
                    "available_functions": [f["name"] for f in functions]
                }
            
            return {
                "signature": self._format_function_signature(target_function),
                "return_type": target_function["return_type"],
                "parameters": target_function["parameters"],
                "location": f"{target_function['file']}:{target_function['line']}",
                "language": target_function.get("language", "c")
            }
            
        except Exception as e:
            logger.error(f"Error getting signature: {e}")
            return {"error": str(e)}

    def _format_function_signature(self, function_info):
        """Format function signature string"""
        params = ", ".join([f"{p['type']} {p['name']}" for p in function_info["parameters"]])
        return f"{function_info['return_type']} {function_info['name']}({params})"
