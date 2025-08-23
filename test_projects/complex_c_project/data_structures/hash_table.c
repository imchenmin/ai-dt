#include "hash_table.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// 静态辅助函数 - 创建哈希节点
static HashNode* create_hash_node(const char* key, int value) {
    HashNode* node = (HashNode*)malloc(sizeof(HashNode));
    if (!node) return NULL;
    
    node->key = strdup(key);
    if (!node->key) {
        free(node);
        return NULL;
    }
    
    node->value = value;
    node->next = NULL;
    return node;
}

// 静态辅助函数 - 释放哈希节点
static void free_hash_node(HashNode* node) {
    if (node) {
        free(node->key);
        free(node);
    }
}

// 默认哈希函数 - DJB2算法
size_t default_hash_function(const char* key, size_t capacity) {
    size_t hash = 5381;
    int c;
    
    while ((c = *key++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    
    return hash % capacity;
}

HashTable* hash_table_create(size_t capacity) {
    if (capacity == 0) capacity = 16;
    
    HashTable* table = (HashTable*)malloc(sizeof(HashTable));
    if (!table) return NULL;
    
    table->buckets = (HashNode**)calloc(capacity, sizeof(HashNode*));
    if (!table->buckets) {
        free(table);
        return NULL;
    }
    
    table->capacity = capacity;
    table->size = 0;
    return table;
}

void hash_table_destroy(HashTable* table) {
    if (!table) return;
    
    for (size_t i = 0; i < table->capacity; i++) {
        HashNode* current = table->buckets[i];
        while (current) {
            HashNode* next = current->next;
            free_hash_node(current);
            current = next;
        }
    }
    
    free(table->buckets);
    free(table);
}

int hash_table_put(HashTable* table, const char* key, int value) {
    if (!table || !key) return -1;
    
    size_t index = default_hash_function(key, table->capacity);
    HashNode* current = table->buckets[index];
    
    // 检查键是否已存在
    while (current) {
        if (strcmp(current->key, key) == 0) {
            current->value = value; // 更新值
            return 0;
        }
        current = current->next;
    }
    
    // 创建新节点并添加到链表头部
    HashNode* new_node = create_hash_node(key, value);
    if (!new_node) return -1;
    
    new_node->next = table->buckets[index];
    table->buckets[index] = new_node;
    table->size++;
    
    return 0;
}

int hash_table_get(const HashTable* table, const char* key, int* out_value) {
    if (!table || !key || !out_value) return -1;
    
    size_t index = default_hash_function(key, table->capacity);
    HashNode* current = table->buckets[index];
    
    while (current) {
        if (strcmp(current->key, key) == 0) {
            *out_value = current->value;
            return 0;
        }
        current = current->next;
    }
    
    return -1; // 键不存在
}

int hash_table_remove(HashTable* table, const char* key) {
    if (!table || !key) return -1;
    
    size_t index = default_hash_function(key, table->capacity);
    HashNode* current = table->buckets[index];
    HashNode* prev = NULL;
    
    while (current) {
        if (strcmp(current->key, key) == 0) {
            if (prev) {
                prev->next = current->next;
            } else {
                table->buckets[index] = current->next;
            }
            
            free_hash_node(current);
            table->size--;
            return 0;
        }
        
        prev = current;
        current = current->next;
    }
    
    return -1; // 键不存在
}

int hash_table_contains(const HashTable* table, const char* key) {
    if (!table || !key) return 0;
    
    size_t index = default_hash_function(key, table->capacity);
    HashNode* current = table->buckets[index];
    
    while (current) {
        if (strcmp(current->key, key) == 0) {
            return 1;
        }
        current = current->next;
    }
    
    return 0;
}

size_t hash_table_size(const HashTable* table) {
    return table ? table->size : 0;
}

int hash_table_is_empty(const HashTable* table) {
    return table ? (table->size == 0) : 1;
}

void hash_table_foreach(const HashTable* table, HashTableIterator iterator, void* context) {
    if (!table || !iterator) return;
    
    for (size_t i = 0; i < table->capacity; i++) {
        HashNode* current = table->buckets[i];
        while (current) {
            if (iterator(current->key, current->value, context) != 0) return;
            current = current->next;
        }
    }
}