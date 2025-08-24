"""
Utility to generate compile_commands.json for C/C++ projects
"""

import json
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class CompileDBGenerator:
    """Generate compile_commands.json using build systems"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def generate_with_cmake(self, build_dir: str = "build") -> bool:
        """Generate compile_commands.json using CMake"""
        build_path = self.project_root / build_dir
        build_path.mkdir(exist_ok=True)
        
        try:
            # Run cmake to generate build system
            result = subprocess.run([
                "cmake", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", ".."
            ], cwd=build_path, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                compile_commands_path = build_path / "compile_commands.json"
                if compile_commands_path.exists():
                    # Move to project root
                    target_path = self.project_root / "compile_commands.json"
                    compile_commands_path.rename(target_path)
                    logger.info(f"Generated compile_commands.json at {target_path}")
                    return True
            
            logger.error(f"CMake failed: {result.stderr}")
            return False
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"CMake generation failed: {e}")
            return False
    
    def generate_with_bear(self, build_command: List[str]) -> bool:
        """Generate compile_commands.json using bear"""
        try:
            result = subprocess.run([
                "bear", "--"] + build_command,
                cwd=self.project_root, capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                compile_commands_path = self.project_root / "compile_commands.json"
                if compile_commands_path.exists():
                    logger.info(f"Generated compile_commands.json with bear")
                    return True
            
            logger.error(f"Bear failed: {result.stderr}")
            return False
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"Bear generation failed: {e}")
            return False
    
    def generate_simple_compile_db(self, source_files: List[str]) -> bool:
        """Generate a simple compile_commands.json for basic projects"""
        compile_commands = []
        
        for source_file in source_files:
            source_path = Path(source_file)
            if not source_path.exists():
                continue
            
            # Determine compiler based on file extension
            if source_path.suffix in ['.c']:
                compiler = "gcc"
                std_flag = ""
            elif source_path.suffix in ['.cpp', '.cc', '.cxx']:
                compiler = "g++"
                std_flag = "-std=c++11"
            else:
                continue
            
            compile_command = {
                "directory": str(self.project_root),
                "command": f"{compiler} -c {source_path.name} -o {source_path.stem}.o {std_flag}",
                "file": str(source_path.name)
            }
            compile_commands.append(compile_command)
        
        if compile_commands:
            output_path = self.project_root / "compile_commands.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(compile_commands, f, indent=2)
            logger.info(f"Generated simple compile_commands.json with {len(compile_commands)} entries")
            return True
        
        return False
    
    def find_source_files(self) -> List[str]:
        """Find C/C++ source files in the project"""
        source_extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']
        source_files = []
        
        for ext in source_extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if file_path.is_file():
                    source_files.append(str(file_path))
        
        return source_files
    
    def generate(self) -> bool:
        """Auto-generate compile_commands.json using available methods"""
        # First try CMake
        if self.generate_with_cmake():
            return True
        
        # Then try bear if makefiles exist
        makefile_path = self.project_root / "Makefile"
        if makefile_path.exists():
            if self.generate_with_bear(["make"]):
                return True
        
        # Fallback to simple generation
        source_files = self.find_source_files()
        if source_files:
            return self.generate_simple_compile_db(source_files)
        
        logger.warning("No source files found for compile_commands.json generation")
        return False