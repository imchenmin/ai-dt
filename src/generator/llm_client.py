"""
LLM client for generating test cases using various AI providers
"""

import json
import requests
import openai
from typing import Dict, Any, Optional
import time
from pathlib import Path
from openai import OpenAI


class LLMClient:
    """Client for interacting with various LLM providers"""
    
    def __init__(self, provider: str = "openai", api_key: str = None, 
                 base_url: str = None, model: str = "gpt-3.5-turbo"):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate client based on provider"""
        if self.provider == "openai":
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else "https://api.openai.com/v1"
            )
        
        elif self.provider == "deepseek":
            # DeepSeek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else "https://api.deepseek.com/v1"
            )
        
        elif self.provider == "anthropic":
            # Anthropic client setup would go here
            self.client = None
        
        elif self.provider == "local":
            # Local model setup
            self.client = None
    
    def generate_test(self, prompt: str, max_tokens: int = 2000, 
                     temperature: float = 0.3) -> Dict[str, Any]:
        """Generate test code using LLM"""
        try:
            if self.provider == "openai":
                return self._generate_with_openai(prompt, max_tokens, temperature)
            elif self.provider == "deepseek":
                return self._generate_with_deepseek(prompt, max_tokens, temperature)
            elif self.provider == "anthropic":
                return self._generate_with_anthropic(prompt, max_tokens, temperature)
            elif self.provider == "local":
                return self._generate_with_local(prompt, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_code': '',
                'usage': {}
            }
    
    def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate test using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的C/C++单元测试工程师，专门生成Google Test + MockCpp测试用例。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                'success': True,
                'test_code': response.choices[0].message.content.strip(),
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': self.model
            }
            
        except openai.AuthenticationError:
            return {
                'success': False,
                'error': "Authentication failed. Please check your API key.",
                'test_code': '',
                'usage': {}
            }
        except openai.RateLimitError:
            return {
                'success': False,
                'error': "Rate limit exceeded. Please try again later.",
                'test_code': '',
                'usage': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"OpenAI API error: {str(e)}",
                'test_code': '',
                'usage': {}
            }
    
    def _generate_with_deepseek(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate test using DeepSeek API"""
        try:
            # DeepSeek uses OpenAI-compatible API format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的C/C++单元测试工程师，专门生成Google Test + MockCpp测试用例。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                'success': True,
                'test_code': response.choices[0].message.content.strip(),
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': self.model
            }
            
        except openai.AuthenticationError:
            return {
                'success': False,
                'error': "DeepSeek认证失败。请检查您的API密钥。",
                'test_code': '',
                'usage': {}
            }
        except openai.RateLimitError:
            return {
                'success': False,
                'error': "DeepSeek API速率限制 exceeded。请稍后重试。",
                'test_code': '',
                'usage': {}
            }
        except openai.APIError as e:
            return {
                'success': False,
                'error': f"DeepSeek API错误: {str(e)}",
                'test_code': '',
                'usage': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"DeepSeek请求错误: {str(e)}",
                'test_code': '',
                'usage': {}
            }
    
    def _generate_with_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate test using Anthropic API (placeholder)"""
        # This would be implemented when Anthropic API is available
        return {
            'success': False,
            'error': "Anthropic API not implemented yet",
            'test_code': '',
            'usage': {}
        }
    
    def _generate_with_local(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Generate test using local model (placeholder)"""
        # This would be implemented for local model inference
        return {
            'success': False,
            'error': "Local model inference not implemented yet",
            'test_code': '',
            'usage': {}
        }
    
    # File saving functionality has been moved to TestFileOrganizer
    # in src/utils/file_organizer.py for better separation of concerns


