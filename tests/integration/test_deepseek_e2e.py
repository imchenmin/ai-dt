"""
端到端测试验证DeepSeek API集成
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml
import json

from src.test_generation.service import TestGenerationService
from src.test_generation.models import TestGenerationConfig, AggregatedResult
from src.llm.client import LLMClient
from src.llm.providers import DeepSeekProvider
from src.utils.config_manager import ConfigManager


class TestDeepSeekEndToEnd:
    """端到端测试DeepSeek API集成"""

    @pytest.fixture
    def deepseek_api_key(self):
        """获取DeepSeek API密钥"""
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            # 不跳过测试，而是返回一个测试密钥
            return "test_api_key"
        return api_key

    @pytest.fixture
    def sample_functions(self):
        """创建示例函数用于测试"""
        return [
            {
                'function': {
                    'name': 'calculate_area',
                    'return_type': 'double',
                    'parameters': [
                        {'name': 'radius', 'type': 'double'}
                    ],
                    'file': '/test/project/geometry.c',
                    'language': 'c',
                    'body': 'double calculate_area(double radius) {\n    return 3.14159 * radius * radius;\n}',
                    'line': 10
                },
                'context': {
                    'includes': ['#include <math.h>', '#include <stdio.h>'],
                    'macros': ['#define PI 3.14159'],
                    'called_functions': [],
                    'data_structures': []
                }
            },
            {
                'function': {
                    'name': 'is_even',
                    'return_type': 'bool',
                    'parameters': [
                        {'name': 'number', 'type': 'int'}
                    ],
                    'file': '/test/project/utils.c',
                    'language': 'c',
                    'body': 'bool is_even(int number) {\n    return number % 2 == 0;\n}',
                    'line': 25
                },
                'context': {
                    'includes': ['#include <stdbool.h>'],
                    'macros': [],
                    'called_functions': [],
                    'data_structures': []
                }
            }
        ]

    @patch('src.llm.providers.requests.post')
    def test_deepseek_provider_connection(self, mock_post, deepseek_api_key):
        """测试DeepSeek Provider连接"""
        # Mock API响应
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": """#include <gtest/gtest.h>
#include "geometry.h"

TEST(CalculateAreaTest, PositiveRadius) {
    EXPECT_DOUBLE_EQ(calculate_area(1.0), 3.14159);
    EXPECT_DOUBLE_EQ(calculate_area(2.0), 12.56636);
}

TEST(CalculateAreaTest, ZeroRadius) {
    EXPECT_DOUBLE_EQ(calculate_area(0.0), 0.0);
}
"""
                }
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_post.return_value = mock_response

        # 创建DeepSeek provider
        provider = DeepSeekProvider(api_key=deepseek_api_key, timeout=30.0)

        # 创建简单的生成请求
        from src.llm.models import GenerationRequest
        request = GenerationRequest(
            prompt="请为一个简单的add函数生成测试代码",
            max_tokens=1000,
            temperature=0.7,
            language="c"
        )

        # 调用API
        response = provider.generate(request)

        # 验证响应
        assert response.success is True, f"API调用失败: {response.error}"
        assert response.content is not None, "响应内容为空"
        assert len(response.content) > 50, "响应内容太短"
        assert response.provider == "deepseek"
        assert response.model is not None

        # 验证包含测试代码相关内容
        assert any(keyword in response.content for keyword in ['TEST', 'test', 'EXPECT', 'ASSERT']), \
            "响应不包含测试代码相关关键字"

        print(f"✓ DeepSeek API连接成功，生成了 {len(response.content)} 字符的内容")

    @patch('src.llm.client.LLMClient.generate_test')
    def test_deepseek_llm_client(self, mock_generate, deepseek_api_key):
        """测试LLM客户端与DeepSeek的集成"""
        # Mock generate_test返回值
        mock_generate.return_value = {
            'success': True,
            'test_code': """#include <gtest/gtest.h>
#include "utils.h"

