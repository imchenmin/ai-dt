#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：验证C语言测试生成模板修复
验证测试套类结构不再重复出现的问题已被修复
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from test_generation.models import PromptContext, TargetFunction, Dependencies, Language, Parameter
from utils.prompt_template_loader import PromptTemplateLoader


class TestTemplateDuplicationFix(unittest.TestCase):
    """测试模板重复问题修复"""
    
    def setUp(self):
        """设置测试环境"""
        self.template_loader = PromptTemplateLoader()
        
        # 创建TargetFunction对象
        target_function = TargetFunction(
            name='memory_pool_alloc',
            signature='void* memory_pool_alloc(size_t size)',
            return_type='void*',
            parameters=[Parameter(name='size', type='size_t')],
            body='',
            location='src/memory_pool.c:45',
            language=Language.C
        )
        
        # 创建Dependencies对象
        dependencies = Dependencies()
        
        # 创建PromptContext对象
        self.test_context = PromptContext(
            target_function=target_function,
            dependencies=dependencies,
            suite_name='memory_poolTest',
            existing_fixture_code='class memory_poolTest : public ::testing::Test {};'
        )
        
        # 用于模板渲染的简化上下文
        self.template_context = {
            'target_function_name': 'memory_pool_alloc',
            'target_location': 'src/memory_pool.c:45',
            'function_signature': 'void* memory_pool_alloc(size_t size)',
            'filename': 'memory_pool',
            'suite_name': 'memory_poolTest',
            'existing_fixture_code': 'class memory_poolTest : public ::testing::Test {};'
        }
    
    def test_template_loads_successfully(self):
        """测试模板能够成功加载"""
        try:
            rendered_prompt = self.template_loader.render_template('c/test_generation.j2', self.template_context)
            self.assertIsNotNone(rendered_prompt)
        except Exception as e:
            self.fail(f"模板加载失败: {e}")
    
    def test_no_duplicate_test_class_structure(self):
        """测试模板中测试类结构不重复"""
        # 渲染模板
        rendered_prompt = self.template_loader.render_template('c/test_generation.j2', self.template_context)
        
        # 检查测试类结构出现次数
        test_class_pattern = f'class {self.template_context["suite_name"]} : public ::testing::Test'
        occurrences = rendered_prompt.count(test_class_pattern)
        
        # 断言：测试类结构应该只出现一次
        self.assertEqual(occurrences, 1, 
                        f"测试类结构出现了{occurrences}次，应该只出现1次")
    
    def test_existing_fixture_section_present(self):
        """测试EXISTING_FIXTURE部分正确显示"""
        rendered_prompt = self.template_loader.render_template('c/test_generation.j2', self.template_context)
        
        # 检查EXISTING_FIXTURE部分是否存在
        self.assertIn('EXISTING_FIXTURE', rendered_prompt)
        self.assertIn(self.template_context['existing_fixture_code'], rendered_prompt)
    
    def test_code_structure_template_section_present(self):
        """测试CODE_STRUCTURE_TEMPLATE部分正确显示"""
        rendered_prompt = self.template_loader.render_template('c/test_generation.j2', self.template_context)
        
        # 检查CODE_STRUCTURE_TEMPLATE部分是否存在
        self.assertIn('**CODE_STRUCTURE_TEMPLATE**:', rendered_prompt)
        
        # 当有existing_fixture_code时，应该显示EXISTING_FIXTURE部分
        if 'existing_fixture_code' in self.template_context and self.template_context['existing_fixture_code']:
            self.assertIn('**EXISTING_FIXTURE**:', rendered_prompt)
            self.assertIn(self.template_context['existing_fixture_code'], rendered_prompt)
        else:
            # 当没有existing_fixture_code时，应该包含SetUp和TearDown方法
            self.assertIn('SetUp() override', rendered_prompt)
            self.assertIn('TearDown() override', rendered_prompt)
    
    def test_suite_name_used_correctly(self):
        """测试suite_name正确使用"""
        rendered_prompt = self.template_loader.render_template('c/test_generation.j2', self.template_context)
        
        # 检查suite_name在NAMING_CONVENTIONS部分的使用
        self.assertIn(f'Test class: `{self.template_context["suite_name"]}`', rendered_prompt)
    
    def test_template_without_suite_name(self):
        """测试没有suite_name时使用filename_test"""
        # 创建不包含suite_name和existing_fixture_code的上下文
        context_without_suite = {
            'filename': 'memory_pool'
        }
        
        rendered_prompt = self.template_loader.render_template('c/test_generation.j2', context_without_suite)
        
        # 检查使用filename_test作为类名
        expected_class_name = f'{context_without_suite["filename"]}_test'
        self.assertIn(f'class {expected_class_name} : public ::testing::Test', rendered_prompt)
        self.assertIn(f'Test class: `{expected_class_name}`', rendered_prompt)


if __name__ == '__main__':
    unittest.main()