"""测试现有测试上下文集成功能的单元测试"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.test_generation.service import TestGenerationService
from src.utils.test_file_matcher import TestFileMatcher
from src.utils.config_manager import ConfigManager


class TestExistingTestsIntegration(unittest.TestCase):
    """测试现有测试上下文集成功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, "tests")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # 创建测试文件
        self.test_file_path = os.path.join(self.test_dir, "math_utils_test.cpp")
        with open(self.test_file_path, 'w') as f:
            f.write("""
#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, TestAdd) {
    EXPECT_EQ(add(2, 3), 5);
}

void test_multiply() {
    // Simple test function
}
""")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.project_root, ignore_errors=True)
    
    @patch('src.utils.config_manager.ConfigManager.get_project_config')
    def test_service_integration_with_existing_tests(self, mock_config_get):
        """测试服务集成现有测试功能"""
        # 配置mock
        mock_config_get.return_value = {'unit_test_directory_path': self.test_dir}
        
        # 创建服务实例
        service = TestGenerationService()
        
        # 模拟函数数据
        functions_with_context = [
            {
                'function': {
                    'name': 'add',
                    'file': os.path.join(self.project_root, 'math_utils.cpp'),
                    'return_type': 'int',
                    'parameters': []
                },
                'context': {}
            }
        ]
        
        # 模拟项目配置
        project_config = {
            'path': self.project_root,
            'comp_db': 'compile_commands.json',
            'description': 'Test Project'
        }
        
        # 使用patch来模拟其他依赖
        with patch('src.test_generation.service.ensure_libclang_configured'), \
             patch('src.test_generation.service.CompilationDatabaseParser') as mock_parser, \
             patch('src.test_generation.service.FunctionAnalyzer') as mock_analyzer:
            
            # 配置mock
            mock_parser_instance = Mock()
            mock_parser.return_value = mock_parser_instance
            mock_parser_instance.parse.return_value = [{
                'file': os.path.join(self.project_root, 'math_utils.cpp'),
                'arguments': []
            }]
            
            mock_analyzer_instance = Mock()
            mock_analyzer.return_value = mock_analyzer_instance
            mock_analyzer_instance.analyze_file.return_value = [{
                'name': 'add',
                'file': os.path.join(self.project_root, 'math_utils.cpp'),
                'return_type': 'int',
                'parameters': []
            }]
            mock_analyzer_instance._analyze_function_context.return_value = {}
            
            # 调用analyze_project_functions方法
            result = service.analyze_project_functions(project_config)
            
            # 验证结果
            self.assertEqual(len(result), 1)
            function_data = result[0]
            
            # 验证existing_tests_context字段存在
            self.assertIn('existing_tests_context', function_data)
            
            # 如果找到了现有测试，验证其结构
            existing_tests = function_data['existing_tests_context']
            if existing_tests:
                self.assertIn('matched_test_files', existing_tests)
                self.assertIn('existing_test_functions', existing_tests)
    
    def test_test_file_matcher_integration(self):
        """测试TestFileMatcher集成"""
        matcher = TestFileMatcher(self.test_dir, self.project_root)
        
        # 测试获取测试上下文
        context = matcher.get_test_context_for_function(
            'add', 
            os.path.join(self.project_root, 'math_utils.cpp')
        )
        
        # 验证结果
        self.assertIsNotNone(context)
        self.assertIn('matched_test_files', context)
        self.assertIn('existing_test_functions', context)
        self.assertIn('test_coverage_summary', context)
        
        # 验证找到的测试文件
        self.assertTrue(len(context['matched_test_files']) > 0)
        
        # 验证找到的测试函数
        test_functions = context['existing_test_functions']
        function_names = [func['name'] for func in test_functions]
        # 应该找到与add函数相关的测试
        self.assertIn('TEST(MathUtilsTest, TestAdd)', function_names)
        # test_multiply与add函数无关，所以不应该被包含在结果中


if __name__ == '__main__':
    unittest.main()