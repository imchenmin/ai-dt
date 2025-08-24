"""
Prompt templates for LLM test generation with language-specific variations
"""

from typing import Dict, Any


class PromptTemplates:
    """Templates for generating high-quality test generation prompts"""
    
    # System prompts for different languages
    SYSTEM_PROMPTS = {
        'c': "你是一个专业的C语言单元测试工程师，专门生成Google Test测试用例。",
        'cpp': "你是一个专业的C++单元测试工程师，专门生成Google Test + MockCpp测试用例。",
        'default': "你是一个专业的C/C++单元测试工程师，专门生成Google Test + MockCpp测试用例。"
    }
    
    @staticmethod
    def get_system_prompt(language: str) -> str:
        """Get appropriate system prompt based on language"""
        return PromptTemplates.SYSTEM_PROMPTS.get(language, PromptTemplates.SYSTEM_PROMPTS['default'])
    
    @staticmethod
    def generate_test_prompt(compressed_context: Dict[str, Any]) -> str:
        """Generate comprehensive test generation prompt"""
        target = compressed_context['target_function']
        deps = compressed_context['dependencies']
        usage = compressed_context['usage_patterns']
        comp = compressed_context['compilation_info']
        
        language = target.get('language', 'c')
        language_display = 'C++' if language == 'cpp' else 'C'
        
        # Determine if mocking is needed
        has_external_deps = bool(deps.get('called_functions'))
        
        prompt_parts = [
            "# 目标函数信息",
            f"函数签名: {target['signature']}",
            f"返回类型: {target['return_type']}",
            f"参数: {', '.join([p['type'] + ' ' + p['name'] for p in target['parameters']])}",
            f"语言: {language_display}",
            f"静态函数: {'是' if target['is_static'] else '否'}",
            f"访问权限: {target['access_specifier']}",
            f"位置: {target['location']}",
            "",
            "# 函数实现预览",
            f"```{language_display.lower()}",
            target['body_preview'],
            "```",
            "",
            "# 依赖分析",
            f"调用的函数: {', '.join([f['name'] for f in deps['called_functions']]) or '无'}",
            f"使用的宏: {', '.join(deps['macros']) or '无'}",
            "",
            "# 宏定义详情"
        ]
        
        # Add macro definitions if available
        if deps.get('macro_definitions'):
            for macro_def in deps['macro_definitions']:
                prompt_parts.extend([
                    f"宏 {macro_def['name']}:",
                    f"定义: {macro_def['definition']}",
                    f"位置: {macro_def['location']}",
                    ""
                ])
        else:
            prompt_parts.append("宏定义: 无详细定义信息")
            
        prompt_parts.extend([
            f"关键数据结构: {', '.join(deps['data_structures']) or '无'}",
            "",
            "# 使用示例"
        ])
        
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
            "# 测试生成要求"
        ])
        
        # Language-specific requirements
        if language == 'cpp':
            prompt_parts.extend([
                "请基于以上信息生成C++ Google Test测试用例，包含:",
                "1. 完整的测试文件包含必要头文件",
                "2. 使用Google Test断言",
                "3. 包含边界条件测试",
                "4. 异常情况处理",
                "5. 测试用例覆盖正常流程和边界情况",
                "6. 特别注意C++特有的内存管理和异常安全"
            ])
        else:
            prompt_parts.extend([
                "请基于以上信息生成C语言Google Test测试用例，包含:",
                "1. 完整的测试文件包含必要头文件", 
                "2. 使用Google Test断言",
                "3. 包含边界条件测试",
                "4. 错误情况处理",
                "5. 测试用例覆盖正常流程和边界情况"
            ])
        
        # Add mocking requirements only if needed
        if has_external_deps:
            prompt_parts.extend([
                "",
                "# Mock要求",
                "请为外部依赖函数生成MockCpp mock:",
                "1. 包含必要的MockCpp头文件",
                "2. 为每个外部函数创建适当的mock",
                "3. 设置合理的mock期望和返回值"
            ])
        
        prompt_parts.extend(["", "生成的测试代码:"])
        
        return '\n'.join(prompt_parts)
    
    @staticmethod
    def generate_memory_function_prompt(compressed_context: Dict[str, Any]) -> str:
        """Specialized prompt for memory management functions"""
        base_prompt = PromptTemplates.generate_test_prompt(compressed_context)
        
        # Add memory-specific guidance
        memory_guidance = """

# 内存函数特别指导
此函数涉及内存管理，请特别注意：
1. 测试内存分配和释放的正确性
2. 验证空指针的安全处理
3. 避免测试未定义行为（如重复释放）
4. 确保测试用例不会导致内存泄漏
5. 对于C++的delete/delete[]操作，验证异常安全

请生成安全、可靠的测试用例，避免危险的测试模式。
"""
        
        return base_prompt + memory_guidance
    
    @staticmethod
    def should_use_memory_template(function_info: Dict[str, Any]) -> bool:
        """Determine if memory function template should be used"""
        function_name = function_info.get('name', '').lower()
        return_type = function_info.get('return_type', '').lower()
        
        # Check for memory-related function names
        memory_keywords = ['free', 'delete', 'alloc', 'malloc', 'new', 'release', 'destroy']
        if any(keyword in function_name for keyword in memory_keywords):
            return True
        
        # Check for pointer return types
        pointer_types = ['*', 'void*']
        if any(ptype in return_type for ptype in pointer_types):
            return True
            
        return False