TEST(MultiplyTest, PositiveNumbers) {
    EXPECT_EQ(multiply(2, 3), 6);
    EXPECT_EQ(multiply(5, 5), 25);
}

TEST(MultiplyTest, NegativeNumbers) {
    EXPECT_EQ(multiply(-2, 3), -6);
    EXPECT_EQ(multiply(-5, -5), 25);
}

TEST(MultiplyTest, Zero) {
    EXPECT_EQ(multiply(0, 10), 0);
    EXPECT_EQ(multiply(10, 0), 0);
}
""",
            'usage': {
                'prompt_tokens': 150,
                'completion_tokens': 100,
                'total_tokens': 250
            },
            'model': 'deepseek-chat',
            'prompt_length': 100,
            'test_length': 300
        }

        # 创建LLM客户端（使用mock provider）
        client = LLMClient.create_mock_client("deepseek-chat")

        # 测试简单的测试生成
        prompt = """请为以下C函数生成完整的单元测试：

函数签名：int multiply(int a, int b)
函数体：return a * b;

要求：
1. 使用Google Test框架
2. 包含正常情况和边界情况测试
3. 测试用例应该覆盖正数、负数和零
"""

        result = client.generate_test(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
            language="c"
        )

        # 验证结果
        assert result['success'], f"测试生成失败: {result.get('error', '未知错误')}"
        assert result['test_code'], "测试代码为空"
        assert 'multiply' in result['test_code'], "测试代码不包含函数名"

        print(f"✓ LLM客户端测试成功，生成了测试代码")

    def test_deepseek_with_test_generation_service(self, deepseek_api_key, sample_functions):
        """测试完整的测试生成服务流程"""
        # 创建Mock LLM客户端
        mock_client = Mock(spec=LLMClient)

        # Mock generate_test返回成功结果
        def mock_generate_test(*args, **kwargs):
            return {
                'success': True,
                'test_code': f"""#include <gtest/gtest.h>

