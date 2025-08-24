"""
Clang-based C/C++ code analyzer using libclang
"""

import clang.cindex
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.libclang_config import ensure_libclang_configured
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ClangAnalyzer:
    """C/C++ code analyzer using libclang AST parsing"""
    
    def __init__(self):
        # Configure libclang using unified configuration
        ensure_libclang_configured()
    
    def analyze_file(self, file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """Analyze a C/C++ file and extract function information"""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        logger.info(f"Analyzing {file_path} with args: {compile_args}")
        
        index = clang.cindex.Index.create()
        
        try:
            # First pass: find all function definitions in the TU
            translation_unit = index.parse(file_path, args=compile_args, options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
            
            if translation_unit is None:
                logger.error(f"Failed to parse {file_path}")
                return []
            
            functions = []
            function_definitions = {}
            self._extract_functions(translation_unit.cursor, functions, function_definitions, file_path)
            
            # Store the definition map on the analyzer instance for later use
            if not hasattr(self, 'function_definition_map'):
                self.function_definition_map = {}
            self.function_definition_map.update(function_definitions)

            logger.info(f"Found {len(functions)} functions in {file_path}")
            return functions
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _extract_functions(self, cursor, functions: List[Dict[str, Any]], function_definitions: Dict[str, Any], file_path: str):
        """Recursively extract function information from AST"""
        seen_functions = set()
        
        def _extract_recursive(cursor):
            if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                if cursor.is_definition():
                    function_info = self._get_function_info(cursor, file_path)
                    if function_info:
                        # Add to the definition map
                        function_definitions[function_info['name']] = cursor

                        # Use function name and file location as unique identifier
                        func_id = f"{function_info['name']}:{function_info['file']}"
                        if func_id not in seen_functions:
                            seen_functions.add(func_id)
                            functions.append(function_info)
            
            # Recursively process child nodes
            for child in cursor.get_children():
                _extract_recursive(child)
        
        _extract_recursive(cursor)
    
    def _get_function_info(self, cursor, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract detailed information about a function"""
        try:
            # Get function signature
            return_type = cursor.result_type.spelling
            function_name = cursor.spelling
            
            # Get the actual file location from the cursor
            actual_file = str(cursor.location.file) if cursor.location.file else file_path
            
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
            
            # Extract function body
            function_body = self._extract_function_body(cursor)
            
            return {
                'name': function_name,
                'return_type': return_type,
                'parameters': parameters,
                'file': actual_file,
                'line': cursor.location.line,
                'is_static': is_static,
                'access_specifier': access_specifier,
                'language': 'cpp' if actual_file.endswith(('.cpp', '.cc', '.cxx')) else 'c',
                'body': function_body
            }
            
        except Exception as e:
            logger.error(f"Error extracting function info: {e}")
            return None
    
    def _extract_function_body(self, cursor) -> str:
        """Extract the function body from cursor"""
        try:
            if not cursor.is_definition():
                return ""
            
            # Get the source range of the function body
            extent = cursor.extent
            start = extent.start
            end = extent.end
            
            # Read the source file and extract the function body
            source_file = start.file
            if source_file:
                with open(source_file.name, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Extract lines from start to end (1-based to 0-based conversion)
                    body_lines = lines[start.line-1:end.line]
                    return ''.join(body_lines).strip()
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting function body: {e}")
            return ""
    
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
        macro_definitions = []
        data_structures = []
        include_directives = []
        
        # Analyze function body for dependencies
        self._analyze_dependencies(cursor, called_functions, macros_used, macro_definitions, data_structures, include_directives)
        
        # Extract full macro definitions for used macros
        full_macro_defs = self._get_macro_definitions(macros_used, file_path, compile_args)
        
        return {
            'called_functions': called_functions,
            'macros_used': macros_used,
            'macro_definitions': full_macro_defs,
            'data_structures': data_structures,
            'include_directives': include_directives
        }
    
    def _analyze_dependencies(self, cursor, called_functions: List, macros_used: List, 
                            macro_definitions: List, data_structures: List, include_directives: List):
        """Recursively analyze AST for dependencies, now extracting full data structure definitions."""
        # Helper to extract source text from a cursor's extent
        def _extract_source_text(node_cursor):
            if not node_cursor or not node_cursor.extent.start.file:
                return ""
            try:
                with open(node_cursor.extent.start.file.name, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    body_lines = lines[node_cursor.extent.start.line-1 : node_cursor.extent.end.line]
                    return ''.join(body_lines).strip()
            except Exception:
                return ""

        # Helper to add a data structure definition if it's not already present
        def _add_data_structure_definition(def_cursor):
            if not def_cursor or not def_cursor.is_definition():
                return

            type_name = def_cursor.spelling or def_cursor.type.spelling
            if not any(d['name'] == type_name for d in data_structures):
                source_text = _extract_source_text(def_cursor)
                if source_text:
                    data_structures.append({
                        'name': type_name,
                        'definition': source_text
                    })

        # Check if this is a function call
        if cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
            called_func_name = cursor.referenced.spelling
            # Look up the full definition from our map
            called_func_def_cursor = self.function_definition_map.get(called_func_name)

            if called_func_def_cursor:
                # Extract info from the full definition cursor, which is reliable
                try:
                    param_decls = [p.type.spelling + ' ' + p.spelling for p in called_func_def_cursor.get_arguments()]
                    params = ', '.join(param_decls)
                    declaration = f"{called_func_def_cursor.result_type.spelling} {called_func_name}({params});"
                    is_mockable = called_func_def_cursor.storage_class != clang.cindex.StorageClass.STATIC
                except Exception:
                    declaration = f"{called_func_def_cursor.result_type.spelling} {called_func_name}(...);" # Fallback
                    is_mockable = True # Assume mockable on error
            else:
                # Fallback for functions not in our map (e.g., standard library)
                declaration = f"{cursor.referenced.result_type.spelling} {called_func_name}(...);"
                is_mockable = True # Assume external functions are mockable

            func_info = {
                'name': called_func_name,
                'declaration': declaration,
                'is_mockable': is_mockable,
                'location': f"{cursor.referenced.location.file.name if cursor.referenced.location.file else 'unknown'}:{cursor.referenced.location.line}",
            }
            if not any(d['name'] == func_info['name'] for d in called_functions):
                called_functions.append(func_info)
        
        # Check for macro usage
        elif cursor.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
            macro_name = cursor.spelling
            if macro_name and macro_name not in macros_used:
                macros_used.append(macro_name)

        # Check for data structure definitions or references
        elif cursor.kind in [clang.cindex.CursorKind.STRUCT_DECL, clang.cindex.CursorKind.CLASS_DECL, clang.cindex.CursorKind.TYPEDEF_DECL, clang.cindex.CursorKind.TYPE_REF]:
            def_cursor = None
            if cursor.kind == clang.cindex.CursorKind.TYPE_REF:
                def_cursor = cursor.type.get_declaration()
            else:
                def_cursor = cursor

            # For typedefs, get the underlying type declaration if it's a struct/class
            if def_cursor.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                underlying_type = def_cursor.underlying_typedef_type.get_canonical()
                decl = underlying_type.get_declaration()
                if decl.kind in [clang.cindex.CursorKind.STRUCT_DECL, clang.cindex.CursorKind.CLASS_DECL]:
                    _add_data_structure_definition(decl)
            
            _add_data_structure_definition(def_cursor)

        # Check for include directives
        elif cursor.kind == clang.cindex.CursorKind.INCLUSION_DIRECTIVE:
            included_file = cursor.spelling
            if included_file and included_file not in include_directives:
                include_directives.append(included_file)
        
        # Recursively process children
        for child in cursor.get_children():
            self._analyze_dependencies(child, called_functions, macros_used, macro_definitions,
                                     data_structures, include_directives)
    
    def _extract_macro_definition(self, cursor) -> Dict[str, Any]:
        """Extract complete macro definition information"""
        try:
            macro_name = cursor.spelling
            
            # Skip system macros (those starting with __)
            if macro_name.startswith('__'):
                return None
            
            # Get macro definition location safely
            location_file = cursor.location.file
            if not location_file:
                return None  # Skip macros without file location (usually system macros)
            
            location_str = f"{location_file.name}:{cursor.location.line}"
            
            # Extract macro tokens to get the full definition
            tokens = list(cursor.get_tokens())
            if len(tokens) >= 2:
                # The first token is the macro name, the rest is the definition
                definition_tokens = [t.spelling for t in tokens[1:]]
                full_definition = ' '.join(definition_tokens).strip()
            else:
                full_definition = ""
            
            # Check if it's a function-like macro
            is_function_like = any('(' in token.spelling for token in tokens if token.spelling)
            has_parameters = len(tokens) > 1 and '(' in tokens[1].spelling if len(tokens) > 1 else False
            
            return {
                'name': macro_name,
                'definition': full_definition,
                'location': location_str,
                'is_function_like': is_function_like,
                'has_parameters': has_parameters
            }
            
        except Exception as e:
            logger.error(f"Error extracting macro definition: {e}")
            return None
    
    def _get_macro_definitions(self, macro_names: List[str], file_path: str, compile_args: List[str]) -> List[Dict[str, Any]]:
        """Get full definitions for specific macros by parsing the file"""
        if not macro_names:
            return []
        
        try:
            index = clang.cindex.Index.create()
            translation_unit = index.parse(file_path, args=compile_args, 
                                         options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
            
            if translation_unit is None:
                return []
            
            macro_definitions = []
            
            # Recursively find all macro definitions in the file
            def _find_macro_defs(cursor):
                if cursor.kind == clang.cindex.CursorKind.MACRO_DEFINITION:
                    macro_def = self._extract_macro_definition(cursor)
                    if macro_def and macro_def['name'] in macro_names:
                        macro_definitions.append(macro_def)
                
                for child in cursor.get_children():
                    _find_macro_defs(child)
            
            _find_macro_defs(translation_unit.cursor)
            return macro_definitions
            
        except Exception as e:
            logger.error(f"Error getting macro definitions: {e}")
            return []