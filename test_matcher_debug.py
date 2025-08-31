import sys
sys.path.append('c:\\Users\\chenmin\\ai-dt')

from src.utils.test_file_matcher import TestFileMatcher
import os

# 创建TestFileMatcher实例
project_root = r"c:\Users\chenmin\ai-dt\test_projects\simple_c_project"
test_dir = os.path.join(project_root, "tests")

print(f"项目根目录: {project_root}")
print(f"测试目录: {test_dir}")
print(f"测试目录是否存在: {os.path.exists(test_dir)}")

if os.path.exists(test_dir):
    print(f"测试目录内容: {os.listdir(test_dir)}")

matcher = TestFileMatcher(project_root, test_dir)

# 测试源文件路径
source_file = os.path.join(project_root, "utils.c")
print(f"\n源文件路径: {source_file}")
print(f"源文件是否存在: {os.path.exists(source_file)}")

# 测试find_matching_test_file
test_file = matcher.find_matching_test_file(source_file)
print(f"\n找到的测试文件: {test_file}")

if test_file:
    print(f"测试文件是否存在: {os.path.exists(test_file)}")
    
    # 测试extract_test_functions
    test_functions = matcher.extract_test_functions(test_file)
    print(f"\n提取的测试函数数量: {len(test_functions)}")
    
    for func in test_functions:
        print(f"  - 函数名: {func['name']}")
        print(f"    目标函数: {func['target_function']}")
        print(f"    代码长度: {len(func['code'])} 字符")
        print()
    
    # 测试get_existing_tests_for_function
    existing_tests = matcher.get_existing_tests_for_function(source_file, "process_data")
    print(f"process_data函数的现有测试数量: {len(existing_tests)}")
    
    for test in existing_tests:
        print(f"  - 测试名: {test['name']}")
        print(f"    目标函数: {test['target_function']}")
        print()
    
    # 测试get_test_context_for_function
    context = matcher.get_test_context_for_function("process_data", source_file)
    print(f"测试上下文:")
    print(f"  匹配的测试文件: {context['matched_test_files']}")
    print(f"  现有测试函数数量: {len(context['existing_test_functions'])}")
    print(f"  测试覆盖摘要: {context['test_coverage_summary']}")
else:
    print("未找到匹配的测试文件")