def extract_target_function_from_test_name(test_name: str) -> str:
    """
    从测试函数名中提取被测函数名
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

# 测试用例
test_names = [
    'process_data_When_PositiveInput_Should_ReturnDouble',
    'test_process_data',
    'process_data_test',
    'process_data_basic'
]

for test_name in test_names:
    result = extract_target_function_from_test_name(test_name)
    print(f"测试名称: {test_name} -> 提取的函数名: {result}")