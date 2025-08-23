#ifndef HASH_TABLE_H
#define HASH_TABLE_H

#include <stddef.h>

// 哈希表节点
typedef struct HashNode {
    char* key;
    int value;
    struct HashNode* next;
} HashNode;

// 哈希表结构
typedef struct {
    HashNode** buckets;
    size_t capacity;
    size_t size;
} HashTable;

// 哈希函数类型
typedef size_t (*HashFunction)(const char* key, size_t capacity);

// 函数声明
HashTable* hash_table_create(size_t capacity);
void hash_table_destroy(HashTable* table);
int hash_table_put(HashTable* table, const char* key, int value);
int hash_table_get(const HashTable* table, const char* key, int* out_value);
int hash_table_remove(HashTable* table, const char* key);
int hash_table_contains(const HashTable* table, const char* key);
size_t hash_table_size(const HashTable* table);
int hash_table_is_empty(const HashTable* table);

// 迭代器
typedef int (*HashTableIterator)(const char* key, int value, void* context);
void hash_table_foreach(const HashTable* table, HashTableIterator iterator, void* context);

// 默认哈希函数
size_t default_hash_function(const char* key, size_t capacity);

#endif // HASH_TABLE_H