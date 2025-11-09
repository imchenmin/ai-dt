
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
