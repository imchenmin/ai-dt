"""
Context compressor for LLM-friendly test generation
"""

from typing import Dict, Any, List


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
        """Compress dependency information"""
        called_funcs = context.get('called_functions', [])
        macros = context.get('macros_used', [])
        data_structs = context.get('data_structures', [])
        
        return {
            'called_functions': [
                {'name': f['name'], 'location': f.get('location', 'unknown')}
                for f in called_funcs[:3]  # Top 3 most relevant
            ],
            'macros': macros[:2],  # Top 2 macros
            'data_structures': data_structs[:2]  # Top 2 data structures
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
        """Format compressed context for LLM prompt"""
        target = compressed_context['target_function']
        deps = compressed_context['dependencies']
        usage = compressed_context['usage_patterns']
        comp = compressed_context['compilation_info']
        
        prompt_parts = [
            "# 目标函数信息",
            f"函数签名: {target['signature']}",
            f"返回类型: {target['return_type']}",
            f"参数: {', '.join([p['type'] + ' ' + p['name'] for p in target['parameters']])}",
            f"语言: {target['language'].upper()}",
            f"静态函数: {'是' if target['is_static'] else '否'}",
            f"访问权限: {target['access_specifier']}",
            "",
            "# 函数实现预览",
            f"```{target['language']}",
            target['body_preview'],
            "```",
            "",
            "# 依赖分析",
            f"调用的函数: {', '.join([f['name'] for f in deps['called_functions']]) or '无'}",
            f"使用的宏: {', '.join(deps['macros']) or '无'}",
            f"关键数据结构: {', '.join(deps['data_structures']) or '无'}",
            "",
            "# 使用示例"
        ]
        
        for i, site in enumerate(usage, 1):
            prompt_parts.extend([
                f"示例 {i} - {site['file']}:{site['line']}:",
                f"```c",
                site['context_preview'],
                f"```",
                ""
            ])
        
        prompt_parts.extend([
            "# 编译信息",
            f"关键编译标志: {', '.join(comp['key_flags']) or '无'}",
            f"总标志数量: {comp['total_flags_count']}",
            "",
            "# 测试生成要求",
            "请基于以上信息生成Google Test + MockCpp测试用例，包含:",
            "1. 完整的测试文件包含必要头文件",
            "2. 使用Google Test断言",
            "3. 为外部依赖函数生成Mock",
            "4. 包含边界条件测试",
            "5. 异常情况处理",
            "6. 测试用例覆盖正常流程和边界情况",
            "",
            "生成的测试代码:"
        ])
        
        return '\n'.join(prompt_parts)