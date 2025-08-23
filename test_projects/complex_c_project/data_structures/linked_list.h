#ifndef LINKED_LIST_H
#define LINKED_LIST_H

#include <stddef.h>

// 链表节点结构
typedef struct ListNode {
    int data;
    struct ListNode* next;
} ListNode;

// 链表结构
typedef struct {
    ListNode* head;
    ListNode* tail;
    size_t size;
} LinkedList;

// 函数声明
LinkedList* list_create(void);
void list_destroy(LinkedList* list);
int list_append(LinkedList* list, int data);
int list_prepend(LinkedList* list, int data);
int list_insert_at(LinkedList* list, size_t index, int data);
int list_remove_at(LinkedList* list, size_t index);
int list_get_at(const LinkedList* list, size_t index);
int list_contains(const LinkedList* list, int data);
size_t list_size(const LinkedList* list);
int list_is_empty(const LinkedList* list);
void list_reverse(LinkedList* list);

// 迭代器函数
typedef int (*ListIterator)(int data, void* context);
void list_foreach(const LinkedList* list, ListIterator iterator, void* context);

#endif // LINKED_LIST_H