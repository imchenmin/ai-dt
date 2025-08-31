#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.utils.config_manager import ConfigManager
from src.utils.test_file_matcher import TestFileMatcher
from pathlib import Path

def main():
    # 加载实际配置
    config_manager = ConfigManager()
    project_config = config_manager.get_project_config('simple_c_project')
    
    print(f"项目配置: {project_config}")
    print(f"项目根目录: {project_config['path']}")
    print(f"单元测试目录配置: {project_config.get('unit_test_directory_path')}")
    
    # 使用实际配置创建TestFileMatcher
    project_root = project_config['path']
    unit_test_dir = project_config.get('unit_test_directory_path')
    
    if unit_test_dir:
        print(f"\n路径调试信息:")
        print(f"  当前工作目录: {os.getcwd()}")
        print(f"  项目根目录(原始): {project_root}")
        print(f"  项目根目录(绝对): {os.path.abspath(project_root)}")
        print(f"  单元测试目录(原始): {unit_test_dir}")
        print(f"  单元测试目录(绝对): {os.path.abspath(unit_test_dir)}")
        
        test_matcher = TestFileMatcher(unit_test_dir, project_root)
        print(f"\n使用TestFileMatcher:")
        print(f"  TestFileMatcher.project_path: {test_matcher.project_path}")
        print(f"  TestFileMatcher.test_directory: {test_matcher.test_directory}")
        print(f"  测试目录是否存在: {test_matcher.test_directory.exists()}")
        
        if test_matcher.test_directory.exists():
            test_files = test_matcher.find_test_files()
            print(f"  找到的测试文件: {test_files}")
        
        # 测试process_data函数
        source_file = os.path.join(project_root, 'utils.c')
        print(f"\n源文件: {source_file}")
        print(f"源文件是否存在: {os.path.exists(source_file)}")
        
        try:
            test_context = test_matcher.get_test_context_for_function('process_data', source_file)
            print(f"\n测试上下文:")
            print(f"  匹配的测试文件: {test_context.get('matched_test_files', [])}")
            print(f"  现有测试函数数量: {len(test_context.get('existing_test_functions', []))}")
            print(f"  测试覆盖摘要: {test_context.get('test_coverage_summary', 'N/A')}")
            
            if test_context.get('existing_test_functions'):
                print(f"\n现有测试函数详情:")
                for i, test_func in enumerate(test_context['existing_test_functions']):
                    print(f"  {i+1}. {test_func['name']}")
                    print(f"     目标函数: {test_func.get('target_function', 'N/A')}")
                    print(f"     代码长度: {len(test_func.get('code', ''))} 字符")
        except Exception as e:
            print(f"获取测试上下文时出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("配置中未指定单元测试目录")

if __name__ == '__main__':
    main()