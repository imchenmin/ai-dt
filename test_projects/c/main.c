#include "math_utils.h"
#include <stdio.h>

int main() {
    int result = add(5, 3);
    printf("5 + 3 = %d\n", result);
    
    result = multiply(4, 5);
    printf("4 * 5 = %d\n", result);
    
    float quotient = divide(10.0f, 2.0f);
    printf("10.0 / 2.0 = %.1f\n", quotient);
    
    return 0;
}