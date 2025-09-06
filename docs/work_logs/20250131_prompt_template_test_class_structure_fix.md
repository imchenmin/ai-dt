# Prompt Template Test Class Structure Fix - 2025-01-31

## 问题描述

在运行 `test_prompt_templates_enhancement.py` 测试时，发现多个测试用例失败，主要涉及推荐测试类结构部分的处理。

### 主要问题

1. **现有测试上下文部分标题缺失**：当 `existing_test_functions` 为空时，测试期望显示标题，但实际没有显示
2. **推荐测试类结构处理不完整**：
   - 没有正确处理现有测试类定义
   - 缺少默认测试类模板的生成
   - `TargetFunction` 对象属性访问错误（使用了不存在的 `file` 属性）

## 修复过程

### 第一步：修复现有测试上下文标题显示

**问题**：`_build_existing_tests_section` 方法只在有测试函数时才显示标题

**修复**：将标题和提示信息的添加逻辑移至 `existing_test_functions` 判断之外

```python
# 修复前
if existing_tests.existing_test_functions:
    existing_tests_lines.append("\n# 3.1. 现有测试上下文 (Existing Test Context)")
    existing_tests_lines.append("**重要提示:** 以下是在单元测试目录中发现的与当前待测函数相关的现有测试信息")

# 修复后
existing_tests_lines.append("\n# 3.1. 现有测试上下文 (Existing Test Context)")
existing_tests_lines.append("**重要提示:** 以下是在单元测试目录中发现的与当前待测函数相关的现有测试信息")

if existing_tests.existing_test_functions or existing_tests.existing_test_classes:
    # 处理测试函数和测试类
```

### 第二步：添加现有测试类处理逻辑

**问题**：`_build_existing_tests_section` 方法没有处理 `existing_test_classes`

**修复**：添加测试类定义的处理逻辑

```python
# 添加现有测试类处理
if existing_tests.existing_test_classes:
    existing_tests_lines.append("\n**现有测试类:**")
    for test_class in existing_tests.existing_test_classes:
        existing_tests_lines.append(f"\n```cpp")
        existing_tests_lines.append(test_class.definition)
        existing_tests_lines.append("```")
```

### 第三步：修复推荐测试类结构生成

**问题1**：`_build_test_class_structure_section` 方法在没有现有测试类时返回空字符串，但测试期望显示默认模板

**问题2**：访问了不存在的 `ctx.target_function.file` 属性

**修复**：
1. 修改逻辑，在没有现有测试类时生成默认模板
2. 使用正确的 `location` 属性并解析文件路径

```python
@staticmethod
def _build_test_class_structure_section(ctx: PromptContext) -> str:
    """Build test class structure section"""
    # Extract test class information from existing tests
    if ctx.existing_tests_context and ctx.existing_tests_context.existing_test_classes:
        return "\n\n## 测试类结构 (Test Class Structure)\n" + \
               "请遵循现有测试类的结构和命名约定。"
    
    # Generate default test class template when no existing classes
    # Extract function name for test class naming
    function_name = ctx.target_function.name if ctx.target_function else "test"
    # Extract module name from location (format: "file:line")
    if ctx.target_function and ctx.target_function.location:
        # Extract file path from location (before the colon)
        file_path = ctx.target_function.location.split(':')[0]
        module_name = Path(file_path).stem
    else:
        module_name = "test"
    
    test_class_name = f"{module_name}_test"
    
    default_template = f"""\n\n## 推荐测试类结构 (Recommended Test Class Structure)
请使用以下测试类结构：

```cpp
class {test_class_name} : public ::testing::Test {{
protected:
    void SetUp() override {{
        // 仅在确实需要时添加共同的初始化代码
        // 大多数情况下可以为空
    }}
    void TearDown() override {{
        GlobalMockObject::verify();
    }}
    // 避免添加成员变量，除非多个测试确实需要相同的复杂对象
}};
```"""
    
    return default_template
```

## 测试验证

修复完成后，所有相关测试都通过：

```bash
# 单个测试验证
python -m pytest tests/unit/test_prompt_templates_enhancement.py::TestPromptTemplatesEnhancement::test_recommended_test_class_without_existing_classes -v
python -m pytest tests/unit/test_prompt_templates_enhancement.py::TestPromptTemplatesEnhancement::test_recommended_test_class_without_existing_context -v

# 全部测试验证
python -m pytest tests/unit/test_prompt_templates_enhancement.py -v
```

所有 5 个测试用例都通过：
- `test_existing_test_context_simplified_format`
- `test_recommended_test_class_with_existing_classes`
- `test_recommended_test_class_without_existing_classes`
- `test_recommended_test_class_without_existing_context`
- `test_existing_test_context_section_presence`

## 修复的文件

- `src/utils/prompt_templates.py`
  - `_build_existing_tests_section` 方法：修复标题显示逻辑，添加测试类处理
  - `_build_test_class_structure_section` 方法：添加默认模板生成，修复属性访问错误

## 总结

这次修复解决了 prompt 模板系统中关于现有测试上下文和推荐测试类结构的处理问题。主要改进包括：

1. **完善了现有测试上下文的显示逻辑**：确保即使没有测试函数也显示相关标题
2. **添加了现有测试类的处理**：正确显示现有测试类定义
3. **实现了默认测试类模板生成**：在没有现有测试类时提供标准模板
4. **修复了属性访问错误**：使用正确的 `location` 属性替代不存在的 `file` 属性

这些修复确保了 prompt 模板系统能够正确处理各种测试上下文场景，为 LLM 生成高质量的测试代码提供了更好的指导。