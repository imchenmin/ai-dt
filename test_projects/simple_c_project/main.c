#include <stdio.h>
#include "utils.h"

int main() {
    int data = 10;
    printf("Calling process_data with: %d\n", data);
    int result = process_data(data);
    printf("Result from process_data: %d\n", result);
    return 0;
}