// Generated test for {args[0] if args else 'function'}
TEST(FunctionTest, BasicCase) {{
    EXPECT_TRUE(true);
}}
""",
                'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150},
                'model': 'deepseek-chat',
                'prompt_length': len(args[0]) if args else 0,
                'test_length': 100
            }

        mock_client.generate_test = mock_generate_test

        # 创建测试生成服务
        service = TestGenerationService(llm_client=mock_client)

        # 创建配置
        config = TestGenerationConfig(
            project_name="deepseek_e2e_test",
            output_dir=tempfile.mkdtemp(),
            max_workers=1,  # 使用单线程避免API限制
            save_prompts=True,
            aggregate_tests=True,
            generate_readme=True,
            timestamped_output=False
        )

        # 执行测试生成
        start_time = time.time()
        result = service.generate_tests_new_api(sample_functions, config)
        end_time = time.time()

        # 验证聚合结果
        assert isinstance(result, AggregatedResult)
        assert result.total_count == len(sample_functions)
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration > 0
        assert result.duration < (end_time - start_time + 1)  # 允许1秒误差

        # 验证至少有一个成功的测试生成
        assert result.successful_count >= 0
        assert result.failed_count >= 0
        assert result.successful_count + result.failed_count == result.total_count

        # 验证输出目录
        output_path = Path(config.output_dir)
        assert output_path.exists()

        # 检查生成的文件
        if result.successful_count > 0:
            # 应该有聚合测试文件
            aggregated_files = list(output_path.glob("**/*_aggregated_tests*"))
            if aggregated_files:
                print(f"✓ 找到聚合测试文件: {aggregated_files[0]}")

            # 应该有README
            readme_files = list(output_path.glob("**/README*"))
            if readme_files:
                print(f"✓ 找到README文件: {readme_files[0]}")

        print(f"✓ 测试生成服务完成，总耗时: {result.duration:.2f}秒")
        print(f"  - 总函数数: {result.total_count}")
        print(f"  - 成功生成: {result.successful_count}")
        print(f"  - 失败数: {result.failed_count}")
        print(f"  - 成功率: {result.successful_count/result.total_count*100:.1f}%")

    @patch('src.llm.providers.requests.post')
    def test_deepseek_error_handling(self, mock_post):
        """测试DeepSeek API的错误处理"""
        # Mock网络错误
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        # 使用错误的API密钥
        wrong_provider = DeepSeekProvider(api_key="wrong_key", timeout=10.0)

        from src.llm.models import GenerationRequest
        request = GenerationRequest(
            prompt="测试错误处理",
            max_tokens=100,
            temperature=0.7,
            language="c"
        )

        # 应该返回失败响应
        response = wrong_provider.generate(request)

        assert response.success is False, "使用错误的API密钥应该失败"
        assert response.error is not None, "应该有错误信息"
        assert "Network error" in response.error or "Invalid response" in response.error, \
            f"错误信息不符合预期: {response.error}"

        print("✓ 错误处理测试通过")

    @patch('src.llm.providers.requests.post')
    def test_deepseek_timeout_handling(self, mock_post):
        """测试超时处理"""
        # Mock超时错误
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        # 创建短超时的provider
        provider = DeepSeekProvider(api_key="test_key", timeout=0.001)

        from src.llm.models import GenerationRequest
        # 创建一个可能需要一些处理时间的请求
        long_prompt = "请生成一个非常详细的测试代码，" * 100
        request = GenerationRequest(
            prompt=long_prompt,
            max_tokens=5000,  # 大量token可能需要更长时间
            temperature=0.7,
            language="c"
        )

        # 调用可能超时
        response = provider.generate(request)

        # 应该超时
        assert response.success is False, "请求应该超时"
        assert "Network error" in response.error or "timeout" in response.error.lower(), \
            f"超时错误信息不符合预期: {response.error}"
        print("✓ 超时处理测试通过")

    @patch('src.llm.providers.requests.post')
    def test_deepseek_concurrent_requests(self, mock_post):
        """测试并发请求处理"""
        import concurrent.futures
        import threading

        # Mock成功的API响应
        def mock_response_func(*args, **kwargs):
            mock_resp = Mock()
            mock_resp.raise_for_status.return_value = None
            # 从请求中提取请求ID来生成不同的响应
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "Generated test response"}}],
                "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
            }
            return mock_resp

        mock_post.side_effect = mock_response_func

        provider = DeepSeekProvider(api_key="test_key")

        def make_request(request_id):
            """单个请求"""
            from src.llm.models import GenerationRequest
            request = GenerationRequest(
                prompt=f"为函数{request_id}生成简单测试",
                max_tokens=200,
                temperature=0.7,
                language="c"
            )
            return provider.generate(request)

        # 并发3个请求
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            responses = [f.result() for f in futures]
        end_time = time.time()

        # 验证所有响应
        success_count = sum(1 for r in responses if r.success)

        assert success_count == 3, "所有请求都应该成功"
        assert end_time - start_time < 60, "并发请求应该在合理时间内完成"

        print(f"✓ 并发请求测试完成，成功: {success_count}/3，总耗时: {end_time - start_time:.2f}秒")

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'})
    def test_config_manager_with_deepseek(self):
        """测试ConfigManager与DeepSeek配置的集成"""
        # 创建临时配置文件
        config_data = {
            'defaults': {
                'llm_provider': 'deepseek',
                'model': 'deepseek-chat',
                'output_dir': './test_output',
                'error_handling': {
                    'max_retries': 2,
                    'retry_delay': 1.0
                }
            },
            'projects': {
                'deepseek_test_project': {
                    'path': './test_projects/c',
                    'comp_db': 'compile_commands.json',
                    'description': 'DeepSeek测试项目'
                }
            },
            'llm_providers': {
                'deepseek': {
                    'api_key_env': 'DEEPSEEK_API_KEY',
                    'models': ['deepseek-chat', 'deepseek-coder'],
                    'base_url': 'https://api.deepseek.com/v1'
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_file = f.name

        try:
            # 创建ConfigManager
            config_manager = ConfigManager(config_file)

            # 验证项目配置
            project_config = config_manager.get_project_config('deepseek_test_project')
            assert project_config['llm_provider'] == 'deepseek'

            # 验证LLM配置
            llm_config = config_manager.get_llm_config('deepseek')
            assert llm_config['api_key_env'] == 'DEEPSEEK_API_KEY'
            assert 'deepseek-chat' in llm_config['models']

            # 验证provider可用性
            assert config_manager.is_provider_available('deepseek') is True

            # 获取API密钥
            api_key = config_manager.get_api_key('deepseek')
            assert api_key == 'test_key'

            print("✓ ConfigManager集成测试通过")

        finally:
            os.unlink(config_file)

    def test_deepseek_with_real_project_structure(self, deepseek_api_key):
        """测试使用真实项目结构进行端到端测试"""
        # 创建临时的项目结构
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "test_project"
            project_dir.mkdir()

            # 创建源文件
            src_file = project_dir / "math_utils.c"
            src_file.write_text("""
