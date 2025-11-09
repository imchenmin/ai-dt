
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
