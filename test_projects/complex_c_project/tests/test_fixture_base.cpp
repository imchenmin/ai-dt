#include <gtest/gtest.h>
#include <mockcpp/mockcpp.h>

// Base fixture for linked list tests
class linked_listTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize common test data
        test_data_small = 42;
        test_data_large = 999999;
        test_index_valid = 0;
        test_index_invalid = 1000;
    }

    void TearDown() override {
        // Clean up any allocated resources
        if (test_list != nullptr) {
            list_destroy(test_list);
            test_list = nullptr;
        }
    }

    // Common test data
    int test_data_small;
    int test_data_large;
    size_t test_index_valid;
    size_t test_index_invalid;
    LinkedList* test_list = nullptr;
};

// Base fixture for hash table tests
class HashTableTestFixture : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize test hash table with capacity 10
        test_capacity = 10;
        test_table = hash_table_create(test_capacity);
        
        // Common test keys and values
        test_key_1 = "test_key_1";
        test_key_2 = "test_key_2";
        test_value_1 = 100;
        test_value_2 = 200;
    }

    void TearDown() override {
        if (test_table != nullptr) {
            hash_table_destroy(test_table);
            test_table = nullptr;
        }
    }

    // Test data members
    HashTable* test_table = nullptr;
    size_t test_capacity;
    const char* test_key_1;
    const char* test_key_2;
    int test_value_1;
    int test_value_2;
};

// Memory pool test fixture
class MemoryPoolTestFixture : public ::testing::Test {
protected:
    void SetUp() override {
        // Create memory pool with standard configuration
        block_size = 64;
        num_blocks = 10;
        test_pool = memory_pool_create(block_size, num_blocks);
    }

    void TearDown() override {
        if (test_pool != nullptr) {
            memory_pool_destroy(test_pool);
            test_pool = nullptr;
        }
    }

    // Test configuration
    MemoryPool* test_pool = nullptr;
    size_t block_size;
    size_t num_blocks;
};