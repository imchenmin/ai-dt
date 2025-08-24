"""
File organization utilities for test generation output
"""

from pathlib import Path
from typing import Dict, Optional, Any
import re


class TestFileOrganizer:
    """Organizes test generation output into structured subdirectories"""
    
    def __init__(self, base_output_dir: str):
        self.base_dir = Path(base_output_dir)
        
    def organize_test_output(self, test_code: str, function_name: str, 
                           prompt: Optional[str] = None, 
                           raw_response: Optional[str] = None) -> Dict[str, str]:
        """
        Organize test generation output into three subdirectories:
        1. prompts/ - Input prompts to LLM
        2. raw_responses/ - Raw LLM responses
        3. pure_tests/ - Extracted pure test code
        """
        # Create the three subdirectories
        prompts_dir = self.base_dir / "1_prompts"
        responses_dir = self.base_dir / "2_raw_responses"
        tests_dir = self.base_dir / "3_pure_tests"
        
        for directory in [prompts_dir, responses_dir, tests_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Save prompt if provided
        prompt_path = None
        if prompt:
            prompt_path = prompts_dir / f"prompt_{function_name}.txt"
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
        
        # Save raw response if provided
        response_path = None
        if raw_response:
            response_path = responses_dir / f"response_{function_name}.txt"
            with open(response_path, 'w', encoding='utf-8') as f:
                f.write(raw_response)
        
        # Extract pure test code (content between ```cpp and ```)
        pure_test_code = self._extract_pure_test_code(test_code)
        
        # Save pure test code
        test_path = tests_dir / f"test_{function_name}.cpp"
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(pure_test_code)
        
        return {
            'prompt_path': str(prompt_path) if prompt_path else None,
            'response_path': str(response_path) if response_path else None,
            'test_path': str(test_path),
            'pure_test_code': pure_test_code
        }
    
    def save_prompt_only(self, function_name: str, prompt: str) -> str:
        """Save only the prompt without waiting for test generation"""
        prompts_dir = self.base_dir / "1_prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        prompt_path = prompts_dir / f"prompt_{function_name}.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return str(prompt_path)
    
    def _extract_pure_test_code(self, test_code: str) -> str:
        """Extract only the C++ code between ```cpp and ``` markers"""
        if '```cpp' in test_code and '```' in test_code:
            # Find the start and end of the code block
            start_idx = test_code.find('```cpp') + len('```cpp')
            end_idx = test_code.find('```', start_idx)
            
            if start_idx != -1 and end_idx != -1:
                pure_code = test_code[start_idx:end_idx].strip()
                # Remove any leading/trailing whitespace and newlines
                return pure_code.strip()
        
        # If no code blocks found, return the original code
        return test_code.strip()
    
    def create_timestamped_directory(self, project_name: str) -> str:
        """Create a timestamped directory for test generation"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{project_name}_{timestamp}"
        timestamped_dir = self.base_dir / dir_name
        timestamped_dir.mkdir(parents=True, exist_ok=True)
        
        return str(timestamped_dir)
    
    def generate_readme(self, generation_info: Dict[str, Any]) -> str:
        """Generate a README file with generation metadata"""
        readme_path = self.base_dir / "README.md"
        
        readme_content = f"""# Test Generation Results

## Generation Information
- **Timestamp**: {generation_info.get('timestamp', 'Unknown')}
- **Project**: {generation_info.get('project_name', 'Unknown')}
- **LLM Provider**: {generation_info.get('llm_provider', 'Unknown')}
- **Model**: {generation_info.get('model', 'Unknown')}
- **Total Functions**: {generation_info.get('total_functions', 0)}
- **Successful**: {generation_info.get('successful', 0)}
- **Failed**: {generation_info.get('failed', 0)}

## Directory Structure
- `1_prompts/`: Input prompts sent to the LLM
- `2_raw_responses/`: Raw responses from the LLM
- `3_pure_tests/`: Extracted pure C++ test code

## Usage Notes
Generated tests use Google Test framework with MockCpp for mocking.
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return str(readme_path)