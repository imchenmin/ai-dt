#!/usr/bin/env python3
"""
真实项目测试脚本
测试 Agentic Coding 系统在真实项目场景下的表现
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from agentic_coding import AgenticCodingSystem
from agentic_coding.utils.exceptions import AgenticCodingError

def create_realistic_project():
    """创建一个真实的项目结构"""
    project_dir = Path("realistic_project")

    # 清理旧项目
    if project_dir.exists():
        shutil.rmtree(project_dir)

    # 创建目录结构
    dirs = [
        "src/core",
        "src/utils",
        "src/data_structures",
        "include",
        "tests/unit",
        "tests/integration",
        "lib",
        "docs",
        "scripts",
        "build"
    ]

    for d in dirs:
        (project_dir / d).mkdir(parents=True)

    # 创建一个真实的数据结构库
    # hash.h
    (project_dir / "include" / "hash.h").write_text("""
#ifndef HASH_H
#define HASH_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct hash_table hash_table_t;

// 创建哈希表
hash_table_t* hash_table_create(size_t capacity);

// 销毁哈希表
void hash_table_destroy(hash_table_t* table);

// 插入键值对
bool hash_table_insert(hash_table_t* table, const char* key, void* value);

// 查找值
void* hash_table_get(hash_table_t* table, const char* key);

// 删除键值对
bool hash_table_remove(hash_table_t* table, const char* key);

// 获取大小
size_t hash_table_size(hash_table_t* table);

// 检查是否存在
bool hash_table_contains(hash_table_t* table, const char* key);

// 清空表
void hash_table_clear(hash_table_t* table);

#ifdef __cplusplus
}
#endif

#endif // HASH_H
""")

    # hash.c
    (project_dir / "src" / "hash.c").write_text("""
#include "hash.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define HASH_TABLE_DEFAULT_LOAD_FACTOR 0.75

typedef struct entry {
    char* key;
    void* value;
    struct entry* next;
} entry_t;

struct hash_table {
    size_t capacity;
    size_t size;
    entry_t** buckets;
    size_t (*hash_func)(const char*);
    bool (*key_equal)(const char*, const char*);
};

// djb2 hash algorithm
static size_t default_hash_func(const char* str) {
    unsigned long hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c;
    }
    return hash;
}

static bool default_key_equal(const char* a, const char* b) {
    return strcmp(a, b) == 0;
}

hash_table_t* hash_table_create(size_t capacity) {
    if (capacity == 0) {
        capacity = 16;
    }

    hash_table_t* table = malloc(sizeof(hash_table_t));
    if (!table) return NULL;

    table->buckets = calloc(capacity, sizeof(entry_t*));
    if (!table->buckets) {
        free(table);
        return NULL;
    }

    table->capacity = capacity;
    table->size = 0;
    table->hash_func = default_hash_func;
    table->key_equal = default_key_equal;

    return table;
}

void hash_table_destroy(hash_table_t* table) {
    if (!table) return;

    for (size_t i = 0; i < table->capacity; i++) {
        entry_t* entry = table->buckets[i];
        while (entry) {
            entry_t* next = entry->next;
            free(entry->key);
            free(entry);
            entry = next;
        }
    }

    free(table->buckets);
    free(table);
}

static entry_t* create_entry(const char* key, void* value) {
    entry_t* entry = malloc(sizeof(entry_t));
    if (!entry) return NULL;

    entry->key = malloc(strlen(key) + 1);
    if (!entry->key) {
        free(entry);
        return NULL;
    }

    strcpy(entry->key, key);
    entry->value = value;
    entry->next = NULL;

    return entry;
}

