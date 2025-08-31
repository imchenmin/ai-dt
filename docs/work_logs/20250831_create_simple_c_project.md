# 20250831 - 创建简单 C 项目

## 概述

根据用户请求，创建了一个简单的 C 项目，用于演示具有可测试函数和静态函数的代码结构。该项目包含两个 `.c` 文件和一个 `.h` 文件，并使用 CMake 进行构建。

## 完成的任务

1.  **创建项目目录**: 在 `test_projects/` 下创建了 `simple_c_project` 目录。
2.  **创建源文件**:
    *   `utils.h`: 声明了 `process_data` 函数。
    *   `utils.c`: 实现了 `process_data` 函数，该函数内部调用了一个静态函数 `helper_function`。
    *   `main.c`: 调用 `process_data` 函数并打印结果。
3.  **创建构建系统**: 添加了 `CMakeLists.txt` 文件以支持项目编译。
4.  **更新配置**: 在 `config/test_generation.yaml` 中添加了新项目的配置。
5.  **编译和验证**: 成功编译并运行了项目，确认其功能符合预期。

## 文件内容

### `utils.h`

```c
#ifndef UTILS_H
#define UTILS_H

// This is the function that can be tested.
int process_data(int data);

#endif // UTILS_H
```

### `utils.c`

```c
#include "utils.h"
#include <stdio.h>

// This is a static function that cannot be directly tested from outside this file.
static int helper_function(int value) {
    return value * 2;
}

// This is the public function that can be tested.
// It calls the static helper_function.
int process_data(int data) {
    printf("Processing data: %d\n", data);
    return helper_function(data);
}
```

### `main.c`

```c
#include <stdio.h>
#include "utils.h"

int main() {
    int data = 10;
    printf("Calling process_data with: %d\n", data);
    int result = process_data(data);
    printf("Result from process_data: %d\n", result);
    return 0;
}
```

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.10)

project(SimpleCProject C)

# Add the executable
add_executable(simple_c_project main.c utils.c)

# Include the current directory for header files
target_include_directories(simple_c_project PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Generate compile_commands.json
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

## 编译和运行

在 `test_projects/simple_c_project` 目录下执行了以下命令：

1.  `cmake -G "MinGW Makefiles" .`
2.  `mingw32-make`
3.  `.\simple_c_project.exe`

程序成功运行并输出：

```
Calling process_data with: 10
Processing data: 10
Result from process_data: 20
```