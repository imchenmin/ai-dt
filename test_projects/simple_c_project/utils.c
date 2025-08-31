#include "utils.h"
#include <stdio.h>

// This is a static function that cannot be directly tested from outside this file.
static int helper_function(int value) {
    return value * 2;
}

// This is the public function that can be tested.
// It calls the static helper_function.
int process_data(int data) {
    printf("Processing data: %d\n", data);
    return helper_function(data);
}