bool hash_table_insert(hash_table_t* table, const char* key, void* value) {
    if (!table || !key) return false;

    // 检查是否需要扩容
    if ((double)table->size / table->capacity > HASH_TABLE_DEFAULT_LOAD_FACTOR) {
        // 简化：不实现扩容
    }

    size_t index = table->hash_func(key) % table->capacity;
    entry_t* entry = table->buckets[index];

    // 检查是否已存在
    while (entry) {
        if (table->key_equal(entry->key, key)) {
            entry->value = value;
            return true;
        }
        entry = entry->next;
    }

    // 创建新条目
    entry_t* new_entry = create_entry(key, value);
    if (!new_entry) return false;

    new_entry->next = table->buckets[index];
    table->buckets[index] = new_entry;
    table->size++;

    return true;
}

void* hash_table_get(hash_table_t* table, const char* key) {
    if (!table || !key) return NULL;

    size_t index = table->hash_func(key) % table->capacity;
    entry_t* entry = table->buckets[index];

    while (entry) {
        if (table->key_equal(entry->key, key)) {
            return entry->value;
        }
        entry = entry->next;
    }

    return NULL;
}

bool hash_table_remove(hash_table_t* table, const char* key) {
    if (!table || !key) return false;

    size_t index = table->hash_func(key) % table->capacity;
    entry_t* entry = table->buckets[index];
    entry_t* prev = NULL;

    while (entry) {
        if (table->key_equal(entry->key, key)) {
            if (prev) {
                prev->next = entry->next;
            } else {
                table->buckets[index] = entry->next;
            }

            free(entry->key);
            free(entry);
            table->size--;
            return true;
        }
        prev = entry;
        entry = entry->next;
    }

    return false;
}

size_t hash_table_size(hash_table_t* table) {
    return table ? table->size : 0;
}

bool hash_table_contains(hash_table_t* table, const char* key) {
    return hash_table_get(table, key) != NULL;
}

void hash_table_clear(hash_table_t* table) {
    if (!table) return;

    for (size_t i = 0; i < table->capacity; i++) {
        entry_t* entry = table->buckets[i];
        while (entry) {
            entry_t* next = entry->next;
            free(entry->key);
            free(entry);
            entry = next;
        }
        table->buckets[i] = NULL;
    }

    table->size = 0;
}
""")

    # 创建 list.h
    (project_dir / "include" / "list.h").write_text("""
#ifndef LIST_H
#define LIST_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct list list_t;
typedef struct list_node list_node_t;

// 创建列表
list_t* list_create(void);

// 销毁列表
void list_destroy(list_t* list);

// 添加元素到头部
bool list_push_front(list_t* list, void* data);

// 添加元素到尾部
bool list_push_back(list_t* list, void* data);

// 移除头部元素
void* list_pop_front(list_t* list);

// 移除尾部元素
void* list_pop_back(list_t* list);

// 获取列表大小
size_t list_size(list_t* list);

// 检查是否为空
bool list_empty(list_t* list);

// 清空列表
void list_clear(list_t* list);

#ifdef __cplusplus
}
#endif

#endif // LIST_H
""")

    # list.c
    (project_dir / "src" / "list.c").write_text("""
#include "list.h"
#include <stdlib.h>

struct list_node {
    void* data;
    struct list_node* next;
    struct list_node* prev;
};

struct list {
    list_node_t* head;
    list_node_t* tail;
    size_t size;
};

list_t* list_create(void) {
    list_t* list = malloc(sizeof(list_t));
    if (!list) return NULL;

    list->head = NULL;
    list->tail = NULL;
    list->size = 0;

    return list;
}

void list_destroy(list_t* list) {
    if (!list) return;

    list_clear(list);
    free(list);
}

static list_node_t* create_node(void* data) {
    list_node_t* node = malloc(sizeof(list_node_t));
    if (!node) return NULL;

    node->data = data;
    node->next = NULL;
    node->prev = NULL;

    return node;
}

bool list_push_front(list_t* list, void* data) {
    if (!list) return false;

    list_node_t* node = create_node(data);
    if (!node) return false;

    node->next = list->head;
    node->prev = NULL;

    if (list->head) {
        list->head->prev = node;
    } else {
        list->tail = node;
    }

    list->head = node;
    list->size++;

    return true;
}

