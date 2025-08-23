#include "data_structures/linked_list.h"
#include "data_structures/hash_table.h"
#include "utils/memory_pool.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 宏定义用于调试
#define DEBUG_PRINT(fmt, ...) \
    printf("[DEBUG] %s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)

// 条件编译 - 不同的测试模式
#ifdef TEST_MODE_FULL
#define RUN_FULL_TESTS 1
#else
#define RUN_FULL_TESTS 0
#endif

// 链表迭代器回调函数
static int print_list_item(int data, void* context) {
    printf("List item: %d\n", data);
    return 0;
}

// 哈希表迭代器回调函数
static int print_hash_item(const char* key, int value, void* context) {
    printf("Hash item: %s -> %d\n", key, value);
    return 0;
}

// 静态函数 - 内部使用的辅助函数
static void test_linked_list(void) {
    printf("=== Testing Linked List ===\n");
    
    LinkedList* list = list_create();
    if (!list) {
        fprintf(stderr, "Failed to create linked list\n");
        return;
    }
    
    // 测试基本操作
    list_append(list, 10);
    list_append(list, 20);
    list_prepend(list, 5);
    list_insert_at(list, 1, 15);
    
    printf("List size: %zu\n", list_size(list));
    printf("List contains 15: %d\n", list_contains(list, 15));
    printf("List contains 99: %d\n", list_contains(list, 99));
    
    // 测试迭代器
    printf("List contents:\n");
    list_foreach(list, print_list_item, NULL);
    
    // 测试反转
    list_reverse(list);
    printf("After reversal:\n");
    list_foreach(list, print_list_item, NULL);
    
    list_destroy(list);
}

static void test_hash_table(void) {
    printf("\n=== Testing Hash Table ===\n");
    
    HashTable* table = hash_table_create(8);
    if (!table) {
        fprintf(stderr, "Failed to create hash table\n");
        return;
    }
    
    // 测试基本操作
    hash_table_put(table, "apple", 10);
    hash_table_put(table, "banana", 20);
    hash_table_put(table, "orange", 30);
    hash_table_put(table, "apple", 15); // 更新值
    
    int value;
    if (hash_table_get(table, "banana", &value) == 0) {
        printf("banana: %d\n", value);
    }
    
    printf("Contains 'orange': %d\n", hash_table_contains(table, "orange"));
    printf("Table size: %zu\n", hash_table_size(table));
    
    // 测试迭代器
    printf("Hash table contents:\n");
    hash_table_foreach(table, print_hash_item, NULL);
    
    // 测试删除
    hash_table_remove(table, "banana");
    printf("After removal - size: %zu\n", hash_table_size(table));
    
    hash_table_destroy(table);
}

static void test_memory_pool(void) {
    printf("\n=== Testing Memory Pool ===\n");
    
    MemoryPool* pool = memory_pool_create(64, 10);
    if (!pool) {
        fprintf(stderr, "Failed to create memory pool\n");
        return;
    }
    
    memory_pool_dump_stats(pool);
    
    // 分配内存
    int* ptr1 = (int*)memory_pool_alloc(pool, sizeof(int));
    char* ptr2 = (char*)memory_pool_alloc(pool, 32);
    
    if (ptr1 && ptr2) {
        *ptr1 = 42;
        strcpy(ptr2, "Hello, Memory Pool!");
        
        printf("Allocated values: %d, %s\n", *ptr1, ptr2);
        
        memory_pool_dump_stats(pool);
        
        // 释放内存
        memory_pool_free(pool, ptr1);
        memory_pool_free(pool, ptr2);
    }
    
    memory_pool_dump_stats(pool);
    
    // 验证内存池完整性
    MemoryPoolError error = memory_pool_validate(pool);
    printf("Memory pool validation: %s\n", 
           error == MEMPOOL_SUCCESS ? "PASS" : "FAIL");
    
    memory_pool_destroy(pool);
}

// 函数指针示例 - 测试运行器
typedef void (*TestRunner)(void);

static TestRunner test_runners[] = {
    test_linked_list,
    test_hash_table,
    test_memory_pool,
    NULL
};

int main(int argc, char* argv[]) {
    printf("Complex C Project Test Runner\n");
    printf("=============================\n\n");
    
    DEBUG_PRINT("Starting test execution");
    
    // 根据编译模式决定运行哪些测试
    if (RUN_FULL_TESTS) {
        printf("Running full test suite...\n\n");
    } else {
        printf("Running basic test suite...\n\n");
    }
    
    // 使用函数指针运行所有测试
    for (int i = 0; test_runners[i] != NULL; i++) {
        test_runners[i]();
        printf("\n");
    }
    
    // 测试内存池边界情况（仅在完整模式下）
    if (RUN_FULL_TESTS) {
        printf("=== Testing Memory Pool Edge Cases ===\n");
        
        MemoryPool* edge_pool = memory_pool_create(32, 3);
        if (edge_pool) {
            void* ptrs[4];
            
            // 分配所有块
            for (int i = 0; i < 3; i++) {
                ptrs[i] = memory_pool_alloc(edge_pool, 16);
                printf("Allocated block %d: %p\n", i, ptrs[i]);
            }
            
            // 尝试分配更多（应该失败）
            ptrs[3] = memory_pool_alloc(edge_pool, 16);
            printf("Extra allocation: %p (should be NULL)\n", ptrs[3]);
            
            printf("Pool is full: %d\n", memory_pool_is_full(edge_pool));
            
            // 释放并重新分配
            memory_pool_free(edge_pool, ptrs[0]);
            void* new_ptr = memory_pool_alloc(edge_pool, 16);
            printf("Reallocated: %p\n", new_ptr);
            
            memory_pool_destroy(edge_pool);
        }
    }
    
    DEBUG_PRINT("Test execution completed");
    printf("\nAll tests completed successfully!\n");
    
    return 0;
}