# 代码组织指南

## 目录结构说明

### 当前结构
```
ai-dt/
├── src/
│   ├── core/
│   │   └── streaming/          # 流式架构核心实现
│   │       ├── interfaces.py   # 接口定义
│   │       ├── streaming_service.py
│   │       ├── pipeline_orchestrator.py
│   │       └── [processors]
│   ├── modes/                  # 命令模式处理器 (新增)
│   │   ├── __init__.py
│   │   ├── streaming_mode.py   # 流式模式处理
│   │   └── comparison_mode.py  # 对比模式处理
│   ├── llm/                    # LLM客户端
│   ├── parser/                 # 代码解析器
│   ├── test_generation/        # 测试生成器
│   ├── api/                    # API服务器
│   └── utils/                  # 工具类
│       ├── retry_utils.py      # 重试工具 (新增)
│       └── ...
├── tests/
│   └── core/
│       └── streaming/          # 流式架构测试
├── config/                     # 配置文件
├── docs/                       # 文档
└── test_projects/              # 测试项目
```

### 建议的优化结构
```
ai-dt/
├── src/
│   ├── core/
│   │   ├── streaming/          # 流式架构
│   │   │   ├── interfaces/     # 接口定义
│   │   │   │   ├── __init__.py
│   │   │   │   ├── packets.py  # 数据包定义
│   │   │   │   ├── processors.py # 处理器接口
│   │   │   │   └── observers.py # 观察者接口
│   │   │   ├── processors/     # 处理器实现
│   │   │   │   ├── __init__.py
│   │   │   │   ├── file_discoverer.py
│   │   │   │   ├── function_processor.py
│   │   │   │   ├── llm_processor.py
│   │   │   │   └── result_collector.py
│   │   │   ├── queues/         # 队列实现
│   │   │   │   ├── __init__.py
│   │   │   │   ├── async_queue.py
│   │   │   │   └── priority_queue.py
│   │   │   ├── orchestrators/  # 协调器
│   │   │   │   ├── __init__.py
│   │   │   │   └── pipeline_orchestrator.py
│   │   │   ├── services/       # 服务层
│   │   │   │   ├── __init__.py
│   │   │   │   └── streaming_service.py
│   │   │   ├── adapters/       # 适配器
│   │   │   │   ├── __init__.py
│   │   │   │   └── migration_adapter.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── modes/                  # 命令模式
│   │   ├── __init__.py
│   │   ├── base.py            # 基础模式类
│   │   ├── streaming.py       # 流式模式
│   │   ├── comparison.py      # 对比模式
│   │   └── legacy.py          # 传统模式
│   ├── llm/                    # LLM集成
│   │   ├── clients/           # 客户端实现
│   │   ├── providers/         # 提供商适配
│   │   └── prompts/           # 提示词模板
│   ├── parsing/               # 代码解析
│   │   ├── clang/             # Clang解析器
│   │   ├── tree_sitter/       # Tree-sitter解析器
│   │   └── models/            # 数据模型
│   ├── generation/            # 测试生成
│   │   ├── strategies/        # 生成策略
│   │   ├── templates/         # 模板管理
│   │   └── validators/        # 验证器
│   ├── api/                   # API层
│   │   ├── routes/            # 路由定义
│   │   ├── middleware/        # 中间件
│   │   └── schemas/           # 数据模式
│   ├── utils/                 # 工具类
│   │   ├── retry/             # 重试机制
│   │   ├── logging/           # 日志工具
│   │   ├── config/            # 配置管理
│   │   └── monitoring/        # 监控工具
│   └── __init__.py
```

## 组织原则

### 1. 单一职责原则
- 每个模块只负责一个功能领域
- 每个类只有一个改变的理由

### 2. 依赖倒置原则
- 高层模块不依赖低层模块
- 都依赖于抽象接口

### 3. 开闭原则
- 对扩展开放，对修改关闭
- 使用策略模式和工厂模式

### 4. 接口隔离原则
- 接口应该小而专注
- 客户端不应该依赖它不需要的接口

## 代码迁移建议

### 阶段1：重组streaming模块
1. 创建子目录结构
2. 拆分interfaces.py到多个文件
3. 将处理器移到processors目录
4. 更新导入语句

### 阶段2：优化modes模块
1. 创建基础模式类
2. 实现统一的模式接口
3. 添加配置验证

### 阶段3：重构utils模块
1. 按功能分组工具类
2. 创建子包
3. 统一异常处理

### 阶段4：改进LLM模块
1. 分离客户端和提供商
2. 独立提示词管理
3. 添加缓存层

## 导入约定

### 推荐的导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地应用导入（按层级）
4. 相对导入

### 导入示例
```python
# Standard library
import asyncio
import time
from typing import List, Optional

# Third-party
import yaml
from pydantic import BaseModel

# Local application
from src.core.streaming.interfaces import StreamPacket
from src.core.streaming.processors.file_discoverer import FileDiscoverer
from src.utils.retry import retry
```

## 命名约定

### 目录和文件
- 使用小写字母和下划线
- 包名使用简短、描述性的名称
- 模块名应该反映其功能

### 类和函数
- 类使用PascalCase
- 函数和变量使用snake_case
- 私有成员使用前缀下划线

### 常量
- 使用大写字母和下划线
- 在模块级别定义
- 使用类型注解

## 测试组织

### 测试目录结构
```
tests/
├── unit/                   # 单元测试
│   ├── core/
│   │   └── streaming/
│   ├── modes/
│   └── utils/
├── integration/            # 集成测试
│   ├── api/
│   └── pipelines/
├── e2e/                   # 端到端测试
├── performance/           # 性能测试
└── fixtures/              # 测试数据
```

### 测试命名
- 测试文件：test_*.py
- 测试类：Test*
- 测试方法：test_*
- 使用描述性的测试名称

## 文档组织

### 文档类型
1. **API文档**：自动生成的接口文档
2. **架构文档**：系统设计和架构说明
3. **指南文档**：如何使用和扩展
4. **工作日志**：开发过程记录

### 文档位置
- `/docs/`：用户文档和架构文档
- `/docs/work_logs/`：开发日志
- 代码内：docstring和注释

## 性能考虑

### 模块加载
- 使用延迟加载大型模块
- 避免循环导入
- 合理使用__all__

### 内存管理
- 及时释放大型对象
- 使用弱引用避免循环引用
- 监控内存使用

## 安全考虑

### 敏感信息
- 使用环境变量
- 不在代码中硬编码密钥
- 使用配置管理工具

### 输入验证
- 在边界层验证输入
- 使用类型检查
- 防止注入攻击