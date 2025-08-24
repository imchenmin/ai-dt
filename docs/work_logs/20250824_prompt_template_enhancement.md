# 工作日志：提示词模板系统增强

## 日期：2025-08-24
## 负责人：Claude Code

## 任务概述
增强测试生成系统的提示词模板，解决语言混淆、Mock要求冲突和安全性问题。

## 问题识别
1. **语言标识问题**：`'cpp'` → `'CPP'` 导致混淆
2. **Mock要求冲突**：系统提示要求Mock但依赖分析显示无外部依赖
3. **安全性缺失**：内存管理函数缺少安全测试指导
4. **提示词分散**：提示生成逻辑分散在多个文件中

## 实施内容

### 1. 创建提示词模板系统 (`src/utils/prompt_templates.py`)
- **语言特定系统提示**：C和C++使用不同的系统提示
- **内存函数检测**：基于函数名和返回类型识别内存管理函数
- **动态Mock要求**：只有存在外部依赖时才要求Mock
- **安全指导**：为内存函数添加特别安全指导

### 2. 核心功能
```python
class PromptTemplates:
    # 语言特定系统提示
    SYSTEM_PROMPTS = {
        'c': "C语言单元测试工程师提示",
        'cpp': "C++单元测试工程师提示",
        'default': "通用C/C++提示"
    }
    
    # 内存函数检测逻辑
    @staticmethod
    def should_use_memory_template(function_info: Dict[str, Any]) -> bool
    
    # 主提示生成
    @staticmethod  
    def generate_test_prompt(compressed_context: Dict[str, Any]) -> str
    
    # 内存函数专用提示
    @staticmethod
    def generate_memory_function_prompt(compressed_context: Dict[str, Any]) -> str
```

### 3. 集成更新
- **ContextCompressor**：改用模板系统生成提示词
- **LLMClient**：添加语言参数，使用语言特定系统提示
- **TestGenerator**：传递语言信息给LLM客户端

## 改进效果

### 之前的问题提示词：
```
语言: CPP
...
请基于以上信息生成Google Test + MockCpp测试用例，包含:
3. 为外部依赖函数生成Mock  # 即使没有依赖也要求Mock
```

### 新的优化提示词：
```
语言: C++
...
请基于以上信息生成C++ Google Test测试用例，包含:
# 根据实际依赖动态显示Mock要求
6. 特别注意C++特有的内存管理和异常安全

# 内存函数特别指导
此函数涉及内存管理，请特别注意：
1. 测试内存分配和释放的正确性
2. 验证空指针的安全处理  
3. 避免测试未定义行为（如重复释放）
```

## 技术细节

### 语言处理改进
- **之前**: `'cpp'` → `'CPP'` (混淆)
- **现在**: `'cpp'` → `'C++'` (清晰)

### Mock要求逻辑
- **之前**: 总是要求Mock，即使没有外部依赖
- **现在**: 动态判断，只有 `deps['called_functions']` 不为空时才要求Mock

### 安全增强
- 自动识别内存管理函数（包含free/delete/alloc等关键词）
- 添加安全测试指导，避免危险测试模式
- 特别强调避免测试未定义行为

## 文件变更
- ✅ `src/utils/prompt_templates.py` (新增)
- ✅ `src/utils/context_compressor.py` (修改)
- ✅ `src/generator/llm_client.py` (修改) 
- ✅ `src/generator/test_generator.py` (修改)

## 验证方法
新的提示词系统会在下次测试生成时自动生效，生成更准确、安全的测试用例。

## 后续建议
1. 监控生成的测试用例质量改进
2. 考虑添加更多函数类型专用模板（如数学函数、字符串处理等）
3. 收集LLM响应数据优化提示词效果