"""
Prompt templates for LLM test generation with language-specific variations
"""

from typing import Dict, Any


import json

class PromptTemplates:
    """Templates for generating high-quality test generation prompts"""
    
    # System prompts for different languages
    SYSTEM_PROMPTS = {
        'c': "你是一个专业的C语言单元测试工程师，专门生成Google Test + MockCpp测试用例。",
        'cpp': "你是一个专业的C++单元测试工程师，专门生成Google Test + MockCpp测试用例。",
        'default': "你是一个专业的C/C++单元测试工程师，专门生成Google Test + MockCpp测试用例。"
    }
    
    @staticmethod
    def get_system_prompt(language: str) -> str:
        """Get appropriate system prompt based on language"""
        return PromptTemplates.SYSTEM_PROMPTS.get(language, PromptTemplates.SYSTEM_PROMPTS['default'])
    
    @staticmethod
    def generate_test_prompt(compressed_context: Dict[str, Any]) -> str:
        """Generate comprehensive test generation prompt with a structured approach."""
        target = compressed_context['target_function']
        deps = compressed_context['dependencies']
        comp = compressed_context['compilation_info']
        
        language = target.get('language', 'c')
        language_display = 'C++' if language == 'cpp' else 'C'
        
        # Determine if mocking is needed
        has_external_deps = bool(deps.get('called_functions'))

        prompt_parts = [
            "# 1. 角色与目标 (Role & Goal)",
            f"你是一位精通{language_display}和Google Test框架的资深软件测试工程师。",
            "你的核心任务是为下方指定的函数，生成一个完整、正确且健壮的Google Test单元测试文件。",
            "",
            "# 2. 被测函数 (Function Under Test - FUT)",
            f"*   **文件路径:** `{target['location']}`",
            f"*   **函数签名:** `{target['signature']}`",
            f"*   **函数体:**",
            f"    ```{language_display.lower()}",
            target['body'],
            "    ```",
            "",
            "# 3. 上下文与依赖 (Context & Dependencies)"
        ]

        # Add dependency definitions if available
        if deps.get('dependency_definitions'):
            prompt_parts.append("*   **关键依赖项源码:**")
            for definition in deps['dependency_definitions']:
                prompt_parts.extend([
                    f"    ```{language_display.lower()}",
                    definition,
                    "    ```"
                ])
        
        # Add macro definitions if available
        if deps.get('macro_definitions'):
            prompt_parts.append("*   **相关宏定义:**")
            for macro_def in deps['macro_definitions']:
                prompt_parts.append(f"    *   `#define {macro_def['name']} {macro_def.get('definition', '')}`")
        prompt_parts.extend([
            "# 4. 测试生成要求 (Test Generation Requirements)",
            "1.  **测试框架:** 必须使用 **Google Test** (`gtest`).",
        ])

        if has_external_deps:
            prompt_parts.append("2.  **依赖函数分析:**")
            for func in deps['called_functions']:
                mock_status = "可以Mock" if func.get('is_mockable', True) else "不可Mock (static)"
                declaration = func.get('declaration', f"{func['name']} (...)")
                prompt_parts.append(f"    *   `{declaration}` - **{mock_status}**")

        # Add comprehensive MockCpp guidance with correct syntax examples
        mockcpp_guidance = [
            "3.  **MockCpp使用指导 (正确语法):",
            f"    *   **语言:** {language_display}",
            "    *   **Mock方法:** 使用 `MOCKER(function_name)` 进行函数Mock",
            "    *   **正确语法示例 (不要使用Google Mock语法):",
            "        ```cpp",
            "        // 正确: MockCpp链式调用",
            "        MOCKER(malloc)",
            "            .stubs()",
            "            .with(eq(sizeof(LinkedList)))",
            "            .will(returnValue(&fake_list));",
            "        ",
            "        // 正确: 带调用次数验证",
            "        MOCKER(create_node)",
            "            .expects(once())",
            "            .with(eq(42))",
            "            .will(returnValue(&mock_node));",
            "        ",
            "        // 错误: 不要使用Google Mock语法",
            "        // mock().expectOneCall(\"malloc\").withParameter(\"size\", size).andReturnValue(ptr);",
            "        ```",
            "    *   **核心方法:",
            "        - `.stubs()` - 不校验调用次数",
            "        - `.expects(times)` - 校验调用次数 (`once()/never()/exactly(n)/atLeast(n)/atMost(n)`)",
            "        - `.with(constraints)` - 参数约束 (`eq(v)/neq(v)/any()/spy(var)/outBound(var)/outBoundP(ptr,size)`)",
            "        - `.will(behavior)` - 函数行为 (`returnValue(v)/returnObjectList(v1,v2)/repeat(v,t)/ignoreReturnValue()/throws(e)`)",
            "    *   **验证:** 在teardown中使用 `GlobalMockObject::verify()`",
            "    *   **最佳实践:**",
            "        - 使用`MOCKER(function)`MockC函数和静态成员函数",
            "        - 使用`MockObject<Class>obj;MOCK_METHOD(obj,method)`Mock类成员函数",
            "        - 有返回值函数必须使用`.will(...)`指定返回值",
            "        - 避免Mock标准库函数和系统调用",
            "        - 优先Mock自定义辅助函数和工具函数",
            "        - 使用`.id()`和`.before()/.after()`进行调用顺序验证",
            "        - 使用`.with()`进行参数验证和输出参数设置"
        ]
        

        prompt_parts.extend(mockcpp_guidance)
        prompt_parts.extend([
            "4.  **核心测试场景:",
            "    *   **正常流程:** 测试函数在典型、有效输入下的行为。",
            "    *   **边界条件:** 测试极限值、空值或特殊值（如0, -1）作为输入。",
            "    *   **异常/错误处理:** 如果适用，测试函数在接收到无效输入或依赖项失败时的错误处理逻辑。",
            "5.  **断言要求:",
            "    *   使用 Google Test 提供的断言宏（如 `EXPECT_EQ`, `ASSERT_TRUE`）来验证结果。",
            "    *   如果使用了 Mock，请使用 `EXPECT_CALL` 来验证与依赖项的交互。",
            "",
            "# 5. 指令与输出格式 (Instructions & Output Format)",
            "1.  **思维链 (Chain of Thought):** 在编写代码之前，请先在心中构思或以注释形式列出你计划实现的测试用例大纲。",
            "2.  **输出单一完整文件:** 生成一个独立的、完整的 C++ 测试文件 (`.cpp`)。",
            "    *   不要包含 `main` 函数。",
            "    *   确保包含所有必要的头文件 (`gtest/gtest.h`, `MockCpp/MockCpp.h`, 以及被测函数和其依赖的头文件)。",
            "",
            "请现在开始生成你的测试代码:",
            f"```{language_display.lower()}"
        ])
        
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