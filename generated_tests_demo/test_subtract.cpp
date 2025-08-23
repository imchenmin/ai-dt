#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, SubtractNormalCases) {
    EXPECT_EQ(subtract(5, 3), 2);
    EXPECT_EQ(subtract(3, 5), -2);
    EXPECT_EQ(subtract(0, 0), 0);
    EXPECT_EQ(subtract(-5, -3), -2);
}

TEST(MathUtilsTest, SubtractEdgeCases) {
    EXPECT_EQ(subtract(INT_MAX, -1), INT_MIN);  // Overflow
    EXPECT_EQ(subtract(INT_MIN, 1), INT_MAX);   // Underflow
    EXPECT_EQ(subtract(INT_MAX, INT_MAX), 0);
}

TEST(MathUtilsTest, SubtractCommutative) {
    EXPECT_EQ(subtract(5, 3), -(subtract(3, 5)));
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}