#!/usr/bin/env python3
"""
Agentic Coding 演示脚本
演示如何使用 Agentic Coding 系统插入和编译测试
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

# 添加项目到路径
sys.path.insert(0, str(Path(__file__).parent))

from agentic_coding import AgenticCodingSystem

def create_demo_project():
    """创建一个演示项目"""
    demo_dir = Path("demo_project")

    # 清理旧的演示项目
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    demo_dir.mkdir()

    # 创建源代码目录和文件
    src_dir = demo_dir / "src"
    src_dir.mkdir()

    # 创建一个简单的哈希表实现
    hash_table_h = src_dir / "hash_table.h"
    hash_table_h.write_text("""
#ifndef HASH_TABLE_H
#define HASH_TABLE_H

#include <stdbool.h>

typedef struct HashTable HashTable;

HashTable* hash_table_create(int capacity);
void hash_table_destroy(HashTable* table);
bool hash_table_insert(HashTable* table, const char* key, int value);
bool hash_table_get(HashTable* table, const char* key, int* value);
bool hash_table_remove(HashTable* table, const char* key);
int hash_table_size(HashTable* table);

#endif
""")

    hash_table_c = src_dir / "hash_table.c"
    hash_table_c.write_text("""
#include "hash_table.h"
#include <stdlib.h>
#include <string.h>

#define MAX_KEY_LEN 256

typedef struct Entry {
    char key[MAX_KEY_LEN];
    int value;
    struct Entry* next;
} Entry;

struct HashTable {
    int capacity;
    int size;
    Entry** buckets;
};

static unsigned int hash(const char* key, int capacity) {
    unsigned int hash = 5381;
    int c;
    while ((c = *key++)) {
        hash = ((hash << 5) + hash) + c;
    }
    return hash % capacity;
}

HashTable* hash_table_create(int capacity) {
    HashTable* table = malloc(sizeof(HashTable));
    table->capacity = capacity;
    table->size = 0;
    table->buckets = calloc(capacity, sizeof(Entry*));
    return table;
}

void hash_table_destroy(HashTable* table) {
    for (int i = 0; i < table->capacity; i++) {
        Entry* entry = table->buckets[i];
        while (entry) {
            Entry* next = entry->next;
            free(entry);
            entry = next;
        }
    }
    free(table->buckets);
    free(table);
}

bool hash_table_insert(HashTable* table, const char* key, int value) {
    if (strlen(key) >= MAX_KEY_LEN) return false;

    unsigned int index = hash(key, table->capacity);
    Entry* entry = table->buckets[index];

    // 检查是否已存在
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            entry->value = value;
            return true;
        }
        entry = entry->next;
    }

    // 创建新条目
    Entry* new_entry = malloc(sizeof(Entry));
    strcpy(new_entry->key, key);
    new_entry->value = value;
    new_entry->next = table->buckets[index];
    table->buckets[index] = new_entry;
    table->size++;
    return true;
}

bool hash_table_get(HashTable* table, const char* key, int* value) {
    unsigned int index = hash(key, table->capacity);
    Entry* entry = table->buckets[index];

    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            *value = entry->value;
            return true;
        }
        entry = entry->next;
    }
    return false;
}

bool hash_table_remove(HashTable* table, const char* key) {
    unsigned int index = hash(key, table->capacity);
    Entry* entry = table->buckets[index];
    Entry* prev = NULL;

    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            if (prev) {
                prev->next = entry->next;
            } else {
                table->buckets[index] = entry->next;
            }
            free(entry);
            table->size--;
            return true;
        }
        prev = entry;
        entry = entry->next;
    }
    return false;
}

int hash_table_size(HashTable* table) {
    return table->size;
}
""")

    # 创建 CMakeLists.txt
    cmake_file = demo_dir / "CMakeLists.txt"
    cmake_file.write_text("""
cmake_minimum_required(VERSION 3.10)
project(HashTableDemo)

set(CMAKE_C_STANDARD 99)

# 启用测试
enable_testing()

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
""")

    # 创建测试目录
    test_dir = demo_dir / "tests"
    test_dir.mkdir()

    # 创建一个初始的空测试文件
    test_file = test_dir / "test_hash_table.cpp"
    test_file.write_text("""
#include <gtest/gtest.h>
#include "hash_table.h"

// 初始空测试文件
""")

    # 创建一些生成的测试文件
    generated_dir = demo_dir / "generated_tests"
    generated_dir.mkdir()

    # 创建一个示例生成的测试文件
    generated_test = generated_dir / "test_hash_table_generated.cpp"
    generated_test.write_text("""
#include <gtest/gtest.h>
#include "hash_table.h"

