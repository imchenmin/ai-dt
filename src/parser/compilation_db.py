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
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse compile_commands.json and return compilation units"""
        if not self.compile_commands_path.exists():
            raise FileNotFoundError(f"compile_commands.json not found at {self.compile_commands_path}")
        
        with open(self.compile_commands_path, 'r', encoding='utf-8') as f:
            compile_commands = json.load(f)
        
        compilation_units = []
        for command in compile_commands:
            unit = {
                'file': command['file'],
                'directory': command['directory'],
                'arguments': self._parse_arguments(command['command']),
                'output': command.get('output', '')
            }
            compilation_units.append(unit)
        
        return compilation_units
    
    def _parse_arguments(self, command: str) -> List[str]:
        """Parse compiler command arguments"""
        # Simple argument parsing - can be enhanced
        return command.split()[1:]  # Skip the compiler executable
    
    def get_file_dependencies(self, file_path: str) -> List[str]:
        """Get include dependencies for a specific file"""
        # TODO: Implement include dependency analysis
        return []
    
    def get_compilation_flags(self, file_path: str) -> Dict[str, Any]:
        """Get compilation flags for a specific file"""
        # TODO: Extract specific flags like -I, -D, etc.
        return {}