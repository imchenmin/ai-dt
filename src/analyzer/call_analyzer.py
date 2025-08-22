"""
Call site analyzer for finding where functions are called
"""

import os
from pathlib import Path
from typing import List, Dict, Any


class CallAnalyzer:
    """Analyzes function call sites across the project"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def find_call_sites(self, function_name: str, compilation_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find all call sites for a given function across the project"""
        call_sites = []
        
        for unit in compilation_units:
            file_path = unit['file']
            compile_args = unit['arguments']
            
            if self._is_source_file(file_path):
                calls = self._find_calls_in_file(function_name, file_path, compile_args)
                call_sites.extend(calls)
        
        return call_sites
    
    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is a C/C++ source file"""
        extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx'}
        return Path(file_path).suffix.lower() in extensions
    
    def _find_calls_in_file(self, function_name: str, file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """Find calls to a specific function in a file"""
        # TODO: Implement using clang AST parsing to find call expressions
        # For now, use simple text-based search as placeholder
        
        calls = []
        path = Path(file_path)
        
        if not path.exists():
            return calls
        
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if function_name in line and self._is_function_call(line, function_name):
                    calls.append({
                        'file': file_path,
                        'line': line_num,
                        'context': line.strip(),
                        'function': function_name
                    })
                    
        except Exception as e:
            print(f"Error analyzing calls in {file_path}: {e}")
        
        return calls
    
    def _is_function_call(self, line: str, function_name: str) -> bool:
        """Heuristic to check if this is likely a function call"""
        # Simple heuristic - look for function name followed by parenthesis
        import re
        
        # Pattern for function calls: function_name(...)
        pattern = rf'\b{re.escape(function_name)}\s*\('
        return re.search(pattern, line) is not None
    
    def analyze_call_context(self, call_site: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the context around a call site"""
        file_path = call_site['file']
        line_num = call_site['line']
        
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            # Get context around the call site
            start_line = max(0, line_num - 3)
            end_line = min(len(lines), line_num + 2)
            
            context_lines = lines[start_line:end_line]
            
            return {
                'file': file_path,
                'line': line_num,
                'context': '\n'.join(context_lines),
                'function': call_site['function']
            }
            
        except Exception as e:
            print(f"Error analyzing call context: {e}")
            return call_site