#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef struct {
    int data;
    struct Node* next;
} Node;

typedef struct {
    int* items;
    int capacity;
    int size;
} Stack;

typedef struct {
    int* items;
    int front;
    int rear;
    int capacity;
} Queue;

typedef struct {
    int* items;
    int size;
    int capacity;
} ArrayList;

// Data structure functions - 20 functions
Node* create_node(int data) {
    Node* node = (Node*)malloc(sizeof(Node));
    if (!node) return NULL;
    node->data = data;
    node->next = NULL;
    return node;
}

void destroy_node(Node* node) {
    if (node) {
        free(node);
    }
}

Stack* create_stack(int capacity) {
    Stack* stack = (Stack*)malloc(sizeof(Stack));
    if (!stack) return NULL;
    stack->items = (int*)malloc(capacity * sizeof(int));
    if (!stack->items) {
        free(stack);
        return NULL;
    }
    stack->capacity = capacity;
    stack->size = 0;
    return stack;
}

void destroy_stack(Stack* stack) {
    if (stack) {
        if (stack->items) free(stack->items);
        free(stack);
    }
}

int stack_push(Stack* stack, int item) {
    if (!stack || stack->size >= stack->capacity) return 0;
    stack->items[stack->size++] = item;
    return 1;
}

int stack_pop(Stack* stack, int* result) {
    if (!stack || stack->size <= 0 || !result) return 0;
    *result = stack->items[--stack->size];
    return 1;
}

int stack_is_empty(Stack* stack) {
    return !stack || stack->size == 0;
}

int stack_is_full(Stack* stack) {
    return !stack || stack->size >= stack->capacity;
}

Queue* create_queue(int capacity) {
    Queue* queue = (Queue*)malloc(sizeof(Queue));
    if (!queue) return NULL;
    queue->items = (int*)malloc(capacity * sizeof(int));
    if (!queue->items) {
        free(queue);
        return NULL;
    }
    queue->capacity = capacity;
    queue->front = 0;
    queue->rear = -1;
    return queue;
}

void destroy_queue(Queue* queue) {
    if (queue) {
        if (queue->items) free(queue->items);
        free(queue);
    }
}

int queue_enqueue(Queue* queue, int item) {
    if (!queue || (queue->rear + 1) % queue->capacity == queue->front) return 0;
    queue->rear = (queue->rear + 1) % queue->capacity;
    queue->items[queue->rear] = item;
    return 1;
}

int queue_dequeue(Queue* queue, int* result) {
    if (!queue || queue->front == (queue->rear + 1) % queue->capacity || !result) return 0;
    *result = queue->items[queue->front];
    queue->front = (queue->front + 1) % queue->capacity;
    return 1;
}

int queue_is_empty(Queue* queue) {
    return !queue || queue->front == (queue->rear + 1) % queue->capacity;
}

ArrayList* create_array_list(int initial_capacity) {
    ArrayList* list = (ArrayList*)malloc(sizeof(ArrayList));
    if (!list) return NULL;
    list->items = (int*)malloc(initial_capacity * sizeof(int));
    if (!list->items) {
        free(list);
        return NULL;
    }
    list->size = 0;
    list->capacity = initial_capacity;
    return list;
}

void destroy_array_list(ArrayList* list) {
    if (list) {
        if (list->items) free(list->items);
        free(list);
    }
}

int array_list_add(ArrayList* list, int item) {
    if (!list) return 0;
    if (list->size >= list->capacity) {
        int new_capacity = list->capacity * 2;
        int* new_items = (int*)realloc(list->items, new_capacity * sizeof(int));
        if (!new_items) return 0;
        list->items = new_items;
        list->capacity = new_capacity;
    }
    list->items[list->size++] = item;
    return 1;
}

int array_list_get(ArrayList* list, int index, int* result) {
    if (!list || index < 0 || index >= list->size || !result) return 0;
    *result = list->items[index];
    return 1;
}

int array_list_size(ArrayList* list) {
    return !list ? 0 : list->size;
}