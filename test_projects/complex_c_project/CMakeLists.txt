cmake_minimum_required(VERSION 3.10)
project(complex_c_project VERSION 1.0.0)

# 设置C标准
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# 设置编译选项
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g -O0 -Wall -Wextra -DTEST_MODE_FULL")
else()
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O2")
endif()

# 包含目录
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/data_structures
    ${CMAKE_CURRENT_SOURCE_DIR}/utils
)

# 源文件
set(SOURCES
    main.c
    data_structures/linked_list.c
    data_structures/hash_table.c
    utils/memory_pool.c
)

# 创建可执行文件
add_executable(complex_app ${SOURCES})

# 安装目标
install(TARGETS complex_app DESTINATION bin)

# 测试模式配置
option(ENABLE_FULL_TESTS "Enable full test mode" OFF)
if(ENABLE_FULL_TESTS)
    target_compile_definitions(complex_app PRIVATE TEST_MODE_FULL)
endif()

# 生成 compile_commands.json 用于工具分析
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)