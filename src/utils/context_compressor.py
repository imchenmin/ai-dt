"""
Context compressor for LLM-friendly test generation
"""

from typing import Dict, Any, List
from .prompt_templates import PromptTemplates


class ContextCompressor:
    """Compresses analysis context for LLM consumption"""
    
    def __init__(self, max_context_size: int = 8000):
        self.max_context_size = max_context_size
    
    def compress_function_context(self, function_info: Dict[str, Any], 
                                full_context: Dict[str, Any]) -> Dict[str, Any]:
        """Compress function context for LLM test generation"""
        compressed = {
            'target_function': self._compress_target_function(function_info),
            'dependencies': self._compress_dependencies(full_context),
            'usage_patterns': self._compress_usage_patterns(full_context),
            'compilation_info': self._compress_compilation_info(full_context)
        }
        
        # Further compress if needed to fit token limit
        return self._ensure_size_limit(compressed)
    
    def _compress_target_function(self, function_info: Dict[str, Any]) -> Dict[str, Any]:
        """Compress information about the target function"""
        return {
            'name': function_info['name'],
            'signature': self._format_function_signature(function_info),
            'return_type': function_info['return_type'],
            'parameters': [
                {'name': p['name'], 'type': p['type']} 
                for p in function_info['parameters']
            ],
            'body_preview': function_info['body'][:300],  # First 300 chars
            'location': f"{function_info['file']}:{function_info['line']}",
            'language': function_info.get('language', 'c'),
            'is_static': function_info.get('is_static', False),
            'access_specifier': function_info.get('access_specifier', 'public')
        }
    
    def _format_function_signature(self, function_info: Dict[str, Any]) -> str:
        """Format function signature string"""
        params = ', '.join([
            f"{p['type']} {p['name']}" for p in function_info['parameters']
        ])
        return f"{function_info['return_type']} {function_info['name']}({params})"
    
    def _compress_dependencies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compress dependency information, now expecting richer data structures."""
        called_funcs = context.get('called_functions', [])
        macros = context.get('macros_used', [])
        macro_defs = context.get('macro_definitions', [])
        # Assume data_structs is now a list of dicts: [{'name': str, 'definition': str}]
        data_structs = context.get('data_structures', [])
        
        # Get full definitions for used macros
        macro_definitions = []
        for macro_name in macros[:3]:  # Top 3 most relevant macros
            # Find definition for this macro
            for macro_def in macro_defs:
                if macro_def['name'] == macro_name:
                    macro_definitions.append(macro_def)
                    break
        
        # Extract names and definitions from the richer data structure
        struct_names = [s['name'] for s in data_structs[:2]]
        struct_definitions = [s['definition'] for s in data_structs[:2] if 'definition' in s]

        return {
            'called_functions': called_funcs[:3],  # Pass through the full dict
            'macros': macros[:3],
            'macro_definitions': macro_definitions[:2],
            'data_structures': struct_names, # Keep just the names here for backward compatibility
            'dependency_definitions': struct_definitions # Add the full definitions
        }
    
    def _compress_usage_patterns(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compress usage patterns from call sites"""
        call_sites = context.get('call_sites', [])
        
        compressed_sites = []
        for site in call_sites[:2]:  # Max 2 representative call sites
            compressed_sites.append({
                'file': site.get('file', 'unknown'),
                'line': site.get('line', 0),
                'context_preview': site.get('context', '')[:150]  # First 150 chars
            })
        
        return compressed_sites
    
    def _compress_compilation_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compress compilation information"""
        # Extract key compilation flags
        flags = context.get('compilation_flags', [])
        key_flags = [
            flag for flag in flags 
            if any(flag.startswith(prefix) for prefix in ['-I', '-D', '-std=', '-O'])
        ][:3]  # Top 3 relevant flags
        
        return {
            'key_flags': key_flags,
            'total_flags_count': len(flags)
        }
    
    def _ensure_size_limit(self, compressed_context: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure compressed context stays within size limits"""
        # Simple size estimation (can be improved with actual token counting)
        import json
        context_str = json.dumps(compressed_context, ensure_ascii=False)
        
        if len(context_str) > self.max_context_size:
            # Further compress by reducing preview lengths
            if 'target_function' in compressed_context:
                compressed_context['target_function']['body_preview'] = \
                    compressed_context['target_function']['body_preview'][:150]
            
            if 'usage_patterns' in compressed_context:
                for site in compressed_context['usage_patterns']:
                    if 'context_preview' in site:
                        site['context_preview'] = site['context_preview'][:100]
        
        return compressed_context
    
    def format_for_llm_prompt(self, compressed_context: Dict[str, Any]) -> str:
        """Format compressed context for LLM prompt using templates"""
        target = compressed_context['target_function']
        
        # Use specialized template for memory functions
        if PromptTemplates.should_use_memory_template(target):
            return PromptTemplates.generate_memory_function_prompt(compressed_context)
        
        # Use general template for other functions
        return PromptTemplates.generate_test_prompt(compressed_context)