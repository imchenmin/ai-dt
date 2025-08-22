#ifndef MATH_UTILS_H
#define MATH_UTILS_H

// Simple math utilities for testing
int add(int a, int b);
int subtract(int a, int b);
float divide(float a, float b);
int multiply(int a, int b);

// Static function (should not be testable)
static int internal_helper(int x) {
    return x * 2;
}

#endif // MATH_UTILS_H