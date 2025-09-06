#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：PromptTemplateLoader类
测试模板加载、占位符验证和变量替换功能
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, mock_open
from src.utils.prompt_template_loader import PromptTemplateLoader, TemplateValidationError


class TestPromptTemplateLoader(unittest.TestCase):
    """PromptTemplateLoader单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.loader = PromptTemplateLoader()
        
        # 创建临时目录和文件用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.temp_dir, 'templates', 'prompts')
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # 创建测试模板文件
        self.test_template_content = """
你好，{name}！
你的年龄是{age}岁。
{optional_section}
"""
        
        self.test_template_path = os.path.join(self.templates_dir, 'test_template.txt')
        with open(self.test_template_path, 'w', encoding='utf-8') as f:
            f.write(self.test_template_content)
        
        # 创建系统提示词配置文件
        self.system_prompts = {
            "c": "C语言系统提示词",
            "cpp": "C++语言系统提示词",
            "java": "Java语言系统提示词",
            "default": "默认系统提示词"
        }
        
        self.system_prompts_path = os.path.join(self.templates_dir, 'system_prompts.json')
        with open(self.system_prompts_path, 'w', encoding='utf-8') as f:
            json.dump(self.system_prompts, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_init_with_custom_templates_dir(self, mock_dirname):
        """测试自定义模板目录初始化"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        expected_path = os.path.join(self.temp_dir, 'templates', 'prompts')
        self.assertEqual(str(loader.templates_dir), expected_path)
    
    def test_extract_placeholders_basic(self):
        """测试基本占位符提取"""
        template = "Hello {name}, you are {age} years old."
        placeholders = self.loader.extract_placeholders(template)
        self.assertEqual(placeholders, {'name', 'age'})
    
    def test_extract_placeholders_nested(self):
        """测试嵌套占位符提取"""
        template = "Hello {user.name}, your score is {stats.score}."
        placeholders = self.loader.extract_placeholders(template)
        self.assertEqual(placeholders, {'user.name', 'stats.score'})
    
    def test_extract_placeholders_empty(self):
        """测试空模板占位符提取"""
        template = "No placeholders here."
        placeholders = self.loader.extract_placeholders(template)
        self.assertEqual(placeholders, set())
    
    def test_extract_placeholders_duplicate(self):
        """测试重复占位符提取"""
        template = "Hello {name}, {name} is your name."
        placeholders = self.loader.extract_placeholders(template)
        self.assertEqual(placeholders, {'name'})
    
    def test_validate_variables_success(self):
        """测试变量验证成功"""
        template = "Hello {name}, you are {age} years old."
        variables = {'name': 'Alice', 'age': 25}
        # 应该不抛出异常
        self.loader.validate_variables(template, variables, strict=True)
    
    def test_validate_variables_missing_strict(self):
        """测试严格模式下缺少变量"""
        template = "Hello {name}, you are {age} years old."
        variables = {'name': 'Alice'}  # 缺少age
        
        with self.assertRaises(TemplateValidationError) as context:
            self.loader.validate_variables(template, variables, strict=True)
        
        self.assertIn('Missing required variables', str(context.exception))
        self.assertIn('age', str(context.exception))
    
    def test_validate_variables_missing_non_strict(self):
        """测试非严格模式下缺少变量"""
        template = "Hello {name}, you are {age} years old."
        variables = {'name': 'Alice'}  # 缺少age
        
        # 非严格模式应该不抛出异常
        self.loader.validate_variables(template, variables, strict=False)
    
    def test_validate_variables_extra_variables(self):
        """测试额外变量（应该被忽略）"""
        template = "Hello {name}."
        variables = {'name': 'Alice', 'extra': 'value'}
        
        # 额外变量应该被忽略，不抛出异常
        self.loader.validate_variables(template, variables, strict=True)
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_load_template_success(self, mock_dirname):
        """测试成功加载模板"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        content = loader.load_template('test_template')
        self.assertEqual(content.strip(), self.test_template_content.strip())
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_load_template_not_found(self, mock_dirname):
        """测试加载不存在的模板"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        with self.assertRaises(FileNotFoundError):
            loader.load_template('nonexistent_template')
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_substitute_variables_success(self, mock_dirname):
        """测试成功变量替换"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        template = "Hello {name}, you are {age} years old."
        variables = {'name': 'Alice', 'age': 25}
        
        result = loader.substitute_variables(template, variables)
        expected = "Hello Alice, you are 25 years old."
        self.assertEqual(result, expected)
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_substitute_variables_missing_non_strict(self, mock_dirname):
        """测试非严格模式下缺少变量的替换"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        template = "Hello {name}, you are {age} years old."
        variables = {'name': 'Alice'}  # 缺少age
        
        result = loader.substitute_variables(template, variables, strict=False)
        expected = "Hello Alice, you are {age} years old."  # age保持原样
        self.assertEqual(result, expected)
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_load_and_substitute_success(self, mock_dirname):
        """测试加载并替换模板成功"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        variables = {
            'name': 'Alice',
            'age': 25,
            'optional_section': '这是可选部分。'
        }
        
        result = loader.load_and_substitute('test_template', variables)
        
        self.assertIn('Alice', result)
        self.assertIn('25', result)
        self.assertIn('这是可选部分', result)
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_get_system_prompt_success(self, mock_dirname):
        """测试成功获取系统提示词"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        # 测试已存在的语言
        c_prompt = loader.get_system_prompt('c')
        self.assertEqual(c_prompt, "C语言系统提示词")
        
        cpp_prompt = loader.get_system_prompt('cpp')
        self.assertEqual(cpp_prompt, "C++语言系统提示词")
        
        java_prompt = loader.get_system_prompt('java')
        self.assertEqual(java_prompt, "Java语言系统提示词")
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_get_system_prompt_default(self, mock_dirname):
        """测试获取默认系统提示词"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        # 测试不存在的语言，应该返回默认值
        unknown_prompt = loader.get_system_prompt('unknown_language')
        self.assertEqual(unknown_prompt, "默认系统提示词")
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_get_system_prompt_file_not_found(self, mock_dirname):
        """测试系统提示词文件不存在"""
        mock_dirname.return_value = '/nonexistent/path'
        loader = PromptTemplateLoader()
        
        # 文件不存在时应该返回默认值
        prompt = loader.get_system_prompt('c')
        self.assertEqual(prompt, "你是一个专业的C语言单元测试工程师，专门生成Google Test + MockCpp测试用例。")
    
    def test_template_validation_error_creation(self):
        """测试TemplateValidationError异常创建"""
        error = TemplateValidationError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)
    
    @patch('src.utils.prompt_template_loader.os.path.dirname')
    def test_complex_template_with_sections(self, mock_dirname):
        """测试复杂模板与条件部分"""
        mock_dirname.return_value = self.temp_dir
        loader = PromptTemplateLoader()
        
        # 创建复杂模板
        complex_template = """
# 标题：{title}

## 用户信息
姓名：{user_name}
年龄：{user_age}

{dependency_section}

{test_section}

## 结论
{conclusion}
"""
        
        complex_template_path = os.path.join(self.templates_dir, 'complex_template.txt')
        with open(complex_template_path, 'w', encoding='utf-8') as f:
            f.write(complex_template)
        
        variables = {
            'title': '测试报告',
            'user_name': '张三',
            'user_age': 30,
            'dependency_section': '## 依赖项\n- 依赖A\n- 依赖B',
            'test_section': '## 测试用例\n- 测试1\n- 测试2',
            'conclusion': '所有测试通过'
        }
        
        result = loader.load_and_substitute('complex_template', variables)
        
        self.assertIn('测试报告', result)
        self.assertIn('张三', result)
        self.assertIn('30', result)
        self.assertIn('依赖A', result)
        self.assertIn('测试1', result)
        self.assertIn('所有测试通过', result)


if __name__ == '__main__':
    unittest.main()