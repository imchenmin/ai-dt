// Generated tests for hash_table.c
// Generated at: 2025-11-06T22:42:19.101082
// Test target: hash_table_size

#include <gtest/gtest.h>
#include <gmock/gmock.h>
extern "C" {
#include "../src/hash_table.h"
}

// Test functions


TEST(HashTableTest, RemoveExistingElement) {
    HashTable* table = hash_table_create(10);
    hash_table_insert(table, "key1", 100);

    EXPECT_TRUE(hash_table_remove(table, "key1"));

    int value;
    EXPECT_FALSE(hash_table_get(table, "key1", &value));

    hash_table_destroy(table);
}