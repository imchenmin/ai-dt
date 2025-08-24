"""
Compilation database parser for reading compile_commands.json
"""

import json
from pathlib import Path
from typing import List, Dict, Any


class CompilationDatabaseParser:
    """Parser for compile_commands.json format"""
    
    def __init__(self, compile_commands_path: str):
        self.compile_commands_path = Path(compile_commands_path)
    
    def parse(self, include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """Parse compile_commands.json and return compilation units
        
        Args:
            include_patterns: List of file/folder patterns to include (e.g., ['src/math/', 'utils.c'])
            exclude_patterns: List of file/folder patterns to exclude
        """
        if not self.compile_commands_path.exists():
            raise FileNotFoundError(f"compile_commands.json not found at {self.compile_commands_path}")
        
        with open(self.compile_commands_path, 'r', encoding='utf-8') as f:
            compile_commands = json.load(f)
        
        compilation_units = []
        for command in compile_commands:
            # Resolve relative file paths
            file_path = Path(command['file'])
            if not file_path.is_absolute():
                file_path = Path(command['directory']) / file_path
            
            # Apply filtering based on include/exclude patterns
            file_path_str = str(file_path.resolve())
            
            if include_patterns and not self._matches_patterns(file_path_str, include_patterns):
                continue
                
            if exclude_patterns and self._matches_patterns(file_path_str, exclude_patterns):
                continue
            
            # Handle both 'command' and 'arguments' formats
            if 'command' in command:
                arguments = self._parse_arguments(command['command'])
            elif 'arguments' in command:
                arguments = command['arguments']
                # Filter out compiler executable and output/file arguments
                arguments = self._filter_arguments(arguments)
            else:
                raise ValueError(f"No 'command' or 'arguments' field found in compile command: {command}")
            
            unit = {
                'file': str(file_path.resolve()),
                'directory': command['directory'],
                'arguments': arguments,
                'output': command.get('output', '')
            }
            compilation_units.append(unit)
        
        return compilation_units
    
    def _parse_arguments(self, command: str) -> List[str]:
        """Parse compiler command arguments"""
        # Extract only relevant compilation flags
        args = command.split()
        
        # Filter out compiler executable and output/file arguments
        filtered_args = []
        skip_next = False
        
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            
            # Skip compiler executable
            if i == 0 and ('gcc' in arg or 'g++' in arg or 'clang' in arg or 'cc' in arg):
                continue
            
            # Skip output file arguments
            if arg in ['-o', '-c']:
                skip_next = True
                continue
            
            # Skip source file names (they're handled separately)
            if arg.endswith(('.c', '.cpp', '.cc', '.cxx', '.o')):
                continue
            
            # Keep include paths, definitions, and other flags
            if arg.startswith(('-I', '-D', '-std=', '-O')):
                filtered_args.append(arg)
        
        return filtered_args
    
    def _filter_arguments(self, arguments: List[str]) -> List[str]:
        """Filter compiler arguments array to remove unnecessary elements"""
        filtered_args = []
        skip_next = False
        
        for i, arg in enumerate(arguments):
            if skip_next:
                skip_next = False
                continue
            
            # Skip compiler executable
            if i == 0 and ('gcc' in arg or 'g++' in arg or 'clang' in arg or 'cc' in arg):
                continue
            
            # Skip output file arguments
            if arg in ['-o', '-c']:
                skip_next = True
                continue
            
            # Skip source file names (they're handled separately)
            if arg.endswith(('.c', '.cpp', '.cc', '.cxx', '.o')):
                continue
            
            # Keep include paths, definitions, and other flags
            if arg.startswith(('-I', '-D', '-std=', '-O')):
                filtered_args.append(arg)
        
        return filtered_args
    
    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the given patterns"""
        for pattern in patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                if pattern in file_path:
                    return True
            # Handle file patterns (exact match or contains)
            elif pattern in file_path:
                return True
            # Handle relative path patterns
            elif '/' in pattern and pattern in file_path:
                return True
        return False
    
    def get_file_dependencies(self, file_path: str) -> List[str]:
        """Get include dependencies for a specific file"""
        # TODO: Implement include dependency analysis
        return []
    
    def get_compilation_flags(self, file_path: str) -> Dict[str, Any]:
        """Get compilation flags for a specific file"""
        # TODO: Extract specific flags like -I, -D, etc.
        return {}