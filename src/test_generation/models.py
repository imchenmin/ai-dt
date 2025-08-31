"""
Data models for test generation operations
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


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