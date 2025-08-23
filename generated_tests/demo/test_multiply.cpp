#include <gtest/gtest.h>
#include "math_utils.h"

// Mock for add function since multiply calls add
int add(int a, int b) {
    return a + b;
}

TEST(MathUtilsTest, MultiplyNormalCases) {
    EXPECT_EQ(multiply(2, 3), 6);
    EXPECT_EQ(multiply(5, 0), 0);
    EXPECT_EQ(multiply(-2, 3), -6);
    EXPECT_EQ(multiply(-2, -3), 6);
}

TEST(MathUtilsTest, MultiplyEdgeCases) {
    EXPECT_EQ(multiply(INT_MAX, 2), -2);  // Overflow behavior
    EXPECT_EQ(multiply(INT_MIN, 2), 0);   // Underflow behavior
    EXPECT_EQ(multiply(0, INT_MAX), 0);
}

TEST(MathUtilsTest, MultiplyWithZero) {
    EXPECT_EQ(multiply(0, 5), 0);
    EXPECT_EQ(multiply(5, 0), 0);
    EXPECT_EQ(multiply(0, 0), 0);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}