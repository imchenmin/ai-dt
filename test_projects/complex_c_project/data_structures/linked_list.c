#include "linked_list.h"
#include <stdlib.h>
#include <stdio.h>

// 静态辅助函数 - 创建新节点
static ListNode* create_node(int data) {
    ListNode* node = (ListNode*)malloc(sizeof(ListNode));
    if (!node) return NULL;
    node->data = data;
    node->next = NULL;
    return node;
}

// 静态辅助函数 - 获取指定位置的节点
static ListNode* get_node_at(const LinkedList* list, size_t index) {
    if (index >= list->size) return NULL;
    
    ListNode* current = list->head;
    for (size_t i = 0; i < index; i++) {
        current = current->next;
    }
    return current;
}

LinkedList* list_create(void) {
    LinkedList* list = (LinkedList*)malloc(sizeof(LinkedList));
    if (!list) return NULL;
    
    list->head = NULL;
    list->tail = NULL;
    list->size = 0;
    return list;
}

void list_destroy(LinkedList* list) {
    if (!list) return;
    
    ListNode* current = list->head;
    while (current) {
        ListNode* next = current->next;
        free(current);
        current = next;
    }
    free(list);
}

int list_append(LinkedList* list, int data) {
    if (!list) return -1;
    
    ListNode* node = create_node(data);
    if (!node) return -1;
    
    if (list->size == 0) {
        list->head = node;
        list->tail = node;
    } else {
        list->tail->next = node;
        list->tail = node;
    }
    
    list->size++;
    return 0;
}

int list_prepend(LinkedList* list, int data) {
    if (!list) return -1;
    
    ListNode* node = create_node(data);
    if (!node) return -1;
    
    if (list->size == 0) {
        list->head = node;
        list->tail = node;
    } else {
        node->next = list->head;
        list->head = node;
    }
    
    list->size++;
    return 0;
}

int list_insert_at(LinkedList* list, size_t index, int data) {
    if (!list || index > list->size) return -1;
    
    if (index == 0) return list_prepend(list, data);
    if (index == list->size) return list_append(list, data);
    
    ListNode* prev = get_node_at(list, index - 1);
    if (!prev) return -1;
    
    ListNode* node = create_node(data);
    if (!node) return -1;
    
    node->next = prev->next;
    prev->next = node;
    list->size++;
    return 0;
}

int list_remove_at(LinkedList* list, size_t index) {
    if (!list || index >= list->size) return -1;
    
    ListNode* to_remove;
    if (index == 0) {
        to_remove = list->head;
        list->head = list->head->next;
        if (list->size == 1) {
            list->tail = NULL;
        }
    } else {
        ListNode* prev = get_node_at(list, index - 1);
        if (!prev || !prev->next) return -1;
        
        to_remove = prev->next;
        prev->next = to_remove->next;
        
        if (index == list->size - 1) {
            list->tail = prev;
        }
    }
    
    free(to_remove);
    list->size--;
    return 0;
}

int list_get_at(const LinkedList* list, size_t index) {
    ListNode* node = get_node_at(list, index);
    return node ? node->data : -1;
}

int list_contains(const LinkedList* list, int data) {
    if (!list) return 0;
    
    ListNode* current = list->head;
    while (current) {
        if (current->data == data) return 1;
        current = current->next;
    }
    return 0;
}

size_t list_size(const LinkedList* list) {
    return list ? list->size : 0;
}

int list_is_empty(const LinkedList* list) {
    return list ? (list->size == 0) : 1;
}

void list_reverse(LinkedList* list) {
    if (!list || list->size <= 1) return;
    
    ListNode* prev = NULL;
    ListNode* current = list->head;
    list->tail = list->head;
    
    while (current) {
        ListNode* next = current->next;
        current->next = prev;
        prev = current;
        current = next;
    }
    
    list->head = prev;
}

void list_foreach(const LinkedList* list, ListIterator iterator, void* context) {
    if (!list || !iterator) return;
    
    ListNode* current = list->head;
    while (current) {
        if (iterator(current->data, context) != 0) break;
        current = current->next;
    }
}