"""
Data models for test generation operations
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum


@dataclass
class GenerationTask:
    """Represents a single test generation task"""
    function_info: Dict[str, Any]
    context: Dict[str, Any]
    target_filepath: str
    suite_name: str
    existing_fixture_code: Optional[str] = None
    existing_tests_context: Optional[Dict[str, Any]] = None
    
    @property
    def function_name(self) -> str:
        return self.function_info.get('name', 'unknown')
    
    @property
    def language(self) -> str:
        return self.function_info.get('language', 'c')


@dataclass
class GenerationResult:
    """Represents the result of a test generation task"""
    task: GenerationTask
    success: bool
    test_code: str = ""
    prompt: str = ""
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    model: str = ""
    prompt_length: int = 0
    test_length: int = 0
    output_path: str = ""
    file_info: Optional[Dict[str, Any]] = None
    
    @property
    def function_name(self) -> str:
        return self.task.function_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            'success': self.success,
            'test_code': self.test_code,
            'function_name': self.function_name,
            'prompt': self.prompt,
            'error': self.error,
            'usage': self.usage or {},
            'model': self.model,
            'prompt_length': self.prompt_length,
            'test_length': self.test_length,
            'output_path': self.output_path,
            'file_info': self.file_info
        }


@dataclass
class TestGenerationConfig:
    """Configuration for test generation process"""
    project_name: str
    output_dir: str
    unit_test_directory_path: Optional[str] = None
    max_workers: int = 3
    save_prompts: bool = True
    aggregate_tests: bool = True
    generate_readme: bool = True
    
    # Execution settings
    execution_strategy: str = "concurrent"  # "sequential" or "concurrent"
    delay_between_requests: float = 1.0
    
    # File organization settings
    timestamped_output: bool = True
    separate_debug_files: bool = True


@dataclass
class AggregatedResult:
    """Aggregated results from test generation"""
    config: TestGenerationConfig
    results: List[GenerationResult]
    generation_info: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def successful_count(self) -> int:
        return len([r for r in self.results if r.success])
    
    @property
    def failed_count(self) -> int:
        return len([r for r in self.results if not r.success])
    
    @property
    def total_count(self) -> int:
        return len(self.results)
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.successful_count / self.total_count
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


# ===== 提示词上下文数据模型 =====

class Language(Enum):
    """支持的编程语言"""
    C = "c"
    CPP = "c++"
    
    @property
    def display_name(self) -> str:
        """获取语言的显示名称"""
        return "C++" if self == Language.CPP else "C"


@dataclass
class Parameter:
    """函数参数信息"""
    name: str
    type: str
    default_value: Optional[str] = None


@dataclass
class TargetFunction:
    """被测试的目标函数信息"""
    name: str
    signature: str
    return_type: str
    parameters: List[Parameter]
    body: str
    location: str
    language: Language
    is_static: bool = False
    access_specifier: str = "public"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetFunction':
        """从字典创建TargetFunction实例"""
        language = Language(data.get('language', 'c'))
        parameters = [Parameter(**param) if isinstance(param, dict) else Parameter(name=param.get('name', ''), type=param.get('type', '')) 
                     for param in data.get('parameters', [])]
        
        return cls(
            name=data['name'],
            signature=data['signature'],
            return_type=data['return_type'],
            parameters=parameters,
            body=data['body'],
            location=data['location'],
            language=language,
            is_static=data.get('is_static', False),
            access_specifier=data.get('access_specifier', 'public')
        )


@dataclass
class CalledFunction:
    """被调用的函数信息"""
    name: str
    declaration: str
    is_mockable: bool = True
    location: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalledFunction':
        """从字典创建CalledFunction实例"""
        return cls(
            name=data['name'],
            declaration=data['declaration'],
            is_mockable=data.get('is_mockable', True),
            location=data.get('location')
        )


@dataclass
class MacroDefinition:
    """宏定义信息"""
    name: str
    definition: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroDefinition':
        """从字典创建MacroDefinition实例"""
        return cls(
            name=data['name'],
            definition=data.get('definition', '')
        )


@dataclass
class Dependencies:
    """依赖项信息"""
    called_functions: List[CalledFunction] = field(default_factory=list)
    macros: List[str] = field(default_factory=list)
    macro_definitions: List[MacroDefinition] = field(default_factory=list)
    data_structures: List[str] = field(default_factory=list)
    dependency_definitions: List[str] = field(default_factory=list)
    
    @property
    def has_external_dependencies(self) -> bool:
        """检查是否有外部依赖"""
        return bool(self.called_functions)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dependencies':
        """从字典创建Dependencies实例"""
        called_functions = [CalledFunction.from_dict(func) if isinstance(func, dict) else func 
                           for func in data.get('called_functions', [])]
        macro_definitions = [MacroDefinition.from_dict(macro) if isinstance(macro, dict) else macro 
                            for macro in data.get('macro_definitions', [])]
        
        return cls(
            called_functions=called_functions,
            macros=data.get('macros', []),
            macro_definitions=macro_definitions,
            data_structures=data.get('data_structures', []),
            dependency_definitions=data.get('dependency_definitions', [])
        )


@dataclass
class UsagePattern:
    """函数使用模式信息"""
    file: str
    line: int
    context_preview: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsagePattern':
        """从字典创建UsagePattern实例"""
        return cls(
            file=data['file'],
            line=data['line'],
            context_preview=data['context_preview']
        )


@dataclass
class CompilationInfo:
    """编译信息"""
    include_paths: List[str] = field(default_factory=list)
    defines: List[str] = field(default_factory=list)
    compiler_flags: List[str] = field(default_factory=list)
    key_flags: List[str] = field(default_factory=list)
    total_flags_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompilationInfo':
        """从字典创建CompilationInfo实例"""
        return cls(
            include_paths=data.get('include_paths', []),
            defines=data.get('defines', []),
            compiler_flags=data.get('compiler_flags', []),
            key_flags=data.get('key_flags', []),
            total_flags_count=data.get('total_flags_count', 0)
        )


@dataclass
class TestFunction:
    """现有测试函数信息"""
    name: str
    target_function: str
    code: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestFunction':
        """从字典创建TestFunction实例"""
        return cls(
            name=data['name'],
            target_function=data.get('target_function', '未知'),
            code=data.get('code')
        )


@dataclass
class TestClass:
    """现有测试类信息"""
    name: str
    definition: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestClass':
        """从字典创建TestClass实例"""
        return cls(
            name=data['name'],
            definition=data['definition']
        )


@dataclass
class ExistingTestsContext:
    """现有测试上下文信息"""
    matched_test_files: List[str] = field(default_factory=list)
    existing_test_functions: List[TestFunction] = field(default_factory=list)
    existing_test_classes: List[TestClass] = field(default_factory=list)
    test_coverage_summary: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExistingTestsContext':
        """从字典创建ExistingTestsContext实例"""
        if not data:
            return cls()
            
        test_functions = [TestFunction.from_dict(func) if isinstance(func, dict) else func 
                         for func in data.get('existing_test_functions', [])]
        test_classes = [TestClass.from_dict(cls_data) if isinstance(cls_data, dict) else cls_data 
                       for cls_data in data.get('existing_test_classes', [])]
        
        return cls(
            matched_test_files=data.get('matched_test_files', []),
            existing_test_functions=test_functions,
            existing_test_classes=test_classes,
            test_coverage_summary=data.get('test_coverage_summary')
        )


@dataclass
class PromptContext:
    """提示词生成的完整上下文信息"""
    target_function: TargetFunction
    dependencies: Dependencies
    usage_patterns: List[UsagePattern] = field(default_factory=list)
    compilation_info: Optional[CompilationInfo] = None
    existing_tests_context: Optional[ExistingTestsContext] = None
    existing_fixture_code: Optional[str] = None
    suite_name: Optional[str] = None
    
    @classmethod
    def from_compressed_context(cls, compressed_context: Dict[str, Any], 
                               existing_fixture_code: Optional[str] = None,
                               suite_name: Optional[str] = None,
                               existing_tests_context: Optional[Dict[str, Any]] = None) -> 'PromptContext':
        """从压缩的上下文字典创建PromptContext实例"""
        target_function = TargetFunction.from_dict(compressed_context['target_function'])
        dependencies = Dependencies.from_dict(compressed_context['dependencies'])
        
        usage_patterns = [UsagePattern.from_dict(pattern) if isinstance(pattern, dict) else pattern 
                         for pattern in compressed_context.get('usage_patterns', [])]
        
        compilation_info = None
        if 'compilation_info' in compressed_context:
            compilation_info = CompilationInfo.from_dict(compressed_context['compilation_info'])
        
        existing_tests = None
        if existing_tests_context:
            existing_tests = ExistingTestsContext.from_dict(existing_tests_context)
        
        return cls(
            target_function=target_function,
            dependencies=dependencies,
            usage_patterns=usage_patterns,
            compilation_info=compilation_info,
            existing_tests_context=existing_tests,
            existing_fixture_code=existing_fixture_code,
            suite_name=suite_name
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于向后兼容"""
        result = {
            'target_function': {
                'name': self.target_function.name,
                'signature': self.target_function.signature,
                'return_type': self.target_function.return_type,
                'parameters': [{'name': p.name, 'type': p.type, 'default_value': p.default_value} 
                              for p in self.target_function.parameters],
                'body': self.target_function.body,
                'location': self.target_function.location,
                'language': self.target_function.language.value,
                'is_static': self.target_function.is_static,
                'access_specifier': self.target_function.access_specifier
            },
            'dependencies': {
                'called_functions': [{
                    'name': func.name,
                    'declaration': func.declaration,
                    'is_mockable': func.is_mockable,
                    'location': func.location
                } for func in self.dependencies.called_functions],
                'macros': self.dependencies.macros,
                'macro_definitions': [{
                    'name': macro.name,
                    'definition': macro.definition
                } for macro in self.dependencies.macro_definitions],
                'data_structures': self.dependencies.data_structures,
                'dependency_definitions': self.dependencies.dependency_definitions
            },
            'usage_patterns': [{
                'file': pattern.file,
                'line': pattern.line,
                'context_preview': pattern.context_preview
            } for pattern in self.usage_patterns]
        }
        
        if self.compilation_info:
            result['compilation_info'] = {
                'include_paths': self.compilation_info.include_paths,
                'defines': self.compilation_info.defines,
                'compiler_flags': self.compilation_info.compiler_flags,
                'key_flags': self.compilation_info.key_flags,
                'total_flags_count': self.compilation_info.total_flags_count
            }
        
        return result
    
    @property
    def language_display(self) -> str:
        """获取语言的显示名称"""
        return self.target_function.language.display_name
    
    @property
    def has_external_dependencies(self) -> bool:
        """检查是否有外部依赖"""
        return self.dependencies.has_external_dependencies