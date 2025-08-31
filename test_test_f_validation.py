#!/usr/bin/env python3
"""
验证TEST_F格式测试用例匹配功能的端到端测试
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.test_file_matcher import TestFileMatcher

def test_test_f_matching():
    """
    测试TEST_F格式的测试用例匹配功能
    """
    # 创建临时测试项目
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "test_project"
    project_path.mkdir()
    
    try:
        # 创建源文件
        source_file = project_path / "calculator.cpp"
        source_content = """
#include "calculator.h"

int Calculator::add(int a, int b) {
    return a + b;
}

int Calculator::subtract(int a, int b) {
    return a - b;
}

int Calculator::multiply(int a, int b) {
    return a * b;
}
"""
        source_file.write_text(source_content, encoding='utf-8')
        
        # 创建头文件
        header_file = project_path / "calculator.h"
        header_content = """
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    int add(int a, int b);
    int subtract(int a, int b);
    int multiply(int a, int b);
};

#endif // CALCULATOR_H
"""
        header_file.write_text(header_content, encoding='utf-8')
        
        # 创建测试目录
        test_dir = project_path / "tests"
        test_dir.mkdir()
        
        # 创建包含TEST_F格式的测试文件
        test_file = test_dir / "calculator_test.cpp"
        test_content = """
#include <gtest/gtest.h>
#include "../calculator.h"

class CalculatorTest : public ::testing::Test {
protected:
    void SetUp() override {
        calc = new Calculator();
    }
    
    void TearDown() override {
        delete calc;
    }
    
    Calculator* calc;
};

// 测试add函数
TEST_F(CalculatorTest, TestAdd) {
    EXPECT_EQ(5, calc->add(2, 3));
    EXPECT_EQ(0, calc->add(-1, 1));
    EXPECT_EQ(-5, calc->add(-2, -3));
}

// 测试subtract函数
TEST_F(CalculatorTest, TestSubtract) {
    EXPECT_EQ(1, calc->subtract(3, 2));
    EXPECT_EQ(-2, calc->subtract(-1, 1));
    EXPECT_EQ(1, calc->subtract(-2, -3));
}

// 测试multiply函数 - 使用普通TEST格式
TEST(CalculatorBasicTest, TestMultiply) {
    Calculator calc;
    EXPECT_EQ(6, calc.multiply(2, 3));
    EXPECT_EQ(-6, calc.multiply(-2, 3));
    EXPECT_EQ(0, calc.multiply(0, 5));
}
"""
        test_file.write_text(test_content, encoding='utf-8')
        
        # 注意: 这里不需要配置文件，直接使用TestFileMatcher
        
        # 创建TestFileMatcher实例
        matcher = TestFileMatcher(
            project_path=str(project_path),
            test_directory=str(test_dir)
        )
        
        print("=== 测试TEST_F格式匹配功能 ===")
        
        # 测试1: 查找add函数的现有测试
        print("\n1. 测试add函数的TEST_F匹配:")
        add_tests = matcher.get_existing_tests_for_function(
            source_file_path=str(source_file),
            function_name="add"
        )
        
        print(f"找到 {len(add_tests)} 个add函数的测试:")
        for test in add_tests:
            print(f"  - {test['name']} (目标函数: {test['target_function']})")
            if 'TEST_F' in test['name']:
                print("    ✅ 成功识别TEST_F格式")
            
        # 测试2: 查找subtract函数的现有测试
        print("\n2. 测试subtract函数的TEST_F匹配:")
        subtract_tests = matcher.get_existing_tests_for_function(
            source_file_path=str(source_file),
            function_name="subtract"
        )
        
        print(f"找到 {len(subtract_tests)} 个subtract函数的测试:")
        for test in subtract_tests:
            print(f"  - {test['name']} (目标函数: {test['target_function']})")
            if 'TEST_F' in test['name']:
                print("    ✅ 成功识别TEST_F格式")
        
        # 测试3: 查找multiply函数的现有测试（普通TEST格式）
        print("\n3. 测试multiply函数的TEST匹配:")
        multiply_tests = matcher.get_existing_tests_for_function(
            source_file_path=str(source_file),
            function_name="multiply"
        )
        
        print(f"找到 {len(multiply_tests)} 个multiply函数的测试:")
        for test in multiply_tests:
            print(f"  - {test['name']} (目标函数: {test['target_function']})")
            if 'TEST(' in test['name'] and 'TEST_F' not in test['name']:
                print("    ✅ 成功识别普通TEST格式")
        
        # 测试4: 提取所有测试函数
        print("\n4. 提取所有测试函数:")
        all_tests = matcher.extract_test_functions(str(test_file))
        print(f"总共找到 {len(all_tests)} 个测试函数:")
        
        test_f_count = 0
        test_count = 0
        
        for test in all_tests:
            print(f"  - {test['name']}")
            if 'TEST_F(' in test['name']:
                test_f_count += 1
                print("    类型: TEST_F (测试夹具)")
            elif 'TEST(' in test['name']:
                test_count += 1
                print("    类型: TEST (基础测试)")
        
        print(f"\n统计结果:")
        print(f"  - TEST_F格式: {test_f_count} 个")
        print(f"  - TEST格式: {test_count} 个")
        print(f"  - 总计: {len(all_tests)} 个")
        
        # 验证结果
        if test_f_count >= 2 and test_count >= 1:
            print("\n✅ TEST_F格式匹配功能测试通过!")
            print("✅ 同时支持TEST和TEST_F两种格式")
        else:
            print("\n❌ TEST_F格式匹配功能测试失败!")
            print(f"期望: TEST_F >= 2, TEST >= 1")
            print(f"实际: TEST_F = {test_f_count}, TEST = {test_count}")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n已清理临时目录: {temp_dir}")

if __name__ == "__main__":
    test_test_f_matching()