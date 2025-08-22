"""
Clang-based C/C++ code analyzer using libclang
"""

import clang.cindex
from pathlib import Path
from typing import List, Dict, Any, Optional


class ClangAnalyzer:
    """C/C++ code analyzer using libclang AST parsing"""
    
    def __init__(self):
        # Configure libclang - try to auto-discover library
        self._configure_libclang()
    
    def _configure_libclang(self):
        """Configure libclang library path"""
        try:
            import clang.cindex
            
            # Check if library is already configured
            if clang.cindex.Config.library_file:
                print(f"libclang library found: {clang.cindex.Config.library_file}")
                return
            
            # Try to set library file from known path
            lib_path = clang.cindex.Config.library_path
            if lib_path:
                # Look for libclang.dll in the library path
                import os
                libclang_path = os.path.join(lib_path, 'libclang.dll')
                if os.path.exists(libclang_path):
                    clang.cindex.Config.set_library_file(libclang_path)
                    print(f"Set libclang library to: {libclang_path}")
                else:
                    print(f"libclang.dll not found in: {lib_path}")
            
        except Exception as e:
            print(f"Warning: Could not configure libclang: {e}")
    
    def analyze_file(self, file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """Analyze a C/C++ file and extract function information"""
        path = Path(file_path)
        if not path.exists():
            print(f"File not found: {file_path}")
            return []
        
        print(f"Analyzing {file_path} with args: {compile_args}")
        
        index = clang.cindex.Index.create()
        
        try:
            # Parse the file with compilation arguments
            translation_unit = index.parse(file_path, args=compile_args)
            
            if translation_unit is None:
                print(f"Failed to parse {file_path}")
                return []
            
            functions = []
            self._extract_functions(translation_unit.cursor, functions, file_path)
            
            print(f"Found {len(functions)} functions in {file_path}")
            return functions
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_functions(self, cursor, functions: List[Dict[str, Any]], file_path: str):
        """Recursively extract function information from AST"""
        if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            function_info = self._get_function_info(cursor, file_path)
            if function_info:
                functions.append(function_info)
        
        # Recursively process child nodes
        for child in cursor.get_children():
            self._extract_functions(child, functions, file_path)
    
    def _get_function_info(self, cursor, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract detailed information about a function"""
        try:
            # Get function signature
            return_type = cursor.result_type.spelling
            function_name = cursor.spelling
            
            # Extract parameters
            parameters = []
            for i, arg in enumerate(cursor.get_arguments()):
                param_type = arg.type.spelling
                param_name = arg.spelling or f"param_{i}"
                parameters.append({
                    'name': param_name,
                    'type': param_type,
                    'position': i
                })
            
            # Determine language and accessibility
            is_static = cursor.storage_class == clang.cindex.StorageClass.STATIC
            access_specifier = self._get_access_specifier(cursor)
            
            return {
                'name': function_name,
                'return_type': return_type,
                'parameters': parameters,
                'file': file_path,
                'line': cursor.location.line,
                'is_static': is_static,
                'access_specifier': access_specifier,
                'language': 'cpp' if file_path.endswith(('.cpp', '.cc', '.cxx')) else 'c'
            }
            
        except Exception as e:
            print(f"Error extracting function info: {e}")
            return None
    
    def _get_access_specifier(self, cursor) -> str:
        """Get C++ access specifier (public, private, protected)"""
        try:
            # This is a simplified approach - may need more complex logic
            if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
                return 'public'
            elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
                return 'private'
            elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
                return 'protected'
            return 'public'  # Default for C functions
        except:
            return 'public'
    
    def get_function_dependencies(self, cursor, file_path: str, compile_args: List[str]) -> Dict[str, Any]:
        """Analyze function dependencies (called functions, macros, etc.)"""
        called_functions = []
        macros_used = []
        data_structures = []
        
        # Analyze function body for dependencies
        self._analyze_dependencies(cursor, called_functions, macros_used, data_structures)
        
        return {
            'called_functions': called_functions,
            'macros_used': macros_used,
            'data_structures': data_structures
        }
    
    def _analyze_dependencies(self, cursor, called_functions: List, macros_used: List, data_structures: List):
        """Recursively analyze AST for dependencies"""
        # Check if this is a function call
        if cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
            called_func = cursor.referenced
            if called_func and called_func.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                func_info = {
                    'name': called_func.spelling,
                    'location': f"{called_func.location.file}:{called_func.location.line}"
                }
                if func_info not in called_functions:
                    called_functions.append(func_info)
        
        # Check for macro usage
        elif cursor.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
            macro_name = cursor.spelling
            if macro_name and macro_name not in macros_used:
                macros_used.append(macro_name)
        
        # Check for data structure usage (struct/class types)
        elif cursor.kind in [clang.cindex.CursorKind.STRUCT_DECL, clang.cindex.CursorKind.CLASS_DECL]:
            struct_name = cursor.spelling
            if struct_name and struct_name not in data_structures:
                data_structures.append(struct_name)
        
        # Recursively process children
        for child in cursor.get_children():
            self._analyze_dependencies(child, called_functions, macros_used, data_structures)