from typing import Dict, Any
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

class MockLLMClient:
    """Mock LLM client for testing without real API calls"""
    
    def __init__(self):
        self.provider = "mock"
    
    def generate_test(self, prompt: str, max_tokens: int = 2000, 
                     temperature: float = 0.3, **kwargs) -> Dict[str, Any]:
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
        # Debug: log what function name we received
        logger.debug(f"Generating test for function: '{function_name}'")
        
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
        return '''#include <gtest/gtest.h>
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
}'''
    
    def _generate_add_test(self) -> str:
        return '''#include <gtest/gtest.h>
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
}'''
    
    def _generate_multiply_test(self) -> str:
        return '''#include <gtest/gtest.h>
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
}'''
    
    def _generate_subtract_test(self) -> str:
        return '''#include <gtest/gtest.h>
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
}'''
    
    def _generate_generic_test(self, function_name: str) -> str:
        return f'''#include <gtest/gtest.h>

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
}}'''
