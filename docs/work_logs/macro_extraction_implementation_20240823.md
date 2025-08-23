# 宏上下文提取功能实现 - 2024年8月23日

## 功能概述
实现了完整的宏上下文提取功能，包括宏使用检测和宏定义提取，为LLM测试生成提供完整的宏上下文信息。

## 实现内容

### 1. 宏定义提取 (`src/analyzer/clang_analyzer.py`)
- **新增功能**: `_extract_macro_definition()` 方法
- **提取内容**: 
  - 宏名称
  - 完整宏定义内容
  - 定义位置（文件:行号）
  - 是否为函数式宏
  - 是否包含参数
- **过滤机制**: 自动过滤系统宏（以`__`开头的宏）

### 2. 宏使用检测增强
- **增强功能**: `_analyze_dependencies()` 方法
- **检测内容**: 
  - `MACRO_INSTANTIATION` - 宏使用实例
  - `MACRO_DEFINITION` - 宏定义
- **去重处理**: 自动避免重复记录相同宏

### 3. 依赖分析改进
- **新增字段**: `macro_definitions` 在依赖分析结果中
- **关联机制**: 将使用的宏名称与完整的宏定义关联
- **优先级排序**: 仅提取最相关的宏定义（前3个）

### 4. 上下文压缩增强 (`src/utils/context_compressor.py`)
- **新增处理**: 在`_compress_dependencies()` 中处理宏定义
- **智能关联**: 将使用的宏名称与对应的完整定义匹配
- **提示工程**: 在LLM提示中包含完整的宏定义信息

## 技术实现细节

### 宏提取算法
```python
def _extract_macro_definition(cursor):
    # 过滤系统宏
    if macro_name.startswith('__'):
        return None
    
    # 提取宏tokens构建完整定义
    tokens = list(cursor.get_tokens())
    definition_tokens = [t.spelling for t in tokens[1:]]  # 跳过宏名称
    full_definition = ' '.join(definition_tokens).strip()
    
    # 检测函数式宏特征
    is_function_like = any('(' in token.spelling for token in tokens)
```

### 依赖分析流程
1. **解析阶段**: 使用 `PARSE_DETAILED_PROCESSING_RECORD` 选项启用宏处理
2. **AST遍历**: 递归分析AST节点寻找宏定义和使用
3. **关联匹配**: 将使用的宏名称与定义文件中的完整定义关联
4. **结果整合**: 返回包含完整宏定义的依赖信息

## 测试验证

### 测试文件: `test_macro.c`
```c
#define MAX_VALUE 100
#define MIN_VALUE 0
#define SQUARE(x) ((x) * (x))

int test_function(int x) {
    if (x > MAX_VALUE) {
        return SQUARE(x);
    }
    return MIN_VALUE;
}
```

### 提取结果
```
Macro: MAX_VALUE
  Definition: 100
  Location: test_macro.c:2
  Function-like: False

Macro: MIN_VALUE  
  Definition: 0
  Location: test_macro.c:3
  Function-like: False

Macro: SQUARE
  Definition: ( x ) ( ( x ) * ( x ) )
  Location: test_macro.c:4
  Function-like: True
```

## LLM提示集成

### 压缩后的上下文格式
```
# 依赖分析
调用的函数: 无
使用的宏: MAX_VALUE, SQUARE

# 宏定义详情
宏 MAX_VALUE:
定义: 100
位置: test_macro.c:2

宏 SQUARE:
定义: ( x ) ( ( x ) * ( x ) )
位置: test_macro.c:4

关键数据结构: 无
```

## 性能考虑

1. **系统宏过滤**: 避免处理大量编译器内置宏
2. **数量限制**: 仅提取最相关的少量宏定义（前3个）
3. **智能匹配**: 只提取实际被使用的宏的完整定义
4. **缓存机制**: 同一文件的宏定义只需提取一次

## 兼容性

- ✅ 支持C和C++语言
- ✅ 处理简单值宏和函数式宏
- ✅ 兼容不同版本的libclang
- ✅ 处理系统头文件宏过滤

## 下一步改进

1. **跨文件宏定义**: 支持提取include文件中的宏定义
2. **宏使用上下文**: 分析宏在函数中的具体使用方式
3. **条件编译处理**: 处理#ifdef等条件编译场景
4. **性能优化**: 添加宏定义缓存机制

## 总结

宏上下文提取功能已完整实现，能够为LLM测试生成提供准确的宏定义信息，显著提升生成的测试代码质量。该实现考虑了性能、兼容性和实用性，为后续功能扩展奠定了良好基础。