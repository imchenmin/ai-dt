#include "memory_pool.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// 内存对齐
#define MEMORY_ALIGNMENT 8
#define ALIGN_SIZE(size) (((size) + MEMORY_ALIGNMENT - 1) & ~(MEMORY_ALIGNMENT - 1))

// 静态辅助函数 - 初始化内存块
static void init_memory_block(MemoryBlock* block, size_t block_size, MemoryBlock* next) {
    block->next = next;
    block->size = block_size;
    block->is_allocated = 0;
    block->data = (char*)block + sizeof(MemoryBlock);
}

// 静态辅助函数 - 查找空闲块
static MemoryBlock* find_free_block(MemoryPool* pool, size_t required_size) {
    MemoryBlock* current = pool->free_list;
    MemoryBlock* prev = NULL;
    MemoryBlock* best_fit = NULL;
    MemoryBlock* best_fit_prev = NULL;
    
    // 最佳适应算法
    while (current) {
        if (current->size >= required_size && !current->is_allocated) {
            if (!best_fit || current->size < best_fit->size) {
                best_fit = current;
                best_fit_prev = prev;
            }
        }
        prev = current;
        current = current->next;
    }
    
    return best_fit;
}

MemoryPool* memory_pool_create(size_t block_size, size_t num_blocks) {
    if (block_size == 0 || num_blocks == 0) return NULL;
    
    // 对齐块大小
    size_t aligned_block_size = ALIGN_SIZE(block_size);
    size_t total_memory = num_blocks * (sizeof(MemoryBlock) + aligned_block_size);
    
    MemoryPool* pool = (MemoryPool*)malloc(sizeof(MemoryPool));
    if (!pool) return NULL;
    
    pool->memory_area = malloc(total_memory);
    if (!pool->memory_area) {
        free(pool);
        return NULL;
    }
    
    // 初始化内存池
    pool->block_size = aligned_block_size;
    pool->total_blocks = num_blocks;
    pool->used_blocks = 0;
    pool->memory_size = total_memory;
    pool->first_block = NULL;
    pool->free_list = NULL;
    
    // 初始化所有内存块
    char* memory_ptr = (char*)pool->memory_area;
    for (size_t i = 0; i < num_blocks; i++) {
        MemoryBlock* block = (MemoryBlock*)memory_ptr;
        init_memory_block(block, aligned_block_size, NULL);
        
        // 添加到块链表
        block->next = pool->first_block;
        pool->first_block = block;
        
        // 添加到空闲链表
        block->next = pool->free_list;
        pool->free_list = block;
        
        memory_ptr += sizeof(MemoryBlock) + aligned_block_size;
    }
    
    return pool;
}

MemoryPoolError memory_pool_destroy(MemoryPool* pool) {
    if (!pool) return MEMPOOL_INVALID_PARAM;
    
    if (pool->used_blocks > 0) {
        return MEMPOOL_CORRUPTED; // 还有内存未释放
    }
    
    free(pool->memory_area);
    free(pool);
    return MEMPOOL_SUCCESS;
}

void* memory_pool_alloc(MemoryPool* pool, size_t size) {
    if (!pool || size == 0 || size > pool->block_size) return NULL;
    
    MemoryBlock* block = find_free_block(pool, size);
    if (!block) return NULL; // 没有合适的空闲块
    
    block->is_allocated = 1;
    pool->used_blocks++;
    
    // 从空闲链表中移除
    if (pool->free_list == block) {
        pool->free_list = block->next;
    } else {
        // 需要遍历找到前一个节点
        MemoryBlock* current = pool->free_list;
        while (current && current->next != block) {
            current = current->next;
        }
        if (current) {
            current->next = block->next;
        }
    }
    
    block->next = NULL;
    return block->data;
}

MemoryPoolError memory_pool_free(MemoryPool* pool, void* ptr) {
    if (!pool || !ptr) return MEMPOOL_INVALID_PARAM;
    
    // 找到对应的内存块
    MemoryBlock* block = (MemoryBlock*)((char*)ptr - sizeof(MemoryBlock));
    
    // 验证指针是否在内存池范围内
    if ((char*)block < (char*)pool->memory_area || 
        (char*)block >= (char*)pool->memory_area + pool->memory_size) {
        return MEMPOOL_INVALID_PARAM;
    }
    
    if (!block->is_allocated) {
        return MEMPOOL_CORRUPTED; // 重复释放
    }
    
    block->is_allocated = 0;
    pool->used_blocks--;
    
    // 添加到空闲链表头部
    block->next = pool->free_list;
    pool->free_list = block;
    
    return MEMPOOL_SUCCESS;
}

size_t memory_pool_get_usage(const MemoryPool* pool) {
    return pool ? pool->used_blocks : 0;
}

size_t memory_pool_get_capacity(const MemoryPool* pool) {
    return pool ? pool->total_blocks : 0;
}

int memory_pool_is_full(const MemoryPool* pool) {
    return pool ? (pool->used_blocks == pool->total_blocks) : 1;
}

int memory_pool_is_empty(const MemoryPool* pool) {
    return pool ? (pool->used_blocks == 0) : 1;
}

MemoryPoolError memory_pool_validate(const MemoryPool* pool) {
    if (!pool) return MEMPOOL_INVALID_PARAM;
    
    // 检查内存块一致性
    size_t counted_blocks = 0;
    size_t counted_allocated = 0;
    
    MemoryBlock* current = pool->first_block;
    while (current) {
        counted_blocks++;
        if (current->is_allocated) counted_allocated++;
        
        // 检查块指针是否在内存池范围内
        if ((char*)current < (char*)pool->memory_area || 
            (char*)current >= (char*)pool->memory_area + pool->memory_size) {
            return MEMPOOL_CORRUPTED;
        }
        
        current = current->next;
    }
    
    if (counted_blocks != pool->total_blocks || counted_allocated != pool->used_blocks) {
        return MEMPOOL_CORRUPTED;
    }
    
    return MEMPOOL_SUCCESS;
}

void memory_pool_dump_stats(const MemoryPool* pool) {
    if (!pool) {
        printf("Memory pool is NULL\n");
        return;
    }
    
    printf("Memory Pool Statistics:\n");
    printf("  Total blocks: %zu\n", pool->total_blocks);
    printf("  Used blocks: %zu\n", pool->used_blocks);
    printf("  Free blocks: %zu\n", pool->total_blocks - pool->used_blocks);
    printf("  Block size: %zu bytes\n", pool->block_size);
    printf("  Total memory: %zu bytes\n", pool->memory_size);
    printf("  Utilization: %.1f%%\n", 
           (float)pool->used_blocks / pool->total_blocks * 100);
}