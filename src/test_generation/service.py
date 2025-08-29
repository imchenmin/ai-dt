"""
Test generation service - provides a high-level interface with backward compatibility
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import TestGenerationConfig, AggregatedResult
from .orchestrator import TestGenerationOrchestrator
from .components import ComponentFactory
from .strategies import ExecutionStrategyFactory
from src.llm.client import LLMClient
from src.llm.models import LLMConfig
from src.llm.factory import LLMProviderFactory
from src.utils.config_loader import ConfigLoader
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class TestGenerationService:
    """
    High-level service for test generation with backward compatibility
    
    This service provides a clean interface while using the new modular architecture
    internally. It maintains compatibility with the existing API.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize service with optional LLM client"""
        self.llm_client = llm_client
        self.orchestrator: Optional[TestGenerationOrchestrator] = None
    
    def generate_tests(self, functions_with_context: List[Dict[str, Any]], 
                      project_config: Dict[str, Any],
                      max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        Generate tests with backward compatible API
        
        Args:
            functions_with_context: List of function data with context
            project_config: Project configuration dictionary
            max_workers: Number of concurrent workers
            
        Returns:
            List of result dictionaries for backward compatibility
        """
        # Convert to new configuration format
        config = self._convert_project_config(project_config, max_workers)
        
        # Setup LLM client if not provided
        if not self.llm_client:
            self.llm_client = self._create_llm_client(project_config)
        
        # Create orchestrator
        self.orchestrator = TestGenerationOrchestrator(
            llm_client=self.llm_client,
            execution_strategy=ExecutionStrategyFactory.create_strategy(
                config.execution_strategy,
                max_workers=config.max_workers,
                delay_between_requests=config.delay_between_requests
            )
        )
        
        # Generate tests
        aggregated = self.orchestrator.generate_tests(functions_with_context, config)
        
        # Convert back to backward compatible format
        return [result.to_dict() for result in aggregated.results]
    
    def generate_tests_new_api(self, functions_with_context: List[Dict[str, Any]], 
                              config: TestGenerationConfig,
                              llm_config: Optional[LLMConfig] = None) -> AggregatedResult:
        """
        Generate tests using new API
        
        Args:
            functions_with_context: List of function data with context
            config: Test generation configuration
            llm_config: LLM configuration (optional)
            
        Returns:
            Aggregated results object
        """
        # Setup LLM client if not provided
        if not self.llm_client:
            if llm_config:
                self.llm_client = LLMClient.create_from_config(llm_config)
            else:
                raise ValueError("Either llm_client or llm_config must be provided")
        
        # Create orchestrator
        self.orchestrator = TestGenerationOrchestrator(
            llm_client=self.llm_client,
            execution_strategy=ExecutionStrategyFactory.create_strategy(
                config.execution_strategy,
                max_workers=config.max_workers,
                delay_between_requests=config.delay_between_requests
            )
        )
        
        # Generate tests
        return self.orchestrator.generate_tests(functions_with_context, config)
    
    def create_config_from_dict(self, project_config: Dict[str, Any], 
                               max_workers: int = 3) -> TestGenerationConfig:
        """Create TestGenerationConfig from dictionary"""
        return self._convert_project_config(project_config, max_workers)
    
    def create_llm_config_from_dict(self, project_config: Dict[str, Any]) -> LLMConfig:
        """Create LLMConfig from dictionary"""
        return self._create_llm_config(project_config)
    
    def _convert_project_config(self, project_config: Dict[str, Any], 
                               max_workers: int) -> TestGenerationConfig:
        """Convert old project config to new TestGenerationConfig"""
        project_name = project_config.get("name", "unknown_project")
        output_dir = project_config.get("output_dir", "./generated_tests")
        
        # Generate timestamped output directory if needed
        if not project_config.get("output_dir_ready", False):
            project_path = project_config.get('path', project_name)
            project_name = Path(project_path).name
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = str(Path(output_dir) / f"{project_name}_{timestamp}")
        
        return TestGenerationConfig(
            project_name=project_name,
            output_dir=output_dir,
            unit_test_directory_path=project_config.get("unit_test_directory_path"),
            max_workers=max_workers,
            execution_strategy="concurrent" if max_workers > 1 else "sequential",
            delay_between_requests=1.0,
            save_prompts=True,
            aggregate_tests=True,
            generate_readme=True,
            timestamped_output=False  # Already handled above
        )
    
    def _create_llm_client(self, project_config: Dict[str, Any]) -> LLMClient:
        """Create LLM client from project config"""
        llm_provider = project_config.get('llm_provider', 'deepseek')
        model = project_config.get('model', 'deepseek-coder')
        
        # Check if this is prompt-only mode
        prompt_only = project_config.get('prompt_only', False)
        if prompt_only:
            return LLMClient.create_mock_client(model)
        
        # Get API key
        api_key = ConfigLoader.get_api_key(llm_provider)
        if not api_key:
            logger.error(f"{llm_provider.upper()} API key not found.")
            llm_config = ConfigLoader.get_llm_config(llm_provider)
            logger.info(f"Please set {llm_config['api_key_env']} environment variable.")
            # Return mock client for graceful fallback
            return LLMClient.create_mock_client(model)
        
        # Create LLM configuration
        llm_config = self._create_llm_config(project_config)
        
        # Create client
        return LLMClient.create_from_config(llm_config)
    
    def _create_llm_config(self, project_config: Dict[str, Any]) -> LLMConfig:
        """Create LLM config from project configuration"""
        llm_provider = project_config.get('llm_provider', 'deepseek')
        model = project_config.get('model', 'deepseek-coder')
        
        # Set default models based on provider
        if model == 'deepseek-coder' and llm_provider != 'deepseek':
            if llm_provider == 'openai':
                model = 'gpt-3.5-turbo'
            elif llm_provider == 'dify':
                model = 'dify_model'
        
        # Get error handling configuration
        error_config = project_config.get('error_handling', {})
        
        return LLMConfig(
            provider_name=llm_provider,
            api_key=ConfigLoader.get_api_key(llm_provider),
            model=model,
            max_retries=error_config.get('max_retries', 3),
            retry_delay=error_config.get('retry_delay', 1.0),
            retry_enabled=True,
            logging_enabled=True
        )
    
    def get_summary_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate summary report from results (backward compatible)"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        report = [
            "=== Test Generation Summary ===",
            f"Total functions processed: {len(results)}",
            f"Successful generations: {len(successful)}",
            f"Failed generations: {len(failed)}",
        ]
        
        if failed:
            report.append("\nFailed functions:")
            for result in failed:
                report.append(f"  • {result['function_name']}: {result.get('error', 'Unknown error')}")
        
        return '\n'.join(report)
    
    def set_llm_client(self, llm_client: LLMClient) -> None:
        """Set LLM client for dependency injection"""
        self.llm_client = llm_client
        if self.orchestrator:
            self.orchestrator.set_llm_client(llm_client)
    
    @classmethod
    def create_for_testing(cls, llm_client: Optional[LLMClient] = None) -> 'TestGenerationService':
        """Create service instance for testing"""
        if not llm_client:
            llm_client = LLMClient.create_mock_client()
        return cls(llm_client)