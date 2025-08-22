#include "math_utils.h"
#include <stdio.h>

#define MAX_VALUE 100

int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

float divide(float a, float b) {
    if (b == 0.0f) {
        return 0.0f;
    }
    return a / b;
}

int multiply(int a, int b) {
    int result = 0;
    for (int i = 0; i < b; i++) {
        result = add(result, a);  // Calls another function
    }
    return result;
}

// Another static function
static void log_operation(const char* op) {
    printf("Performing operation: %s\n", op);
}