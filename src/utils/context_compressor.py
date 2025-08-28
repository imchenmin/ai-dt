"""
Context compressor for LLM-friendly test generation with intelligent compression
"""

from typing import Dict, Any, List, Optional
from .prompt_templates import PromptTemplates
from .token_counter import TokenCounter, create_token_counter
from .dependency_ranker import DependencyRanker, select_top_dependencies, select_top_dependency_names, DependencyType


class ContextCompressor:
    """Compresses analysis context for LLM consumption"""
    
    def __init__(self, max_context_size: int = None, 
                 llm_provider: str = "openai", llm_model: str = "gpt-3.5-turbo"):
        """
        Initialize context compressor with intelligent token management
        
        Args:
            max_context_size: Maximum context size in characters (for backward compatibility)
            llm_provider: LLM provider name (openai, deepseek, mock)
            llm_model: Specific model name for token counting
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.token_counter = create_token_counter(llm_provider, llm_model)
        
        # For backward compatibility, use provided size or calculate from token limit
        if max_context_size is not None:
            self.max_context_size = max_context_size
        else:
            # Convert token limit to approximate character limit (4 chars per token)
            token_limit = self.token_counter.get_model_limit()
            self.max_context_size = token_limit * 4
    
    def compress_function_context(self, function_info: Dict[str, Any], 
                                full_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress function context for LLM test generation with intelligent selection
        
        Uses token counting and importance-based ranking to optimize context selection
        """
        # First pass: basic compression with importance ranking
        compressed = {
            'target_function': self._compress_target_function(function_info),
            'dependencies': self._compress_dependencies(full_context, function_info),
            'usage_patterns': self._compress_usage_patterns(full_context),
            'compilation_info': self._compress_compilation_info(full_context)
        }
        
        # Intelligent size management with token counting
        return self._ensure_optimal_size(compressed, function_info)
    
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
            'body': function_info['body'],  # Keep full function body
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
    
    def _compress_dependencies(self, context: Dict[str, Any], 
                              function_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress dependency information with intelligent ranking
        
        Uses importance-based selection instead of static limits
        """
        called_funcs = context.get('called_functions', [])
        macros = context.get('macros_used', [])
        macro_defs = context.get('macro_definitions', [])
        data_structs = context.get('data_structures', [])
        
        # Use dependency ranker for intelligent selection
        ranker = DependencyRanker(function_info)
        
        # Rank and select top dependencies
        ranked_functions = ranker.rank_called_functions(called_funcs, [])
        ranked_structs = ranker.rank_data_structures(data_structs)
        ranked_macros = ranker.rank_macros(macros, macro_defs)
        
        # Select top dependencies based on importance (use names for macro/struct selection)
        selected_functions = select_top_dependencies(ranked_functions, max_count=5)
        selected_struct_names = select_top_dependency_names(ranked_structs, max_count=3)
        selected_macro_names = select_top_dependency_names(ranked_macros, max_count=4)
        
        # Extract definitions for selected macros
        macro_definitions = []
        macro_def_map = {defn['name']: defn for defn in macro_defs}
        for macro_name in selected_macro_names:
            if macro_name in macro_def_map:
                macro_definitions.append(macro_def_map[macro_name])
        
        # Extract definitions for selected data structures

        # Extract function bodies for static functions to help understand implementation
        static_function_definitions = []
        for func in selected_functions:
            if func.get("is_static", False) and func.get("function_body"):
                static_function_definitions.append(func["function_body"])
        struct_definitions = []
        struct_map = {s['name']: s for s in data_structs}
        for struct_name in selected_struct_names:
            if struct_name in struct_map and 'definition' in struct_map[struct_name]:
                struct_definitions.append(struct_map[struct_name]['definition'])

        return {
            'called_functions': selected_functions,
            'macros': selected_macro_names,
            'macro_definitions': macro_definitions,
            'data_structures': selected_struct_names,
            'dependency_definitions': struct_definitions + static_function_definitions
        }
    
    def _compress_usage_patterns(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compress usage patterns from call sites with intelligent selection
        
        Prioritizes call sites that show different usage patterns
        """
        call_sites = context.get('call_sites', [])
        
        if not call_sites:
            return []
        
        # Group call sites by file to get diverse examples
        sites_by_file = {}
        for site in call_sites:
            file = site.get('file', 'unknown')
            if file not in sites_by_file:
                sites_by_file[file] = []
            sites_by_file[file].append(site)
        
        # Select up to 2 representative call sites from different files
        compressed_sites = []
        selected_files = set()
        
        for file, sites in sites_by_file.items():
            if len(compressed_sites) >= 2:
                break
            if file not in selected_files:
                # Take first site from this file
                site = sites[0]
                compressed_sites.append({
                    'file': site.get('file', 'unknown'),
                    'line': site.get('line', 0),
                    'context_preview': site.get('context', '')[:200]  # Slightly more context
                })
                selected_files.add(file)
        
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
    
    def _ensure_optimal_size(self, compressed_context: Dict[str, Any], 
                           function_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure compressed context stays within optimal size using token counting
        
        Applies progressive compression strategies based on token usage
        """
        # Calculate current token usage
        current_tokens = self.token_counter.count_tokens_from_dict(compressed_context)
        available_tokens = self.token_counter.get_available_tokens()
        
        # If within limits, return as-is
        if current_tokens <= available_tokens:
            return compressed_context
        
        # Apply progressive compression strategies
        compression_level = 0
        while current_tokens > available_tokens and compression_level < 3:
            compression_level += 1
            
            if compression_level == 1:
                # Level 1: Reduce non-critical content
                compressed_context = self._apply_compression_level_1(compressed_context)
            elif compression_level == 2:
                # Level 2: Reduce dependency details
                compressed_context = self._apply_compression_level_2(compressed_context, function_info)
            elif compression_level == 3:
                # Level 3: Aggressive compression
                compressed_context = self._apply_compression_level_3(compressed_context)
            
            # Recalculate token usage
            current_tokens = self.token_counter.count_tokens_from_dict(compressed_context)
        
        return compressed_context
    
    def _apply_compression_level_1(self, compressed_context: Dict[str, Any]) -> Dict[str, Any]:
        """Level 1 compression: Reduce non-critical content"""
        # Reduce function body preview - preserve full body for target function
        # Target function body is critical and should not be truncated
        
        # Reduce call site context
        if 'usage_patterns' in compressed_context:
            for site in compressed_context['usage_patterns']:
                if 'context_preview' in site:
                    site['context_preview'] = site['context_preview'][:150]
        
        return compressed_context
    
    def _apply_compression_level_2(self, compressed_context: Dict[str, Any], 
                                  function_info: Dict[str, Any]) -> Dict[str, Any]:
        """Level 2 compression: Reduce dependency details"""
        ranker = DependencyRanker(function_info)
        
        # Further compress dependencies with higher importance threshold
        if 'dependencies' in compressed_context:
            deps = compressed_context['dependencies']
            
            # Re-rank with higher importance threshold
            if 'called_functions' in deps:
                ranked_funcs = ranker.rank_called_functions(deps['called_functions'], [])
                deps['called_functions'] = select_top_dependencies(
                    ranked_funcs, max_count=3, 
                    min_importance=ranker._determine_importance_level(1.0)
                )
            
            # Reduce macro definitions
            if 'macro_definitions' in deps:
                deps['macro_definitions'] = deps['macro_definitions'][:2]
            
            # Reduce data structure definitions
            if 'dependency_definitions' in deps:
                deps['dependency_definitions'] = deps['dependency_definitions'][:1]
        
        return compressed_context
    
    def _apply_compression_level_3(self, compressed_context: Dict[str, Any]) -> Dict[str, Any]:
        """Level 3 compression: Aggressive reduction"""
        # Minimal function body - preserve full body for target function
        # Target function body is critical and should not be truncated
        
        # Remove usage patterns if still too large
        if 'usage_patterns' in compressed_context:
            compressed_context['usage_patterns'] = []
        
        # Minimal dependencies
        if 'dependencies' in compressed_context:
            deps = compressed_context['dependencies']
            if 'called_functions' in deps:
                deps['called_functions'] = deps['called_functions'][:1]
            if 'macro_definitions' in deps:
                deps['macro_definitions'] = []
            if 'dependency_definitions' in deps:
                deps['dependency_definitions'] = []
        
        return compressed_context
    
    def format_for_llm_prompt(self, compressed_context: Dict[str, Any]) -> str:
        """Format compressed context for LLM prompt using templates"""
        target = compressed_context['target_function']
        
        # Use specialized template for memory functions
        if PromptTemplates.should_use_memory_template(target):
            return PromptTemplates.generate_memory_function_prompt(compressed_context)
        
        # Use general template for other functions
        return PromptTemplates.generate_test_prompt(compressed_context)