bool list_push_back(list_t* list, void* data) {
    if (!list) return false;

    list_node_t* node = create_node(data);
    if (!node) return false;

    node->prev = list->tail;
    node->next = NULL;

    if (list->tail) {
        list->tail->next = node;
    } else {
        list->head = node;
    }

    list->tail = node;
    list->size++;

    return true;
}

void* list_pop_front(list_t* list) {
    if (!list || !list->head) return NULL;

    list_node_t* node = list->head;
    void* data = node->data;

    list->head = node->next;
    if (list->head) {
        list->head->prev = NULL;
    } else {
        list->tail = NULL;
    }

    free(node);
    list->size--;

    return data;
}

void* list_pop_back(list_t* list) {
    if (!list || !list->tail) return NULL;

    list_node_t* node = list->tail;
    void* data = node->data;

    list->tail = node->prev;
    if (list->tail) {
        list->tail->next = NULL;
    } else {
        list->head = NULL;
    }

    free(node);
    list->size--;

    return data;
}

size_t list_size(list_t* list) {
    return list ? list->size : 0;
}

bool list_empty(list_t* list) {
    return list ? list->size == 0 : true;
}

void list_clear(list_t* list) {
    if (!list) return;

    while (list->head) {
        list_pop_front(list);
    }
}
""")

    # 创建 CMakeLists.txt
    (project_dir / "CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.10)
project(DataStructures VERSION 1.0.0 LANGUAGES C CXX)

# 设置 C 标准
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 包含目录
include_directories(include)

# 查找依赖
find_package(PkgConfig REQUIRED)
pkg_check_modules(GTEST REQUIRED gtest_main)

# 创建库
add_library(datastructures STATIC
    src/hash.c
    src/list.c
)

# 设置库属性
set_target_properties(datastructures PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    PUBLIC_HEADER "include/hash.h;include/list.h"
)

# 安装规则
install(TARGETS datastructures
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    PUBLIC_HEADER DESTINATION include
)

# 启用测试
enable_testing()

# 测试可执行文件
add_executable(test_hash tests/unit/test_hash.cpp)
add_executable(test_list tests/unit/test_list.cpp)
add_executable(test_integration tests/integration/test_main.cpp)

# 链接库
target_link_libraries(test_hash datastructures ${GTEST_LIBRARIES})
target_link_libraries(test_list datastructures ${GTEST_LIBRARIES})
target_link_libraries(test_integration datastructures ${GTEST_LIBRARIES})

# 添加测试
add_test(NAME HashTest COMMAND test_hash)
add_test(NAME ListTest COMMAND test_list)
add_test(NAME IntegrationTest COMMAND test_integration)
""")

    # 创建一些初始测试文件
    (project_dir / "tests" / "unit" / "test_hash.cpp").write_text("""
#include <gtest/gtest.h>
#include <hash.h>

class HashTest : public ::testing::Test {
protected:
    void SetUp() override {
        table = hash_table_create(10);
    }

    void TearDown() override {
        hash_table_destroy(table);
    }

    hash_table_t* table;
};

TEST_F(HashTest, CreateTable) {
    EXPECT_NE(table, nullptr);
    EXPECT_EQ(hash_table_size(table), 0);
}

TEST_F(HashTest, InsertAndGet) {
    int value = 42;
    EXPECT_TRUE(hash_table_insert(table, "key", &value));

    int* retrieved = (int*)hash_table_get(table, "key");
    EXPECT_NE(retrieved, nullptr);
    EXPECT_EQ(*retrieved, 42);
}
""")

    (project_dir / "tests" / "unit" / "test_list.cpp").write_text("""
#include <gtest/gtest.h>
#include <list.h>

class ListTest : public ::testing::Test {
protected:
    void SetUp() override {
        list = list_create();
    }

    void TearDown() override {
        list_destroy(list);
    }

    list_t* list;
};

TEST_F(ListTest, CreateList) {
    EXPECT_NE(list, nullptr);
    EXPECT_TRUE(list_empty(list));
    EXPECT_EQ(list_size(list), 0);
}
""")

    # 创建一个复杂的使用示例
    (project_dir / "src" / "cache.c").write_text("""
#include "hash.h"
#include "list.h"
#include <stdio.h>
#include <time.h>

typedef struct {
    char* key;
    void* value;
    time_t timestamp;
    int access_count;
} cache_entry_t;

typedef struct {
    hash_table_t* table;
    list_t* lru_list;
    size_t max_size;
} lru_cache_t;

lru_cache_t* lru_cache_create(size_t max_size) {
    lru_cache_t* cache = malloc(sizeof(lru_cache_t));
    if (!cache) return NULL;

    cache->table = hash_table_create(max_size * 2);
    if (!cache->table) {
        free(cache);
        return NULL;
    }

    cache->lru_list = list_create();
    if (!cache->lru_list) {
        hash_table_destroy(cache->table);
        free(cache);
        return NULL;
    }

    cache->max_size = max_size;
    return cache;
}

void lru_cache_destroy(lru_cache_t* cache) {
    if (!cache) return;

    // 清理所有条目
    // ... 实现省略

    hash_table_destroy(cache->table);
    list_destroy(cache->lru_list);
    free(cache);
}

bool lru_cache_put(lru_cache_t* cache, const char* key, void* value) {
    if (!cache || !key) return false;

    // 检查是否已存在
    cache_entry_t* entry = (cache_entry_t*)hash_table_get(cache->table, key);
    if (entry) {
        entry->value = value;
        entry->timestamp = time(NULL);
        entry->access_count++;
        return true;
    }

    // 检查是否需要驱逐
    if (hash_table_size(cache->table) >= cache->max_size) {
        // 简化：不实现 LRU 驱逐
        return false;
    }

    // 创建新条目
    entry = malloc(sizeof(cache_entry_t));
    if (!entry) return false;

    entry->key = malloc(strlen(key) + 1);
    if (!entry->key) {
        free(entry);
        return false;
    }

    strcpy(entry->key, key);
    entry->value = value;
    entry->timestamp = time(NULL);
    entry->access_count = 1;

    if (!hash_table_insert(cache->table, key, entry)) {
        free(entry->key);
        free(entry);
        return false;
    }

    return true;
}

void* lru_cache_get(lru_cache_t* cache, const char* key) {
    if (!cache || !key) return NULL;

    cache_entry_t* entry = (cache_entry_t*)hash_table_get(cache->table, key);
    if (entry) {
        entry->timestamp = time(NULL);
        entry->access_count++;
        return entry->value;
    }

    return NULL;
}
""")

    (project_dir / "include" / "cache.h").write_text("""
#ifndef CACHE_H
#define CACHE_H

#include "hash.h"
#include "list.h"
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct lru_cache lru_cache_t;

lru_cache_t* lru_cache_create(size_t max_size);
void lru_cache_destroy(lru_cache_t* cache);
bool lru_cache_put(lru_cache_t* cache, const char* key, void* value);
void* lru_cache_get(lru_cache_t* cache, const char* key);
size_t lru_cache_size(lru_cache_t* cache);

#ifdef __cplusplus
}
#endif

#endif // CACHE_H
""")

    # 创建一个 AI 生成的测试文件
    (project_dir / "generated_tests").mkdir()
    (project_dir / "generated_tests" / "test_cache_generated.cpp").write_text("""
#include <gtest/gtest.h>
#include <cache.h>

// **TARGET_FUNCTION**: lru_cache_create

TEST(LRUCacheTest, CreateCache) {
    const size_t max_size = 10;
    lru_cache_t* cache = lru_cache_create(max_size);

    ASSERT_NE(cache, nullptr);

    // 清理
    lru_cache_destroy(cache);
}

// **TARGET_FUNCTION**: lru_cache_put

TEST(LRUCacheTest, PutAndGet) {
    const size_t max_size = 10;
    lru_cache_t* cache = lru_cache_create(max_size);
    ASSERT_NE(cache, nullptr);

    // 插入值
    int value = 42;
    EXPECT_TRUE(lru_cache_put(cache, "test_key", &value));

    // 获取值
    int* retrieved = (int*)lru_cache_get(cache, "test_key");
    ASSERT_NE(retrieved, nullptr);
    EXPECT_EQ(*retrieved, 42);

    // 清理
    lru_cache_destroy(cache);
}

// **TARGET_FUNCTION**: lru_cache_get

TEST(LRUCacheTest, GetNonExistent) {
    const size_t max_size = 10;
    lru_cache_t* cache = lru_cache_create(max_size);
    ASSERT_NE(cache, nullptr);

    // 获取不存在的键
    void* result = lru_cache_get(cache, "non_existent");
    EXPECT_EQ(result, nullptr);

    // 清理
    lru_cache_destroy(cache);
}

// **TARGET_FUNCTION**: lru_cache_size (通过 hash_table_size)

TEST(LRUCacheTest, CacheSize) {
    const size_t max_size = 10;
    lru_cache_t* cache = lru_cache_create(max_size);
    ASSERT_NE(cache, nullptr);

    // 初始大小应该是 0
    EXPECT_EQ(lru_cache_size(cache), 0);

    // 插入一些值
    int values[] = {1, 2, 3};
    EXPECT_TRUE(lru_cache_put(cache, "key1", &values[0]));
    EXPECT_TRUE(lru_cache_put(cache, "key2", &values[1]));
    EXPECT_TRUE(lru_cache_put(cache, "key3", &values[2]));

    // 大小应该增加
    EXPECT_EQ(lru_cache_size(cache), 3);

    // 清理
    lru_cache_destroy(cache);
}

// 测试边界情况
TEST(LRUCacheTest, PutNullKey) {
    const size_t max_size = 10;
    lru_cache_t* cache = lru_cache_create(max_size);
    ASSERT_NE(cache, nullptr);

    // 尝试插入空键
    int value = 42;
    EXPECT_FALSE(lru_cache_put(cache, NULL, &value));

    // 清理
    lru_cache_destroy(cache);
}

// 测试覆写现有值
TEST(LRUCacheTest, OverwriteValue) {
    const size_t max_size = 10;
    lru_cache_t* cache = lru_cache_create(max_size);
    ASSERT_NE(cache, nullptr);

    // 插入初始值
    int value1 = 42;
    EXPECT_TRUE(lru_cache_put(cache, "test_key", &value1));

    // 获取并验证
    int* retrieved = (int*)lru_cache_get(cache, "test_key");
    ASSERT_NE(retrieved, nullptr);
    EXPECT_EQ(*retrieved, 42);

    // 覆写值
    int value2 = 100;
    EXPECT_TRUE(lru_cache_put(cache, "test_key", &value2));

    // 获取新值
    retrieved = (int*)lru_cache_get(cache, "test_key");
    ASSERT_NE(retrieved, nullptr);
    EXPECT_EQ(*retrieved, 100);

    // 大小应该仍然是 1
    EXPECT_EQ(lru_cache_size(cache), 1);

    // 清理
    lru_cache_destroy(cache);
}
""")

    # 创建 README
    (project_dir / "README.md").write_text("""# Realistic Data Structures Library

A simple but functional implementation of common data structures in C.

## Features

- Hash Table with chaining
- Doubly Linked List
- LRU Cache (built on top of Hash Table and List)
- Unit tests with Google Test
- CMake build system

## Building

```bash
mkdir build
cd build
cmake ..
make
```

## Running Tests

```bash
ctest --output-on-failure
```

## Usage

```c
#include "hash.h"
#include "cache.h"

int main() {
    // Create hash table
    hash_table_t* table = hash_table_create(100);

    // Insert value
    int value = 42;
    hash_table_insert(table, "key", &value);

    // Get value
    int* retrieved = (int*)hash_table_get(table, "key");

    // Clean up
    hash_table_destroy(table);
    return 0;
}
```
""")

    # 创建 .gitignore
    (project_dir / ".gitignore").write_text("""# Build directories
build/
cmake-build-*/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Generated files
*.o
*.a
*.so
*.dylib
*.exe

# Test outputs
test_results/
coverage/
""")

    return project_dir


