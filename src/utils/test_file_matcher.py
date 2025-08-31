"""测试文件搜索和匹配功能模块

该模块负责：
1. 在指定目录中搜索现有的测试文件
2. 根据命名规范匹配待测文件和测试文件
3. 解析测试文件中的测试用例，识别已有的测试函数
4. 支持C/C++头文件与实现文件的匹配逻辑
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

from src.utils.logging_utils import get_logger
from src.utils.error_handler import with_error_handling

logger = get_logger(__name__)


class TestFileMatcher:
    """测试文件匹配器"""
    
    def __init__(self, test_directory: str, project_path: str = "."):
        """
        初始化测试文件匹配器
        
        Args:
            test_directory: 测试文件目录路径（可以是绝对路径或相对于项目路径的相对路径）
            project_path: 项目根路径
        """
        self.project_path = Path(project_path).resolve()
        
        # 处理测试目录路径：如果是绝对路径则直接使用，否则相对于项目路径
        test_dir_path = Path(test_directory)
        if test_dir_path.is_absolute():
            self.test_directory = test_dir_path
        else:
            self.test_directory = self.project_path / test_directory
        
        # 支持的源文件扩展名
        self.source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.c++'}
        # 支持的头文件扩展名
        self.header_extensions = {'.h', '.hpp', '.hh', '.hxx', '.h++'}
        # 支持的测试文件扩展名
        self.test_extensions = {'.c', '.cpp', '.cc', '.cxx', '.c++'}
        
        logger.info(f"初始化测试文件匹配器: 项目路径={self.project_path}, 测试目录={self.test_directory}")
    
    @with_error_handling(context="搜索测试文件", critical=False)
    def find_test_files(self) -> Dict[str, str]:
        """
        搜索测试目录中的所有测试文件
        
        Returns:
            Dict[str, str]: 测试文件名 -> 完整路径的映射
        """
        if not self.test_directory.exists():
            logger.warning(f"测试目录不存在: {self.test_directory}")
            return {}
        
        test_files = {}
        
        for root, dirs, files in os.walk(self.test_directory):
            for file in files:
                if self._is_test_file(file):
                    file_path = Path(root) / file
                    test_files[file] = str(file_path)
        
        logger.info(f"找到 {len(test_files)} 个测试文件")
        return test_files
    
    def _is_test_file(self, filename: str) -> bool:
        """
        判断文件是否为测试文件
        
        支持的命名规范：
        - xxx_test.cpp
        - xxx_test.c
        - test_xxx.cpp (可选支持)
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否为测试文件
        """
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if extension not in self.test_extensions:
            return False
        
        name = file_path.stem.lower()
        
        # 支持 xxx_test 命名规范
        if name.endswith('_test'):
            return True
        
        # 可选支持 test_xxx 命名规范
        if name.startswith('test_'):
            return True
        
        return False
    
    @with_error_handling(context="匹配测试文件", critical=False)
    def find_matching_test_file(self, source_file_path: str) -> Optional[str]:
        """
        为给定的源文件查找匹配的测试文件
        
        Args:
            source_file_path: 源文件路径（相对于项目根目录或绝对路径）
            
        Returns:
            Optional[str]: 匹配的测试文件路径，如果没有找到则返回None
        """
        source_path = Path(source_file_path)
        
        # 如果是相对路径，转换为相对于项目根目录的路径
        if not source_path.is_absolute():
            source_path = self.project_path / source_path
        
        # 获取源文件的基本信息
        source_name = source_path.stem
        source_extension = source_path.suffix.lower()
        
        # 处理头文件：查找对应的实现文件
        if source_extension in self.header_extensions:
            impl_candidates = self._find_implementation_files(source_path)
            for impl_file in impl_candidates:
                test_file = self._find_test_file_for_source(impl_file)
                if test_file:
                    return test_file
        
        # 直接查找源文件对应的测试文件
        return self._find_test_file_for_source(source_path)
    
    def _find_implementation_files(self, header_path: Path) -> List[Path]:
        """
        为头文件查找对应的实现文件
        
        Args:
            header_path: 头文件路径
            
        Returns:
            List[Path]: 可能的实现文件路径列表
        """
        header_name = header_path.stem
        header_dir = header_path.parent
        
        candidates = []
        
        # 在同一目录下查找
        for ext in self.source_extensions:
            impl_path = header_dir / f"{header_name}{ext}"
            if impl_path.exists():
                candidates.append(impl_path)
        
        # 在项目中递归查找同名的实现文件
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                file_path = Path(root) / file
                if (file_path.stem == header_name and 
                    file_path.suffix.lower() in self.source_extensions and
                    file_path not in candidates):
                    candidates.append(file_path)
        
        return candidates
    
    def _find_test_file_for_source(self, source_path: Path) -> Optional[str]:
        """
        为源文件查找对应的测试文件
        
        Args:
            source_path: 源文件路径
            
        Returns:
            Optional[str]: 测试文件路径，如果没有找到则返回None
        """
        source_name = source_path.stem
        
        # 查找 xxx_test.cpp 格式的测试文件
        for ext in self.test_extensions:
            test_filename = f"{source_name}_test{ext}"
            test_path = self.test_directory / test_filename
            
            if test_path.exists():
                return str(test_path)
        
        # 递归查找测试目录中的匹配文件
        for root, dirs, files in os.walk(self.test_directory):
            for file in files:
                if self._is_matching_test_file(file, source_name):
                    return str(Path(root) / file)
        
        return None
    
    def _is_matching_test_file(self, test_filename: str, source_name: str) -> bool:
        """
        判断测试文件是否匹配源文件
        
        Args:
            test_filename: 测试文件名
            source_name: 源文件名（不含扩展名）
            
        Returns:
            bool: 是否匹配
        """
        test_path = Path(test_filename)
        test_name = test_path.stem.lower()
        source_name_lower = source_name.lower()
        
        # xxx_test 格式
        if test_name == f"{source_name_lower}_test":
            return True
        
        # test_xxx 格式
        if test_name == f"test_{source_name_lower}":
            return True
        
        return False
    
    @with_error_handling(context="解析测试函数", critical=False)
    def extract_test_functions(self, test_file_path: str) -> List[Dict[str, str]]:
        """
        从测试文件中提取测试函数信息
        
        Args:
            test_file_path: 测试文件路径
            
        Returns:
            List[Dict[str, str]]: 测试函数信息列表，每个字典包含:
                - name: 测试函数名
                - target_function: 被测函数名（从测试函数名推断）
                - code: 测试函数代码
        """
        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取测试文件失败 {test_file_path}: {e}")
            return []
        
        test_functions = []
        
        # 匹配测试函数的正则表达式
        # 支持 Google Test 格式: TEST(TestSuite, TestName) 和 TEST_F(TestFixture, TestName)
        # 支持普通函数格式: void test_function_name()
        patterns = [
            # Google Test 格式 - 简化版本，匹配到函数体开始
            r'TEST\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            r'TEST_F\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
            # 普通函数格式
            r'(?:void|int)\s+(test_\w+)\s*\([^)]*\)'
        ]
        
        # 先处理Google Test格式 (TEST)
        gtest_pattern = r'TEST\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        gtest_matches = re.finditer(gtest_pattern, content, re.MULTILINE | re.DOTALL)
        for match in gtest_matches:
            test_suite = match.group(1).strip()
            test_name = match.group(2).strip()
            full_name = f"TEST({test_suite}, {test_name})"
            target_function = self._extract_target_function_from_test_name(test_name)
            test_code = self._extract_function_body(content, match.end())
            
            test_functions.append({
                'name': full_name,
                'target_function': target_function,
                'code': test_code
            })
        
        # 处理Google Test Fixture格式 (TEST_F)
        gtest_f_pattern = r'TEST_F\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        gtest_f_matches = re.finditer(gtest_f_pattern, content, re.MULTILINE | re.DOTALL)
        for match in gtest_f_matches:
            test_fixture = match.group(1).strip()
            test_name = match.group(2).strip()
            full_name = f"TEST_F({test_fixture}, {test_name})"
            target_function = self._extract_target_function_from_test_name(test_name)
            test_code = self._extract_function_body(content, match.end())
            
            test_functions.append({
                'name': full_name,
                'target_function': target_function,
                'code': test_code
            })
        
        # 再处理普通函数格式
        func_pattern = r'(?:void|int)\s+(test_\w+)\s*\([^)]*\)'
        func_matches = re.finditer(func_pattern, content, re.MULTILINE | re.DOTALL)
        for match in func_matches:
            full_name = match.group(1).strip()
            target_function = self._extract_target_function_from_test_name(full_name)
            test_code = self._extract_function_body(content, match.end())
            
            test_functions.append({
                'name': full_name,
                'target_function': target_function,
                'code': test_code
            })
        
        logger.info(f"从 {test_file_path} 中提取到 {len(test_functions)} 个测试函数")
        return test_functions
    
    def _extract_function_body(self, content: str, start_pos: int) -> str:
        """
        从指定位置开始提取函数体内容
        
        Args:
            content: 文件内容
            start_pos: 开始位置
            
        Returns:
            str: 函数体内容
        """
        # 查找第一个 {
        brace_start = content.find('{', start_pos)
        if brace_start == -1:
            return ""
        
        # 计算匹配的 }
        brace_count = 1
        pos = brace_start + 1
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count == 0:
            return content[brace_start + 1:pos - 1].strip()
        else:
            return content[brace_start + 1:].strip()
    
    def _extract_target_function_from_test_name(self, test_name: str) -> str:
        """
        从测试函数名中提取被测函数名
        
        Args:
            test_name: 测试函数名
            
        Returns:
            str: 被测函数名
        """
        # 移除常见的测试前缀和后缀
        name = test_name.lower()
        
        # 移除 test_ 前缀
        if name.startswith('test_'):
            name = name[5:]
        
        # 移除 _test 后缀
        if name.endswith('_test'):
            name = name[:-5]
        
        # 处理 BDD 风格的测试名称 (如: function_When_Condition_Should_Result)
        # 提取第一个 '_when' 或 '_should' 之前的部分
        bdd_keywords = ['_when', '_should', '_given', '_then']
        for keyword in bdd_keywords:
            if keyword in name:
                name = name.split(keyword)[0]
                break
        
        # 移除常见的测试后缀
        suffixes = ['_basic', '_simple', '_complex', '_edge_case', '_error', '_null', '_invalid']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        return name
    
    def get_existing_tests_for_function(self, source_file_path: str, function_name: str) -> List[Dict[str, str]]:
        """
        获取指定函数的现有测试用例
        
        Args:
            source_file_path: 源文件路径
            function_name: 函数名
            
        Returns:
            List[Dict[str, str]]: 相关的测试用例列表
        """
        test_file = self.find_matching_test_file(source_file_path)
        if not test_file:
            return []
        
        all_tests = self.extract_test_functions(test_file)
        
        # 过滤出与指定函数相关的测试
        related_tests = []
        function_name_lower = function_name.lower()
        
        for test in all_tests:
            target_func = test['target_function'].lower()
            test_name_lower = test['name'].lower()
            
            # 检查是否匹配
            if (target_func == function_name_lower or 
                function_name_lower in test_name_lower or
                target_func in function_name_lower):
                related_tests.append(test)
        
        return related_tests
    
    def get_test_context_summary(self, source_file_path: str, function_name: str) -> Dict[str, any]:
        """
        获取测试上下文摘要信息
        
        Args:
            source_file_path: 源文件路径
            function_name: 函数名
            
        Returns:
            Dict[str, any]: 测试上下文摘要，包含:
                - has_existing_tests: 是否有现有测试
                - test_file_path: 测试文件路径
                - existing_tests: 现有测试列表
                - test_count: 测试数量
        """
        existing_tests = self.get_existing_tests_for_function(source_file_path, function_name)
        test_file = self.find_matching_test_file(source_file_path)
        
        return {
            'has_existing_tests': len(existing_tests) > 0,
            'test_file_path': test_file,
            'existing_tests': existing_tests,
            'test_count': len(existing_tests)
        }
    
    def get_test_context_for_function(self, function_name: str, source_file: str) -> Dict[str, Any]:
        """
        Get existing test context for a function
        
        Args:
            function_name: Name of the function to get test context for
            source_file: Path to the source file containing the function
            
        Returns:
            Dictionary containing test context information
        """
        test_file = self.find_matching_test_file(source_file)
        existing_tests = self.get_existing_tests_for_function(source_file, function_name)
        
        return {
            'matched_test_files': [test_file] if test_file else [],
            'existing_test_functions': existing_tests,
            'test_coverage_summary': f"Found {len(existing_tests)} existing tests in {1 if test_file else 0} test files"
        }