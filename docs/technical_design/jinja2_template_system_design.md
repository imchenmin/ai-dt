# Jinja2模板系统重构设计文档

## 1. 当前问题分析

### 1.1 硬编码问题识别

当前提示词模板系统存在以下硬编码问题：

1. **逻辑硬编码在Python代码中**：
   - `PromptTemplates._prepare_section_variables()` 中包含大量条件判断逻辑
   - 各种section的构建逻辑分散在多个静态方法中
   - 模板选择逻辑硬编码在 `_select_template()` 方法中

2. **模板文件缺乏逻辑能力**：
   - 当前模板文件只是简单的字符串替换
   - 无法在模板中进行条件判断和循环
   - 无法实现复杂的数据处理逻辑

3. **配置系统不完整**：
   - 模板选择完全由代码控制
   - 缺乏灵活的模板配置机制
   - 无法通过配置文件控制模板行为

### 1.2 具体硬编码示例

```python
# 当前硬编码逻辑示例
if ctx.dependencies.dependency_definitions:
    sections['dependency_definitions_section'] = PromptTemplates._build_dependency_definitions_section(ctx)
else:
    sections['dependency_definitions_section'] = ""

if ctx.has_external_dependencies:
    sections['dependency_analysis_section'] = PromptTemplates._build_dependency_analysis_section(ctx)
else:
    sections['dependency_analysis_section'] = ""
```

## 2. Jinja2模板系统设计

### 2.1 设计原则

1. **逻辑分离**：将所有条件判断和循环逻辑移到Jinja2模板中
2. **配置驱动**：通过配置文件控制模板选择和行为
3. **向后兼容**：保持现有API接口不变
4. **可扩展性**：支持新语言和新模板类型的轻松添加

### 2.2 新架构设计

```
templates/
├── prompts/
│   ├── jinja2/                    # 新的Jinja2模板目录
│   │   ├── base/                  # 基础模板
│   │   │   ├── test_generation.j2 # 主测试生成模板
│   │   │   ├── sections/          # 模板片段
│   │   │   │   ├── dependencies.j2
│   │   │   │   ├── existing_tests.j2
│   │   │   │   ├── mock_guidance.j2
│   │   │   │   └── test_structure.j2
│   │   │   └── macros/            # 可复用宏
│   │   │       ├── code_block.j2
│   │   │       └── test_naming.j2
│   │   ├── c/                     # C语言特定模板
│   │   │   └── test_generation.j2
│   │   ├── cpp/                   # C++语言特定模板
│   │   │   └── test_generation.j2
│   │   └── java/                  # Java语言特定模板
│   │       └── test_generation.j2
config/
├── template_config.yaml           # 新的模板配置文件
└── test_generation.yaml           # 扩展现有配置
```

### 2.3 模板配置系统

```yaml
# config/template_config.yaml
template_engine: "jinja2"

template_sets:
  default:
    base_template: "base/test_generation.j2"
    language_overrides:
      c: "c/test_generation.j2"
      cpp: "cpp/test_generation.j2"
      java: "java/test_generation.j2"
  
  minimal:
    base_template: "base/minimal_test.j2"
    
  comprehensive:
    base_template: "base/comprehensive_test.j2"

default_template_set: "default"

# 模板变量配置
template_variables:
  show_memory_guidance: true
  include_mock_examples: true
  max_dependency_definitions: 10
  
# 条件渲染配置
conditional_sections:
  dependency_definitions:
    enabled: true
    min_dependencies: 1
  mock_guidance:
    enabled: true
    languages: ["c", "cpp"]
  existing_tests:
    enabled: true
    show_full_code: false
```

## 3. 实现计划

### 3.1 阶段一：基础设施

1. 安装Jinja2依赖
2. 创建新的模板目录结构
3. 重构PromptTemplateLoader支持Jinja2
4. 创建模板配置系统

### 3.2 阶段二：模板迁移

1. 将现有模板转换为Jinja2格式
2. 将Python中的逻辑移到模板中
3. 创建可复用的模板宏和片段
4. 实现语言特定的模板继承

### 3.3 阶段三：集成测试

1. 重构PromptTemplates类
2. 更新配置文件
3. 创建全面的测试用例
4. 性能测试和优化

## 4. 关键技术实现

### 4.1 Jinja2模板示例

```jinja2
{# templates/prompts/jinja2/base/test_generation.j2 #}
# 1. 角色与目标 (Role & Goal)
你是一位精通{{ language_display }}和Google Test框架的资深软件测试工程师。
你的核心任务是为下方指定的函数，生成一个完整、正确且健壮的Google Test单元测试文件。

# 2. 被测函数 (Function Under Test - FUT)
*   **文件路径:** `{{ target_function.location }}`
*   **函数签名:** `{{ target_function.signature }}`
*   **函数体:**
    ```{{ language_lower }}
{{ target_function.body | indent(4, true) }}
    ```

# 3. 上下文与依赖 (Context & Dependencies)
{% include 'sections/dependencies.j2' %}
{% include 'sections/existing_tests.j2' %}

# 4. 测试生成要求 (Test Generation Requirements)
1.  **测试框架:** 必须使用 **Google Test** (`gtest`).
{% include 'sections/mock_guidance.j2' %}
{% include 'sections/test_structure.j2' %}
```

### 4.2 条件渲染示例

```jinja2
{# sections/dependencies.j2 #}
{% if dependencies.dependency_definitions %}
## 依赖定义 (Dependency Definitions)
{% for definition in dependencies.dependency_definitions %}
```{{ language_lower }}
{{ definition }}
```
{% endfor %}
{% endif %}

{% if dependencies.macro_definitions %}
## 宏定义 (Macro Definitions)
{{ dependencies.macro_definitions }}
{% endif %}
```

### 4.3 新的PromptTemplateLoader接口

```python
class PromptTemplateLoader:
    def __init__(self, config_path: str = None):
        self.config = self._load_template_config(config_path)
        self.jinja_env = self._setup_jinja_environment()
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """使用Jinja2渲染模板"""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
    
    def get_template_for_language(self, language: str, template_set: str = None) -> str:
        """根据语言和模板集获取模板名称"""
        template_set = template_set or self.config['default_template_set']
        templates = self.config['template_sets'][template_set]
        
        # 检查语言特定覆盖
        if language in templates.get('language_overrides', {}):
            return templates['language_overrides'][language]
        
        return templates['base_template']
```

## 5. 验证策略

### 5.1 测试用例设计

1. **模板渲染测试**：验证Jinja2模板正确渲染
2. **逻辑迁移测试**：确保迁移后的逻辑与原有逻辑一致
3. **配置驱动测试**：验证配置文件正确控制模板行为
4. **多语言支持测试**：测试C/C++/Java模板
5. **性能测试**：确保新系统性能不低于原系统

### 5.2 回归测试

1. 运行现有的所有测试用例
2. 对比新旧系统生成的提示词
3. 验证生成的测试代码质量

## 6. 迁移策略

### 6.1 渐进式迁移

1. 保留原有系统作为fallback
2. 通过配置开关控制使用新旧系统
3. 逐步迁移各个模板
4. 最终移除旧系统

### 6.2 兼容性保证

1. 保持现有API接口不变
2. 支持新旧配置格式
3. 提供迁移工具和文档

## 7. 预期收益

1. **可维护性提升**：逻辑集中在模板中，易于修改
2. **可扩展性增强**：新增语言和模板类型更容易
3. **配置灵活性**：通过配置文件控制模板行为
4. **代码质量**：减少Python代码中的硬编码逻辑
5. **团队协作**：非程序员也可以修改模板逻辑