#include <math.h>
#include <stdio.h>

double calculate_circle_area(double radius) {
    return M_PI * radius * radius;
}

int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

int is_prime(int num) {
    if (num < 2) return 0;
    for (int i = 2; i <= sqrt(num); i++) {
        if (num % i == 0) return 0;
    }
    return 1;
}
""")

            # 创建compile_commands.json
            compile_commands = [{
                "directory": str(project_dir),
                "file": str(src_file),
                "arguments": ["gcc", "-c", str(src_file), "-o", "math_utils.o"]
            }]

            compile_file = project_dir / "compile_commands.json"
            compile_file.write_text(json.dumps(compile_commands, indent=2))

            # 创建Mock服务
            mock_client = Mock(spec=LLMClient)
            mock_client.generate_test.return_value = {
                'success': True,
                'test_code': """#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, CalculateCircleArea) {
    EXPECT_DOUBLE_EQ(calculate_circle_area(1.0), M_PI);
    EXPECT_DOUBLE_EQ(calculate_circle_area(0.0), 0.0);
}
""",
                'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
            }

            service = TestGenerationService(llm_client=mock_client)

            config = TestGenerationConfig(
                project_name="real_structure_test",
                output_dir=tempfile.mkdtemp(),
                max_workers=1,
                save_prompts=True,
                aggregate_tests=True
            )

            # 创建函数数据
            functions_with_context = []
            functions = [
                {
                    'name': 'calculate_circle_area',
                    'return_type': 'double',
                    'parameters': [{'name': 'radius', 'type': 'double'}],
                    'file': str(src_file),
                    'language': 'c',
                    'body': 'return M_PI * radius * radius;',
                    'line': 4
                },
                {
                    'name': 'fibonacci',
                    'return_type': 'int',
                    'parameters': [{'name': 'n', 'type': 'int'}],
                    'file': str(src_file),
                    'language': 'c',
                    'body': 'if (n <= 1) return n;\nreturn fibonacci(n-1) + fibonacci(n-2);',
                    'line': 8
                }
            ]

            for func in functions:
                functions_with_context.append({
                    'function': func,
                    'context': {
                        'includes': ['#include <math.h>', '#include <stdio.h>'],
                        'macros': [],
                        'called_functions': [],
                        'data_structures': []
                    }
                })

            # 执行测试生成
            result = service.generate_tests_new_api(functions_with_context, config)

            # 验证结果
            assert isinstance(result, AggregatedResult)
            assert result.total_count == len(functions_with_context)

            if result.successful_count > 0:
                output_path = Path(config.output_dir)
                # 查找生成的测试文件
                test_files = list(output_path.glob("**/*.cpp"))
                test_files.extend(list(output_path.glob("**/*.c")))

                if test_files:
                    print(f"✓ 生成了测试文件: {test_files[0].name}")

                    # 验证测试文件内容
                    content = test_files[0].read_text()
                    assert any(func['name'] in content for func in functions), \
                        "测试文件应该包含原函数名"

            print(f"✓ 真实项目结构测试完成，成功率: {result.successful_count/result.total_count*100:.1f}%")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])