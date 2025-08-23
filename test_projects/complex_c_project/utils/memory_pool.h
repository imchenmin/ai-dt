#ifndef MEMORY_POOL_H
#define MEMORY_POOL_H

#include <stddef.h>

// 内存池块结构
typedef struct MemoryBlock {
    struct MemoryBlock* next;
    size_t size;
    int is_allocated;
    void* data;
} MemoryBlock;

// 内存池结构
typedef struct {
    MemoryBlock* first_block;
    MemoryBlock* free_list;
    size_t block_size;
    size_t total_blocks;
    size_t used_blocks;
    void* memory_area;
    size_t memory_size;
} MemoryPool;

// 错误码
typedef enum {
    MEMPOOL_SUCCESS = 0,
    MEMPOOL_INVALID_PARAM = -1,
    MEMPOOL_OUT_OF_MEMORY = -2,
    MEMPOOL_CORRUPTED = -3,
    MEMPOOL_ALREADY_INIT = -4
} MemoryPoolError;

// 函数声明
MemoryPool* memory_pool_create(size_t block_size, size_t num_blocks);
MemoryPoolError memory_pool_destroy(MemoryPool* pool);
void* memory_pool_alloc(MemoryPool* pool, size_t size);
MemoryPoolError memory_pool_free(MemoryPool* pool, void* ptr);
size_t memory_pool_get_usage(const MemoryPool* pool);
size_t memory_pool_get_capacity(const MemoryPool* pool);
int memory_pool_is_full(const MemoryPool* pool);
int memory_pool_is_empty(const MemoryPool* pool);
MemoryPoolError memory_pool_validate(const MemoryPool* pool);

// 调试函数
void memory_pool_dump_stats(const MemoryPool* pool);

#endif // MEMORY_POOL_H