# 函数过滤机制分析与改进 - 20250824

## 问题背景
在简化 `--config` 模式的过程中，发现自动函数检测会包含大量标准库函数，导致不必要的测试生成。

## 已实施的改进

### 1. 移除手动函数配置
- 删除了 `config/test_generation.yaml` 中的 `functions:` 配置节
- 实现了基于项目路径的自动函数检测

### 2. 基于项目路径的过滤
```python
def should_include_function(func, filter_config, project_config):
    # 只包含项目目录下的函数
    if project_path:
        abs_project_path = str(Path(project_path).absolute())
        abs_file_path = str(Path(file_path).absolute())
        if not abs_file_path.startswith(abs_project_path):
            return False
```

### 3. Glibc内联函数过滤
添加了对Glibc特定内联模式的检测：
- `__extern_inline`
- `__STDIO_INLINE` 
- `__THROW`

## 测试结果

### ✅ 简单C项目 (test_projects/c)
- 正确识别: add, subtract, divide, multiply
- 成功排除: main函数

### ✅ 复杂C项目 (test_projects/complex_c_project) 
- 正确识别: 32个自有函数（链表、哈希表、内存池相关）
- 成功排除: 所有标准库函数（atoi, printf, malloc等）

### ⚠️ C++项目问题 (test_projects/complex_example)
- 仍然检测到大量C++标准库函数
- 原因: C++标准库使用 `inline` 关键字，模式不同于Glibc

## 根本问题分析

1. **clang解析特性**: clang看到的是预处理后的代码，包含所有内联定义
2. **C/C++差异**: 
   - C标准库 (Glibc): 使用特殊宏 (`__extern_inline`)
   - C++标准库: 使用普通 `inline` 关键字
3. **过滤挑战**: 需要区分"真正的项目函数"和"内联的标准库函数"

## 待解决的问题

1. **C++标准库过滤**: 需要识别C++标准库的内联模式
2. **启发式规则**: 可能需要基于函数名、文件路径等多重判断
3. **性能考虑**: 大规模项目的过滤效率

## 下一步计划

1. 分析C++标准库函数的具体模式
2. 实现针对C++的过滤规则
3. 测试复杂C++项目的过滤效果
4. 考虑是否需要函数名黑名单作为补充