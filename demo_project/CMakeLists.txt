
cmake_minimum_required(VERSION 3.10)
project(HashTableDemo)

set(CMAKE_C_STANDARD 99)

# 启用测试
enable_testing()

find_package(GTest REQUIRED)

# 查找 GTest
find_package(GTest REQUIRED)

# 添加库
add_library(hash_table src/hash_table.c)

# 包含目录
target_include_directories(hash_table PUBLIC src)

# 创建测试可执行文件
add_executable(test_hash_table tests/test_hash_table.cpp)

# 链接库
target_link_libraries(test_hash_table hash_table GTest::gtest GTest::gtest_main)

# 添加测试
add_test(NAME HashTableTest COMMAND test_hash_table)
