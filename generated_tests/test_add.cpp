#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, AddNormalCases) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(add(-2, 3), 1);
    EXPECT_EQ(add(0, 0), 0);
}

TEST(MathUtilsTest, AddEdgeCases) {
    EXPECT_EQ(add(INT_MAX, 1), INT_MIN);  // Overflow behavior
    EXPECT_EQ(add(INT_MIN, -1), INT_MAX); // Underflow behavior
    EXPECT_EQ(add(INT_MAX, INT_MIN), -1);
}

TEST(MathUtilsTest, AddCommutative) {
    EXPECT_EQ(add(5, 3), add(3, 5));
    EXPECT_EQ(add(-5, 3), add(3, -5));
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}