// **TARGET_FUNCTION**: hash_table_insert

TEST(HashTableTest, InsertSingleElement) {
    HashTable* table = hash_table_create(10);
    ASSERT_TRUE(hash_table_insert(table, "key1", 100));

    int value;
    ASSERT_TRUE(hash_table_get(table, "key1", &value));
    EXPECT_EQ(value, 100);

    hash_table_destroy(table);
}

// **TARGET_FUNCTION**: hash_table_get

TEST(HashTableTest, GetNonExistentElement) {
    HashTable* table = hash_table_create(10);

    int value;
    EXPECT_FALSE(hash_table_get(table, "nonexistent", &value));

    hash_table_destroy(table);
}

// **TARGET_FUNCTION**: hash_table_remove

TEST(HashTableTest, RemoveExistingElement) {
    HashTable* table = hash_table_create(10);
    hash_table_insert(table, "key1", 100);

    EXPECT_TRUE(hash_table_remove(table, "key1"));

    int value;
    EXPECT_FALSE(hash_table_get(table, "key1", &value));

    hash_table_destroy(table);
}

// **TARGET_FUNCTION**: hash_table_size

TEST(HashTableTest, SizeAfterOperations) {
    HashTable* table = hash_table_create(10);

    EXPECT_EQ(hash_table_size(table), 0);

    hash_table_insert(table, "key1", 100);
    hash_table_insert(table, "key2", 200);
    EXPECT_EQ(hash_table_size(table), 2);

    hash_table_remove(table, "key1");
    EXPECT_EQ(hash_table_size(table), 1);

    hash_table_destroy(table);
}
""")

    return demo_dir

def main():
    """主演示函数"""
    print("🚀 Agentic Coding 演示")
    print("=" * 70)

    # 创建演示项目
    print("\n📁 创建演示项目...")
    demo_dir = create_demo_project()
    print(f"✅ 演示项目创建于: {demo_dir.absolute()}")

    # 初始化 Git 仓库（用于备份）
    print("\n📦 初始化 Git 仓库...")
    # 不切换目录，使用绝对路径操作
    os.system(f"cd {demo_dir} && git init -q")
    os.system(f"cd {demo_dir} && git config user.email 'demo@example.com'")
    os.system(f"cd {demo_dir} && git config user.name 'Demo User'")
    os.system(f"cd {demo_dir} && git add .")
    os.system(f"cd {demo_dir} && git commit -m 'Initial commit' -q")

    # 配置 Agentic Coding 系统
    print("\n⚙️ 配置 Agentic Coding 系统...")
    config = {
        'project_root': str(demo_dir.absolute()),
        'source_dir': 'src',
        'test_dir': 'tests',
        'build_dir': 'build',
        'backup_method': 'git',
        'run_tests': True,
        'log_level': 'INFO'
    }

    # 创建 Agentic Coding 系统
    system = AgenticCodingSystem(config)

    # 运行系统
    print("\n🔧 运行 Agentic Coding 系统...")
    print("-" * 70)

    test_files = ['generated_tests/test_hash_table_generated.cpp']

    result = system.run({
        **config,
        'test_files': [str(demo_dir / f) for f in test_files]
    })

    # 打印详细报告
    system.print_report(result)

    # 验证结果
    print("\n📊 验证结果:")

    # 检查测试文件是否被更新
    test_file = demo_dir / "tests" / "test_hash_table.cpp"
    if test_file.exists():
        content = test_file.read_text()
        test_count = content.count("TEST(")
        print(f"✅ 测试文件已更新，包含 {test_count} 个测试")

    # 尝试构建和运行测试
    print("\n🔨 构建项目...")
    build_result = os.system(f"cd {demo_dir} && mkdir -p build && cmake -S . -B build && cmake --build build 2>/dev/null")

    if build_result == 0:
        print("✅ 构建成功")

        print("\n🧪 运行测试...")
        test_result = os.system(f"cd {demo_dir}/build && ctest --output-on-failure")

        if test_result == 0:
            print("✅ 所有测试通过！")
        else:
            print("⚠️ 部分测试失败")
    else:
        print("❌ 构建失败")

    print("\n" + "=" * 70)
    print("演示完成！")
    print(f"📁 演示项目位于: {demo_dir.absolute()}")
    print("\n查看生成的文件:")
    print(f"  - 测试文件: {test_file}")
    print(f"  - CMakeLists.txt: {demo_dir / 'CMakeLists.txt'}")
    print("\n可以手动进入项目目录查看和运行：")
    print(f"  cd {demo_dir}")
    print("  mkdir -p build && cmake -S . -B build")
    print("  cmake --build build")
    print("  cd build && ctest")

if __name__ == "__main__":
    main()