#include <gtest/gtest.h>
#include "math_utils.h"

TEST(MathUtilsTest, DivideNormalCases) {
    EXPECT_FLOAT_EQ(divide(10.0f, 2.0f), 5.0f);
    EXPECT_FLOAT_EQ(divide(1.0f, 4.0f), 0.25f);
    EXPECT_FLOAT_EQ(divide(-10.0f, 2.0f), -5.0f);
}

TEST(MathUtilsTest, DivideByZero) {
    EXPECT_FLOAT_EQ(divide(5.0f, 0.0f), 0.0f);
    EXPECT_FLOAT_EQ(divide(-5.0f, 0.0f), 0.0f);
    EXPECT_FLOAT_EQ(divide(0.0f, 0.0f), 0.0f);
}

TEST(MathUtilsTest, DivideEdgeCases) {
    EXPECT_FLOAT_EQ(divide(0.0f, 5.0f), 0.0f);
    EXPECT_FLOAT_EQ(divide(FLT_MAX, 2.0f), FLT_MAX / 2.0f);
    EXPECT_FLOAT_EQ(divide(FLT_MIN, 2.0f), FLT_MIN / 2.0f);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}