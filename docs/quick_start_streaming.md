# ai-dt 流式架构快速开始指南

**5分钟上手流式测试生成**

## 🚀 快速体验

### 1. 基本流式模式

```bash
# 最简单的流式模式
python -m src.main --streaming --project /path/to/your/project
```

### 2. 带进度报告

```bash
# 实时查看进度
python -m src.main --streaming --project /path/to/your/project --progress
```

### 3. 高性能模式

```bash
# 大项目使用高并发
python -m src.main --streaming --project /path/to/your/project --max-concurrent 5 --progress
```

## 📊 性能对比

### 架构对比

```bash
# 对比两种架构的性能和兼容性
python -m src.main --compare --project /path/to/your/project --output ./comparison_results
```

### 预期结果

对于大型项目（1000+函数）：

| 指标 | 传统架构 | 流式架构 | 改善幅度 |
|------|----------|----------|----------|
| 首结果时间 | 45分钟 | 30秒 | **98.9%↑** |
| 总处理时间 | 90分钟 | 35分钟 | **61%↑** |
| 内存使用 | 2.5GB | 1.0GB | **60%↓** |

## ⚙️ 简单配置

### 启用流式架构

编辑 `config/test_generation.yaml`：

```yaml
# 添加流式配置
streaming:
  enabled: true  # 启用流式架构

  pipeline:
    max_concurrent_llm_calls: 3  # 并发LLM调用数
    timeout_seconds: 300       # 超时时间
```

### 高性能配置

```yaml
streaming:
  pipeline:
    max_concurrent_files: 5
    max_concurrent_functions: 10
    max_concurrent_llm_calls: 5
    timeout_seconds: 600
```

## 🎯 推荐用法

### 小项目（<50函数）

```bash
python -m src.main --streaming --project ./small_project --max-concurrent 1
```

### 中等项目（50-500函数）

```bash
python -m src.main --streaming --project ./medium_project --max-concurrent 3 --progress
```

### 大型项目（500+函数）

```bash
python -m src.main --streaming --project ./large_project --max-concurrent 5 --progress
```

## 🔍 监控和调试

### 实时进度

```bash
python -m src.main --streaming --project ./project --progress
```

输出示例：
```
Starting streaming test generation for: ./project
First result generated in 12.5s
Progress: 5 completed, throughput: 0.33 packets/sec
Progress: 20 completed, throughput: 0.67 packets/sec
Streaming test generation completed in 180.2s
Results: 48 successful, 2 failed
```

### 错误排查

1. **首结果慢**：降低并发数 `--max-concurrent 1`
2. **内存占用高**：减少队列大小和并发数
3. **API限流**：减少LLM并发调用数

## 📝 示例工作流

### 1. 新项目首次使用

```bash
# 步骤1：运行对比验证兼容性
python -m src.main --compare --project ./new_project

# 步骤2：使用流式模式生成测试
python -m src.main --streaming --project ./new_project --progress

# 步骤3：验证生成结果
ls -la ./experiment/generated_tests/
```

### 2. 现有项目升级

```bash
# 步骤1：在测试环境验证
python -m src.main --compare --project ./existing_project

# 步骤2：并行运行验证
python -m src.main --config existing_project
python -m src.main --streaming --project ./existing_project --output ./streaming_test

# 步骤3：比较结果
diff -r ./experiment/generated_tests/ ./streaming_test/
```

### 3. CI/CD集成

```bash
# CI脚本示例
python -m src.main --streaming --project . --max-concurrent 2 --output ./generated_tests
```

## 🚨 常见问题

### Q: 如何知道流式架构在工作？
A: 使用 `--progress` 参数会显示实时进度。

### Q: 流式架构生成的测试质量和传统一样吗？
A: 使用 `--compare` 模式可以验证兼容性。

### Q: 内存使用过高怎么办？
A: 降低 `--max-concurrent` 参数值。

### Q: 首个结果很慢怎么办？
A: 检查网络连接，降低并发数，或调整API配置。

## 📚 更多资源

- [完整使用指南](./streaming_architecture_guide.md)
- [架构设计文档](./work_logs/20251101_ai-dt_流式架构设计与实现_TDD_CleanCode.md)
- [测试报告](./work_logs/20251101_ai-dt_流式架构测试报告_全面验证.md)

## 🎉 开始使用

现在就开始体验流式架构的强大性能提升吧！

```bash
python -m src.main --streaming --project ./your_project --progress
```

享受从分钟级到秒级的响应速度提升！