class MockLLMClient:
    """Mock LLM client for testing without real API calls"""
    
    def __init__(self):
        self.provider = "mock"
    
    def generate_test(self, prompt: str, max_tokens: int = 2000, 
                     temperature: float = 0.3) -> Dict[str, Any]:
        """Generate mock test code"""
        # Extract function name from prompt
        function_name = "unknown"
        if "函数签名:" in prompt:
            lines = prompt.split('\n')
            for line in lines:
                if line.startswith("函数签名:"):
                    # Extract function name from signature like "int add(int a, int b)"
                    signature = line.replace("函数签名:", "").strip()
                    # Split by space and take the second word (function name)
                    parts = signature.split()
                    if len(parts) >= 2:
                        # Get the part before '(' which should be the function name
                        func_part = parts[1].split('(')[0]
                        function_name = func_part
                    break
        
        # Generate mock test code based on function info
        test_code = self._generate_mock_test_code(function_name, prompt)
        
        return {
            'success': True,
            'test_code': test_code,
            'usage': {
                'prompt_tokens': len(prompt) // 4,
                'completion_tokens': len(test_code) // 4,
                'total_tokens': (len(prompt) + len(test_code)) // 4
            },
            'model': 'mock-gpt-3.5-turbo'
        }
    
    def _generate_mock_test_code(self, function_name: str, prompt: str) -> str:
        """Generate realistic mock test code"""
        # Debug: print what function name we received
        print(f"DEBUG: Generating test for function: '{function_name}'")
        
        if "divide" in function_name.lower():
            return self._generate_divide_test()
        elif "add" in function_name.lower():
            return self._generate_add_test()
        elif "multiply" in function_name.lower():
            return self._generate_multiply_test()
        elif "subtract" in function_name.lower():
            return self._generate_subtract_test()
        else:
            return self._generate_generic_test(function_name)
    
    def _generate_divide_test(self) -> str:
        return """#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, DivideNormalCases) {
    EXPECT_FLOAT_EQ(divide(10.0f, 2.0f), 5.0f);
    EXPECT_FLOAT_EQ(divide(1.0f, 4.0f), 0.25f);
    EXPECT_FLOAT_EQ(divide(-10.0f, 2.0f), -5.0f);
}

TEST(MathUtilsTest, DivideByZero) {
    EXPECT_FLOAT_EQ(divide(5.0f, 0.0f), 0.0f);
    EXPECT_FLOAT_EQ(divide(-5.0f, 0.0f), 0.0f);
    EXPECT_FLOAT_EQ(divide(0.0f, 0.0f), 0.0f);
}

TEST(MathUtilsTest, DivideEdgeCases) {
    EXPECT_FLOAT_EQ(divide(0.0f, 5.0f), 0.0f);
    EXPECT_FLOAT_EQ(divide(FLT_MAX, 2.0f), FLT_MAX / 2.0f);
    EXPECT_FLOAT_EQ(divide(FLT_MIN, 2.0f), FLT_MIN / 2.0f);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}"""
    
    def _generate_add_test(self) -> str:
        return """#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, AddNormalCases) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(add(-2, 3), 1);
    EXPECT_EQ(add(0, 0), 0);
}

TEST(MathUtilsTest, AddEdgeCases) {
    EXPECT_EQ(add(INT_MAX, 1), INT_MIN);  // Overflow behavior
    EXPECT_EQ(add(INT_MIN, -1), INT_MAX); // Underflow behavior
    EXPECT_EQ(add(INT_MAX, INT_MIN), -1);
}

TEST(MathUtilsTest, AddCommutative) {
    EXPECT_EQ(add(5, 3), add(3, 5));
    EXPECT_EQ(add(-5, 3), add(3, -5));
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}"""
    
    def _generate_multiply_test(self) -> str:
        return """#include <gtest/gtest.h>
#include "math_utils.h"

// Mock for add function since multiply calls add
int add(int a, int b) {
    return a + b;
}

TEST(MathUtilsTest, MultiplyNormalCases) {
    EXPECT_EQ(multiply(2, 3), 6);
    EXPECT_EQ(multiply(5, 0), 0);
    EXPECT_EQ(multiply(-2, 3), -6);
    EXPECT_EQ(multiply(-2, -3), 6);
}

TEST(MathUtilsTest, MultiplyEdgeCases) {
    EXPECT_EQ(multiply(INT_MAX, 2), -2);  // Overflow behavior
    EXPECT_EQ(multiply(INT_MIN, 2), 0);   // Underflow behavior
    EXPECT_EQ(multiply(0, INT_MAX), 0);
}

TEST(MathUtilsTest, MultiplyWithZero) {
    EXPECT_EQ(multiply(0, 5), 0);
    EXPECT_EQ(multiply(5, 0), 0);
    EXPECT_EQ(multiply(0, 0), 0);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}"""
    
    def _generate_subtract_test(self) -> str:
        return """#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, SubtractNormalCases) {
    EXPECT_EQ(subtract(5, 3), 2);
    EXPECT_EQ(subtract(3, 5), -2);
    EXPECT_EQ(subtract(0, 0), 0);
    EXPECT_EQ(subtract(-5, -3), -2);
}

TEST(MathUtilsTest, SubtractEdgeCases) {
    EXPECT_EQ(subtract(INT_MAX, -1), INT_MIN);  // Overflow
    EXPECT_EQ(subtract(INT_MIN, 1), INT_MAX);   // Underflow
    EXPECT_EQ(subtract(INT_MAX, INT_MAX), 0);
}

TEST(MathUtilsTest, SubtractCommutative) {
    EXPECT_EQ(subtract(5, 3), -(subtract(3, 5)));
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}"""
    
    def _generate_generic_test(self, function_name: str) -> str:
        return f"""#include <gtest/gtest.h>

// Generated test for {function_name}
TEST(GeneratedTest, {function_name}BasicTest) {{
    // Basic functionality test
    // TODO: Add specific test cases
}}

TEST(GeneratedTest, {function_name}EdgeCases) {{
    // Edge case tests
    // TODO: Add boundary tests
}}

int main(int argc, char **argv) {{
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}}"""
    
    # File saving functionality has been moved to TestFileOrganizer
    # in src/utils/file_organizer.py for better separation of concerns