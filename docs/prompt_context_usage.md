# PromptContext 使用指南

## 概述

`PromptContext` 是一个结构化的数据模型，用于替代之前传递给提示词模板的字典结构。它提供了类型安全、更好的代码可读性和维护性。

## 数据模型结构

### 核心类

- `PromptContext`: 主要的上下文容器
- `TargetFunction`: 被测试的目标函数信息
- `Dependencies`: 依赖项信息
- `CompilationInfo`: 编译相关信息
- `ExistingTestsContext`: 现有测试上下文

### 支持类

- `Language`: 编程语言枚举
- `Parameter`: 函数参数信息
- `CalledFunction`: 被调用函数信息
- `MacroDefinition`: 宏定义信息
- `UsagePattern`: 使用模式信息
- `TestFunction`: 测试函数信息
- `TestClass`: 测试类信息

## 使用示例

### 1. 创建基本的 PromptContext

```python
from test_generation.models import (
    PromptContext, TargetFunction, Dependencies, 
    CompilationInfo, Language, Parameter
)

# 创建目标函数
target = TargetFunction(
    name="calculate_sum",
    signature="int calculate_sum(int a, int b)",
    location="math_utils.c:15",
    return_type="int",
    parameters=[
        Parameter(name="a", type="int", description="第一个数字"),
        Parameter(name="b", type="int", description="第二个数字")
    ],
    description="计算两个整数的和"
)

# 创建依赖项
deps = Dependencies(
    called_functions=[],
    macro_definitions=[],
    usage_patterns=[]
)

# 创建编译信息
comp = CompilationInfo(
    include_paths=["/usr/include"],
    compile_flags=["-std=c99"],
    linked_libraries=["m"]
)

# 创建完整的上下文
context = PromptContext(
    target=target,
    dependencies=deps,
    compilation_info=comp,
    language=Language.C
)
```

### 2. 从字典创建 PromptContext

```python
# 原有的字典格式
compressed_context = {
    'target': {
        'name': 'hash_insert',
        'signature': 'int hash_insert(HashTable* table, const char* key, void* value)',
        'location': 'hash_table.c:145',
        'return_type': 'int',
        'parameters': [
            {'name': 'table', 'type': 'HashTable*', 'description': '哈希表指针'},
            {'name': 'key', 'type': 'const char*', 'description': '键'},
            {'name': 'value', 'type': 'void*', 'description': '值'}
        ]
    },
    'deps': {
        'called_functions': [
            {
                'name': 'hash_function',
                'declaration': 'unsigned int hash_function(const char* key)',
                'mockable': True
            }
        ]
    },
    'comp': {
        'include_paths': ['/usr/include'],
        'compile_flags': ['-std=c99']
    }
}

# 转换为结构化对象
context = PromptContext.from_dict(compressed_context)
```

### 3. 在 prompt_templates.py 中使用

```python
from test_generation.models import PromptContext
from utils.prompt_templates import PromptTemplates

# 使用新的结构化对象
context = PromptContext.from_dict(compressed_context)
prompt = PromptTemplates.generate_test_prompt(prompt_context=context)

# 或者继续支持旧的字典格式（向后兼容）
prompt = PromptTemplates.generate_test_prompt(compressed_context=compressed_context)
```

### 4. 处理现有测试上下文

```python
from test_generation.models import ExistingTestsContext, TestFunction, TestClass

# 创建现有测试上下文
existing_tests = ExistingTestsContext(
    existing_test_functions=[
        TestFunction(
            name="TEST_F(HashTableTest, InsertValidKey)",
            content="// 测试插入有效键",
            file_path="test_hash_table.cpp"
        )
    ],
    existing_test_classes=[
        TestClass(
            name="HashTableTest",
            definition="class HashTableTest : public ::testing::Test { ... }",
            file_path="test_hash_table.cpp"
        )
    ]
)

# 添加到主上下文
context.existing_tests_context = existing_tests
```

## 迁移指南

### 从字典到结构化对象

1. **自动转换**: 使用 `PromptContext.from_dict()` 方法
2. **渐进式迁移**: 新代码使用 `PromptContext`，旧代码保持兼容
3. **类型检查**: 利用 IDE 的类型提示功能

### 主要优势

1. **类型安全**: 编译时检查类型错误
2. **代码提示**: IDE 提供更好的自动完成
3. **文档化**: 每个字段都有明确的类型和含义
4. **验证**: 内置数据验证逻辑
5. **扩展性**: 易于添加新字段和方法

## 最佳实践

1. **优先使用结构化对象**: 新代码应该使用 `PromptContext`
2. **保持向后兼容**: 支持旧的字典格式以便平滑迁移
3. **使用类型提示**: 在函数签名中明确指定类型
4. **验证数据**: 利用模型的验证功能确保数据完整性

## 常见问题

### Q: 如何处理可选字段？
A: 使用 `Optional` 类型注解，并在 `from_dict` 方法中提供默认值。

### Q: 如何扩展现有模型？
A: 继承现有类或添加新的属性，确保向后兼容性。

### Q: 性能影响如何？
A: 结构化对象的创建开销很小，但提供了更好的类型安全和代码可读性。

## 相关文件

- `src/test_generation/models.py`: 数据模型定义
- `src/utils/prompt_templates.py`: 提示词模板使用
- `tests/`: 相关测试用例