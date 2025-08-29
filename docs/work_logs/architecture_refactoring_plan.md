# LLM Client & Test Generator 架构重构计划

## 重构目标
- 提高代码可维护性和可扩展性
- 实现更好的关注点分离
- 增强代码可读性
- 采用SOLID设计原则

## 当前问题分析

### LLM Client 问题
1. **单一职责违背**: 一个类处理多个提供商的API调用、错误处理、重试逻辑
2. **开闭原则违背**: 添加新提供商需要修改现有代码
3. **依赖倒置违背**: 直接依赖具体的HTTP客户端实现
4. **错误处理分散**: 每个方法都有自己的错误处理逻辑

### Test Generator 问题
1. **单一职责违背**: 包含测试生成、文件组织、并发处理、统计报告
2. **依赖过多**: 直接依赖多个具体实现类
3. **复杂度过高**: `generate_tests`方法过于复杂
4. **可测试性差**: 紧耦合使得单元测试困难

## 改进架构设计

### 1. LLM Client 重构架构

#### 核心抽象层
```python
# 抽象基类
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        pass

# 值对象
@dataclass
class GenerationRequest:
    prompt: str
    max_tokens: int
    temperature: float
    language: str
    system_prompt: str

@dataclass  
class GenerationResponse:
    success: bool
    content: str
    usage: TokenUsage
    model: str
    error: Optional[str] = None
```

#### 提供商实现层
```python
class OpenAIProvider(LLMProvider):
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # OpenAI特定实现

class DeepSeekProvider(LLMProvider):
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # DeepSeek特定实现

class DifyProvider(LLMProvider):
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # Dify特定实现
```

#### 装饰器模式增强功能
```python
class RetryDecorator(LLMProvider):
    def __init__(self, provider: LLMProvider, max_retries: int = 3):
        self.provider = provider
        self.max_retries = max_retries
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # 重试逻辑

class RateLimitDecorator(LLMProvider):
    def __init__(self, provider: LLMProvider, rate_limit: float):
        self.provider = provider
        self.rate_limit = rate_limit
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # 速率限制逻辑
```

#### 工厂模式创建客户端
```python
class LLMProviderFactory:
    @staticmethod
    def create_provider(config: LLMConfig) -> LLMProvider:
        base_provider = LLMProviderFactory._create_base_provider(config)
        
        # 应用装饰器
        if config.retry_enabled:
            base_provider = RetryDecorator(base_provider, config.max_retries)
        
        if config.rate_limit_enabled:
            base_provider = RateLimitDecorator(base_provider, config.rate_limit)
            
        return base_provider
```

### 2. Test Generator 重构架构

#### 核心服务层
```python
class TestGenerationOrchestrator:
    """测试生成编排器 - 负责协调整个测试生成流程"""
    
    def __init__(self, 
                 prompt_generator: PromptGenerator,
                 test_generator: CoreTestGenerator,
                 file_organizer: TestFileOrganizer,
                 execution_strategy: ExecutionStrategy):
        self.prompt_generator = prompt_generator
        self.test_generator = test_generator
        self.file_organizer = file_organizer
        self.execution_strategy = execution_strategy
```

#### 策略模式处理执行
```python
class ExecutionStrategy(ABC):
    @abstractmethod
    def execute(self, tasks: List[GenerationTask]) -> List[GenerationResult]:
        pass

class SequentialExecution(ExecutionStrategy):
    def execute(self, tasks: List[GenerationTask]) -> List[GenerationResult]:
        # 顺序执行逻辑

class ConcurrentExecution(ExecutionStrategy):
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
    
    def execute(self, tasks: List[GenerationTask]) -> List[GenerationResult]:
        # 并发执行逻辑
```

#### 职责分离的组件
```python
class PromptGenerator:
    """专门负责生成提示的组件"""
    def generate_prompt(self, function_context: FunctionContext) -> Prompt:
        pass

class CoreTestGenerator:
    """核心测试生成器 - 只负责调用LLM生成测试"""
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    def generate_test(self, prompt: Prompt) -> TestCode:
        pass

class TestResultAggregator:
    """测试结果聚合器"""
    def aggregate_results(self, results: List[GenerationResult]) -> AggregatedResult:
        pass
```

## 重构步骤

### 第一阶段：LLM Client 重构
1. 创建抽象层和值对象
2. 实现具体提供商类
3. 添加装饰器增强功能
4. 创建工厂类
5. 更新测试

### 第二阶段：Test Generator 重构  
1. 创建编排器和策略接口
2. 分离核心组件
3. 实现执行策略
4. 重构主要流程
5. 更新依赖注入

### 第三阶段：集成和验证
1. 更新所有依赖模块
2. 运行完整测试套件
3. 性能验证
4. 文档更新

## 期望收益

### 可维护性提升
- 每个类职责单一，修改影响范围小
- 依赖清晰，便于理解和修改

### 可扩展性提升
- 新增LLM提供商只需实现接口
- 新增执行策略不影响现有代码
- 装饰器模式灵活组合功能

### 可测试性提升
- 依赖注入便于mock
- 小粒度组件便于单元测试
- 策略模式便于测试不同场景

### 代码可读性提升
- 意图明确的类名和方法名
- 职责清晰的组件划分
- 统一的抽象层次