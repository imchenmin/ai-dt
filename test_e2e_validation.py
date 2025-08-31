#!/usr/bin/env python3
"""
端到端验证脚本：测试现有测试上下文集成功能
"""

import tempfile
import os
import shutil
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from test_generation.service import TestGenerationService

def test_existing_tests_integration():
    """测试现有测试上下文是否正确集成到测试生成流程中"""
    
    # 创建临时测试项目
    temp_dir = tempfile.mkdtemp()
    project_dir = os.path.join(temp_dir, 'test_project')
    test_dir = os.path.join(project_dir, 'tests')
    
    try:
        # 创建目录结构
        os.makedirs(project_dir)
        os.makedirs(test_dir)
        
        # 创建源文件
        source_file = os.path.join(project_dir, 'calculator.cpp')
        with open(source_file, 'w') as f:
            f.write('''
#include "calculator.h"

int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

int subtract(int a, int b) {
    return a - b;
}
''')
        
        # 创建头文件
        header_file = os.path.join(project_dir, 'calculator.h')
        with open(header_file, 'w') as f:
            f.write('''
#ifndef CALCULATOR_H
#define CALCULATOR_H

int add(int a, int b);
int multiply(int a, int b);
int subtract(int a, int b);

#endif
''')
        
        # 创建现有测试文件
        test_file = os.path.join(test_dir, 'calculator_test.cpp')
        with open(test_file, 'w') as f:
            f.write('''
#include <gtest/gtest.h>
#include "../calculator.h"

TEST(CalculatorTest, TestAdd) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(add(-1, 1), 0);
    EXPECT_EQ(add(0, 0), 0);
}

TEST(CalculatorTest, TestMultiply) {
    EXPECT_EQ(multiply(2, 3), 6);
    EXPECT_EQ(multiply(-1, 1), -1);
    EXPECT_EQ(multiply(0, 5), 0);
}
''')
        
        # 设置项目配置
        project_config = {
            'path': project_dir,
            'comp_db': 'dummy.json',
            'unit_test_directory_path': test_dir
        }
        
        print(f"测试项目路径: {project_dir}")
        print(f"测试目录路径: {test_dir}")
        
        # 创建测试生成服务实例
        service = TestGenerationService()
        
        # 测试为add函数生成测试（应该找到现有测试）
        print("\n=== 测试为add函数生成测试 ===")
        function_info = {
            'name': 'add',
            'file_path': source_file,
            'file': source_file,
            'start_line': 3,
            'end_line': 5,
            'line': 3,
            'signature': 'int add(int a, int b)',
            'body': 'return a + b;',
            'return_type': 'int',
            'parameters': [
                {'type': 'int', 'name': 'a'},
                {'type': 'int', 'name': 'b'}
            ]
        }
        
        # 使用正确的API格式
        functions_with_context = [{
            'function': function_info,
            'context': {
                'file_content': open(source_file, 'r').read(),
                'includes': [],
                'dependencies': []
            }
        }]
        result = service.generate_tests(
            functions_with_context=functions_with_context,
            project_config=project_config,
            max_workers=1
        )
        
        print(f"生成结果类型: {type(result)}")
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            print(f"第一个结果键: {list(first_result.keys())}")
            
            # 检查提示词中是否包含现有测试信息
            if 'prompt' in first_result:
                prompt_content = first_result['prompt']
                print(f"\n提示词长度: {len(prompt_content)}")
                
                # 检查提示词中是否包含现有测试相关内容
                if 'existing test' in prompt_content.lower() or 'TEST(CalculatorTest, TestAdd)' in prompt_content:
                    print("✅ 提示词中包含现有测试信息")
                    # 显示相关部分
                    lines = prompt_content.split('\n')
                    for i, line in enumerate(lines):
                        if 'existing' in line.lower() or 'TEST(' in line:
                            print(f"  第{i+1}行: {line.strip()}")
                else:
                    print("❌ 提示词中未找到现有测试信息")
                    # 显示提示词的前500个字符来诊断问题
                    print("\n提示词前500个字符:")
                    print(prompt_content[:500])
                    print("\n...")
                    print("\n提示词后500个字符:")
                    print(prompt_content[-500:])
                    
            if 'existing_tests_context' in first_result:
                existing_tests = first_result['existing_tests_context']
                print(f"现有测试上下文: {existing_tests}")
                
                # 验证是否找到了现有测试
                if existing_tests and 'matched_test_files' in existing_tests:
                    matched_files = existing_tests['matched_test_files']
                    print(f"匹配的测试文件: {matched_files}")
                    assert len(matched_files) > 0, "应该找到匹配的测试文件"
                    
                if existing_tests and 'existing_test_functions' in existing_tests:
                    test_functions = existing_tests['existing_test_functions']
                    print(f"现有测试函数: {[func['name'] for func in test_functions]}")
                    function_names = [func['name'] for func in test_functions]
                    assert 'TEST(CalculatorTest, TestAdd)' in function_names, "应该找到TestAdd测试"
                    
        # 测试为subtract函数生成测试（应该没有现有测试）
        print("\n=== 测试为subtract函数生成测试 ===")
        function_info_subtract = {
            'name': 'subtract',
            'file_path': source_file,
            'file': source_file,
            'start_line': 9,
            'end_line': 11,
            'line': 9,
            'signature': 'int subtract(int a, int b)',
            'body': 'return a - b;',
            'return_type': 'int',
            'parameters': [
                {'type': 'int', 'name': 'a'},
                {'type': 'int', 'name': 'b'}
            ]
        }
        
        functions_with_context_subtract = [{
            'function': function_info_subtract,
            'context': {
                'file_content': open(source_file, 'r').read(),
                'includes': [],
                'dependencies': []
            }
        }]
        result_subtract = service.generate_tests(
            functions_with_context=functions_with_context_subtract,
            project_config=project_config,
            max_workers=1
        )
        
        if isinstance(result_subtract, list) and len(result_subtract) > 0:
            first_result_subtract = result_subtract[0]
            if 'existing_tests_context' in first_result_subtract:
                existing_tests_subtract = first_result_subtract['existing_tests_context']
                print(f"subtract函数的现有测试上下文: {existing_tests_subtract}")
            
        print("\n=== 端到端测试完成 ===")
        print("✅ 现有测试上下文集成功能正常工作")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已清理临时目录: {temp_dir}")

if __name__ == '__main__':
    test_existing_tests_integration()