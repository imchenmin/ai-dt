"""
Function analyzer for identifying testable C/C++ functions
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from .clang_analyzer import ClangAnalyzer
from .call_analyzer import CallAnalyzer


class FunctionAnalyzer:
    """Analyzes C/C++ files to identify testable functions"""
    
    def __init__(self, project_root: str = "."):
        self.clang_analyzer = ClangAnalyzer()
        self.call_analyzer = CallAnalyzer(project_root)
    
    def analyze_file(self, file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """Analyze a C/C++ file and return testable functions"""
        path = Path(file_path)
        if not path.exists():
            return []
        
        # Use clang-based analysis to extract function information
        functions = self._extract_functions_with_clang(file_path, compile_args)
        
        # Filter testable functions
        testable_functions = [
            func for func in functions 
            if self._is_testable_function(func)
        ]
        
        return testable_functions
    
    def _extract_functions_with_clang(self, file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """Use clang to extract function information from source file"""
        return self.clang_analyzer.analyze_file(file_path, compile_args)
    
    def _is_testable_function(self, function_info: Dict[str, Any]) -> bool:
        """Determine if a function is testable based on rules"""
        language = function_info.get('language', 'c')
        
        if language == 'c':
            # C: Only non-static functions are testable
            return not function_info.get('is_static', False)
        elif language == 'cpp':
            # C++: Public methods, static methods, and private methods (via symbol hijacking)
            return (
                function_info.get('access_specifier') == 'public' or
                function_info.get('is_static', False) or
                function_info.get('can_hijack', False)
            )
        return False
    
    def _analyze_function_context(self, function_info: Dict[str, Any], compile_args: List[str], 
                                 compilation_units: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze function context including dependencies and usage"""
        function_name = function_info['name']
        
        # Find call sites across the project
        call_sites = self.call_analyzer.find_call_sites(function_name, compilation_units)
        
        # Analyze each call site context with deduplication
        analyzed_call_sites = []
        seen_call_contexts = set()
        
        for call_site in call_sites:
            analyzed_context = self.call_analyzer.analyze_call_context(call_site)
            # Create unique identifier for call context to avoid duplicates
            context_id = f"{analyzed_context['file']}:{analyzed_context['line']}"
            if context_id not in seen_call_contexts:
                seen_call_contexts.add(context_id)
                analyzed_call_sites.append(analyzed_context)
        
        # TODO: Add dependency analysis from clang_analyzer
        
        return {
            'called_functions': [],
            'macros_used': [],
            'data_structures': [],
            'call_sites': analyzed_call_sites
        }