def run_realistic_test():
    """运行真实项目测试"""
    print("🚀 真实项目测试开始")
    print("=" * 70)

    # 创建项目
    print("\n📁 创建真实项目结构...")
    project_dir = create_realistic_project()
    print(f"✅ 项目创建于: {project_dir.absolute()}")

    # 初始化 Git
    print("\n📦 初始化 Git 仓库...")
    subprocess.run(f"cd {project_dir} && git init -q", shell=True)
    subprocess.run(f"cd {project_dir} && git config user.email 'test@example.com'", shell=True)
    subprocess.run(f"cd {project_dir} && git config user.name 'Test User'", shell=True)
    subprocess.run(f"cd {project_dir} && git add .", shell=True)
    subprocess.run(f"cd {project_dir} && git commit -m 'Initial commit' -q", shell=True)

    # 配置 Agentic Coding 系统
    print("\n⚙️ 配置 Agentic Coding 系统...")
    config = {
        'project_root': str(project_dir.absolute()),
        'source_dir': 'src',
        'test_dir': 'tests',
        'build_dir': 'build',
        'backup_method': 'git',
        'run_tests': True,
        'log_level': 'INFO',
        'compilation_timeout': 120
    }

    # 运行系统
    print("\n🔧 运行 Agentic Coding 系统...")
    print("-" * 70)

    try:
        from agentic_coding import AgenticCodingSystem
        system = AgenticCodingSystem(config)

        # 运行测试插入
        result = system.run({
            **config,
            'test_files': [str(project_dir / 'generated_tests' / 'test_cache_generated.cpp')]
        })

        # 打印结果
        print("\n📊 执行结果:")
        print(f"  成功: {'✅' if result.success else '❌'}")
        print(f"  执行时间: {result.execution_time:.2f} 秒")
        print(f"  插入的测试: {len(result.inserted_tests)}")
        print(f"  失败的测试: {len(result.failed_insertions)}")

        if result.inserted_tests:
            print("\n✅ 成功插入的测试:")
            for test in result.inserted_tests:
                print(f"  - {test['test_name']}")

        if result.errors:
            print("\n❌ 错误:")
            for error in result.errors:
                print(f"  - {error}")

        # 验证编译和运行
        print("\n🔨 验证编译...")
        build_result = subprocess.run(
            f"cd {project_dir} && mkdir -p build && cmake -S . -B build && cmake --build build",
            shell=True,
            capture_output=True,
            text=True
        )

        if build_result.returncode == 0:
            print("✅ 编译成功")

            # 运行测试
            print("\n🧪 运行所有测试...")
            test_result = subprocess.run(
                f"cd {project_dir}/build && ctest --output-on-failure",
                shell=True,
                capture_output=True,
                text=True
            )

            if test_result.returncode == 0:
                print("✅ 所有测试通过！")

                # 显示测试输出
                if "tests passed" in test_result.stdout:
                    import re
                    match = re.search(r'(\d+)\s+test', test_result.stdout)
                    if match:
                        print(f"  总共运行了 {match.group(1)} 个测试")
            else:
                print("⚠️ 部分测试失败")
                print(test_result.stdout[-500:])
        else:
            print("❌ 编译失败")
            print(build_result.stderr[-500:])

    except Exception as e:
        print(f"\n❌ 系统运行出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("测试完成！")
    print(f"\n📁 项目位于: {project_dir.absolute()}")
    print("\n手动验证命令:")
    print(f"  cd {project_dir}")
    print("  mkdir -p build && cmake -S . -B build")
    print("  cmake --build build")
    print("  cd build && ctest")

    # 保存测试报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'project_path': str(project_dir.absolute()),
        'status': 'completed',
        'config': config
    }

    with open('realistic_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 测试报告已保存到: realistic_test_report.json")


if __name__ == "__main__":
    run_realistic_test()