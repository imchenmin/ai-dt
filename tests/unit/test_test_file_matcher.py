"""TestFileMatcher模块的单元测试"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.test_file_matcher import TestFileMatcher


class TestTestFileMatcher(unittest.TestCase):
    """TestFileMatcher类的单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        self.test_dir = self.project_path / "tests"
        self.test_dir.mkdir(exist_ok=True)
        
        # 创建测试文件结构
        self._create_test_structure()
        
        self.matcher = TestFileMatcher("tests", str(self.project_path))
    
    def tearDown(self):
        """测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_structure(self):
        """创建测试文件结构"""
        # 创建源文件
        src_dir = self.project_path / "src"
        src_dir.mkdir(exist_ok=True)
        
        (src_dir / "math_utils.c").touch()
        (src_dir / "math_utils.h").touch()
        (src_dir / "string_utils.cpp").touch()
        (src_dir / "string_utils.hpp").touch()
        
        # 创建测试文件
        (self.test_dir / "math_utils_test.c").touch()
        (self.test_dir / "string_utils_test.cpp").touch()
        (self.test_dir / "test_helper.cpp").touch()  # 这个也会被识别为测试文件
        (self.test_dir / "other_test.cpp").touch()   # 测试文件但不匹配
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.matcher.project_path, self.project_path.resolve())
        self.assertEqual(self.matcher.test_directory, self.test_dir.resolve())
    
    def test_is_test_file(self):
        """测试测试文件识别"""
        # 正确的测试文件
        self.assertTrue(self.matcher._is_test_file("math_utils_test.c"))
        self.assertTrue(self.matcher._is_test_file("string_utils_test.cpp"))
        self.assertTrue(self.matcher._is_test_file("test_math_utils.c"))
        
        # 不是测试文件
        self.assertFalse(self.matcher._is_test_file("math_utils.c"))
        self.assertFalse(self.matcher._is_test_file("helper.cpp"))
        self.assertFalse(self.matcher._is_test_file("test_helper.txt"))
    
    def test_find_test_files(self):
        """测试查找测试文件"""
        test_files = self.matcher.find_test_files()
        
        # 应该找到4个测试文件
        self.assertEqual(len(test_files), 4)  # math_utils_test.c, string_utils_test.cpp, test_helper.cpp, other_test.cpp
        self.assertIn("math_utils_test.c", test_files)
        self.assertIn("string_utils_test.cpp", test_files)
        self.assertIn("test_helper.cpp", test_files)
        self.assertIn("other_test.cpp", test_files)
    
    def test_find_matching_test_file(self):
        """测试查找匹配的测试文件"""
        # 测试C文件匹配
        test_file = self.matcher.find_matching_test_file("src/math_utils.c")
        self.assertIsNotNone(test_file)
        self.assertTrue(test_file.endswith("math_utils_test.c"))
        
        # 测试C++文件匹配
        test_file = self.matcher.find_matching_test_file("src/string_utils.cpp")
        self.assertIsNotNone(test_file)
        self.assertTrue(test_file.endswith("string_utils_test.cpp"))
        
        # 测试头文件匹配（应该找到对应的实现文件的测试）
        test_file = self.matcher.find_matching_test_file("src/math_utils.h")
        self.assertIsNotNone(test_file)
        self.assertTrue(test_file.endswith("math_utils_test.c"))
        
        # 测试不存在的文件
        test_file = self.matcher.find_matching_test_file("src/nonexistent.c")
        self.assertIsNone(test_file)
    
    def test_is_matching_test_file(self):
        """测试测试文件匹配逻辑"""
        # xxx_test 格式
        self.assertTrue(self.matcher._is_matching_test_file("math_utils_test.c", "math_utils"))
        self.assertTrue(self.matcher._is_matching_test_file("string_utils_test.cpp", "string_utils"))
        
        # test_xxx 格式
        self.assertTrue(self.matcher._is_matching_test_file("test_math_utils.c", "math_utils"))
        
        # 不匹配
        self.assertFalse(self.matcher._is_matching_test_file("other_test.c", "math_utils"))
        self.assertFalse(self.matcher._is_matching_test_file("math_utils.c", "math_utils"))
    
    def test_extract_target_function_from_test_name(self):
        """测试从测试名提取目标函数名"""
        # 测试各种命名格式
        self.assertEqual(self.matcher._extract_target_function_from_test_name("test_add"), "add")
        self.assertEqual(self.matcher._extract_target_function_from_test_name("add_test"), "add")
        self.assertEqual(self.matcher._extract_target_function_from_test_name("test_add_basic"), "add")
        self.assertEqual(self.matcher._extract_target_function_from_test_name("add_edge_case"), "add")
        self.assertEqual(self.matcher._extract_target_function_from_test_name("AddNumbers"), "addnumbers")
    
    def test_extract_test_functions(self):
        """测试从测试文件中提取测试函数"""
        # 创建包含测试函数的文件
        test_content = """
#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, TestAdd) {
    EXPECT_EQ(add(2, 3), 5);
}

TEST(MathUtilsTest, TestSubtract) {
    EXPECT_EQ(subtract(5, 3), 2);
}

void test_multiply() {
    assert(multiply(2, 3) == 6);
}
"""
        test_file = self.test_dir / "math_utils_test.cpp"
        test_file.write_text(test_content)
        
        # 提取测试函数
        test_functions = self.matcher.extract_test_functions(str(test_file))
        
        # 应该找到3个测试函数
        self.assertEqual(len(test_functions), 3)
        
        # 检查函数信息
        function_names = [func['name'] for func in test_functions]
        self.assertIn('TEST(MathUtilsTest, TestAdd)', function_names)
        self.assertIn('TEST(MathUtilsTest, TestSubtract)', function_names)
        self.assertIn('test_multiply', function_names)
    
    def test_get_test_context_summary(self):
        """测试获取测试上下文摘要"""
        # 创建一个测试文件内容
        test_content = '''
            TEST(MathUtilsTest, AddBasic) {
                EXPECT_EQ(add(2, 3), 5);
            }
        '''
        
        test_file_path = self.test_dir / "math_utils_test.c"
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # 获取上下文摘要
        summary = self.matcher.get_test_context_summary("src/math_utils.c", "add")
        
        self.assertIsInstance(summary, dict)
        self.assertIn('has_existing_tests', summary)
        self.assertIn('test_file_path', summary)
        self.assertIn('existing_tests', summary)
        self.assertIn('test_count', summary)
    
    def test_nonexistent_test_directory(self):
        """测试不存在的测试目录"""
        matcher = TestFileMatcher("nonexistent", str(self.project_path))
        test_files = matcher.find_test_files()
        self.assertEqual(len(test_files), 0)
    
    def test_find_implementation_files(self):
        """测试查找实现文件"""
        header_path = self.project_path / "src" / "math_utils.h"
        impl_files = self.matcher._find_implementation_files(header_path)
        
        # 应该找到对应的.c文件
        self.assertGreater(len(impl_files), 0)
        impl_names = [f.name for f in impl_files]
        self.assertIn("math_utils.c", impl_names)


if __name__ == '__main__':
    unittest.main()