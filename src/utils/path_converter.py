"""
Utility to convert WSL paths to Windows paths in compile_commands.json
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List


class WSLPathConverter:
    """Convert WSL paths to Windows paths for compile_commands.json"""
    
    @staticmethod
    def wsl_to_windows_path(wsl_path: str) -> str:
        """Convert WSL path to Windows path"""
        # Convert /mnt/c/... to C:/...
        if wsl_path.startswith('/mnt/'):
            drive_letter = wsl_path[5].upper()
            remaining_path = wsl_path[6:].replace('/', '\\')
            return f"{drive_letter}:\\{remaining_path}"
        
        # Handle other WSL paths if needed
        return wsl_path
    
    @staticmethod
    def convert_compile_commands(wsl_compile_commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert all paths in compile_commands.json from WSL to Windows format"""
        converted_commands = []
        
        for command in wsl_compile_commands:
            converted_command = command.copy()
            
            # Convert directory path
            if 'directory' in converted_command:
                converted_command['directory'] = WSLPathConverter.wsl_to_windows_path(
                    converted_command['directory']
                )
            
            # Convert file path
            if 'file' in converted_command:
                converted_command['file'] = WSLPathConverter.wsl_to_windows_path(
                    converted_command['file']
                )
            
            # Convert paths in command string
            if 'command' in converted_command:
                converted_command['command'] = WSLPathConverter.convert_command_paths(
                    converted_command['command']
                )
            
            converted_commands.append(converted_command)
        
        return converted_commands
    
    @staticmethod
    def convert_command_paths(command: str) -> str:
        """Convert WSL paths in command string to Windows paths"""
        # Find all WSL paths in the command
        wsl_path_pattern = r'/mnt/[a-zA-Z]/[^\s]*'
        
        def replace_wsl_path(match):
            wsl_path = match.group(0)
            return WSLPathConverter.wsl_to_windows_path(wsl_path)
        
        # Replace all WSL paths with Windows paths
        return re.sub(wsl_path_pattern, replace_wsl_path, command)
    
    @staticmethod
    def convert_file(input_path: str, output_path: str = None) -> bool:
        """Convert a compile_commands.json file from WSL to Windows format"""
        input_path_obj = Path(input_path)
        
        if not input_path_obj.exists():
            print(f"Input file not found: {input_path}")
            return False
        
        # Read the WSL compile_commands.json
        with open(input_path, 'r', encoding='utf-8') as f:
            wsl_commands = json.load(f)
        
        # Convert paths
        windows_commands = WSLPathConverter.convert_compile_commands(wsl_commands)
        
        # Determine output path
        if output_path is None:
            output_path = input_path_obj.parent.parent / "compile_commands.json"
        
        # Write converted file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(windows_commands, f, indent=2)
        
        print(f"Converted compile_commands.json saved to: {output_path}")
        return True