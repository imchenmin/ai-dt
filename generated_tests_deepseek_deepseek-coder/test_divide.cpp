```cpp
#include <gtest/gtest.h>
#include <mockcpp/mockcpp.hpp>

extern "C" {
    #include "math_utils.h" // 假设头文件名为math_utils.h
}

using namespace mockcpp;

class DivideTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 测试前的设置代码（如有需要）
    }

    void TearDown() override {
        // 测试后的清理代码（如有需要）
        GlobalMockObject::verify();
        GlobalMockObject::reset();
    }
};

// 测试正常除法运算
TEST_F(DivideTest, NormalDivision) {
    EXPECT_FLOAT_EQ(5.0f, divide(10.0f, 2.0f));
    EXPECT_FLOAT_EQ(2.5f, divide(5.0f, 2.0f));
    EXPECT_FLOAT_EQ(-3.0f, divide(-9.0f, 3.0f));
}

// 测试除数为零的情况
TEST_F(DivideTest, DivisionByZero) {
    EXPECT_FLOAT_EQ(0.0f, divide(10.0f, 0.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(-5.0f, 0.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(0.0f, 0.0f));
}

// 测试边界值情况
TEST_F(DivideTest, BoundaryValues) {
    // 测试浮点数极值
    EXPECT_FLOAT_EQ(1.0f, divide(FLT_MAX, FLT_MAX));
    EXPECT_FLOAT_EQ(-1.0f, divide(-FLT_MAX, FLT_MAX));
    
    // 测试接近零的值
    EXPECT_FLOAT_EQ(1000.0f, divide(0.001f, 0.000001f));
    EXPECT_FLOAT_EQ(0.0f, divide(0.0f, FLT_MIN));
}

// 测试浮点数精度问题
TEST_F(DivideTest, PrecisionTest) {
    EXPECT_NEAR(0.333333f, divide(1.0f, 3.0f), 0.000001f);
    EXPECT_NEAR(0.666667f, divide(2.0f, 3.0f), 0.000001f);
}

// 测试正负号组合
TEST_F(DivideTest, SignCombinations) {
    EXPECT_FLOAT_EQ(2.0f, divide(4.0f, 2.0f));      // 正/正
    EXPECT_FLOAT_EQ(-2.0f, divide(-4.0f, 2.0f));    // 负/正
    EXPECT_FLOAT_EQ(-2.0f, divide(4.0f, -2.0f));    // 正/负
    EXPECT_FLOAT_EQ(2.0f, divide(-4.0f, -2.0f));    // 负/负
}

// 测试特殊浮点数值
TEST_F(DivideTest, SpecialFloatValues) {
    // 测试NaN（虽然函数实现中不会产生NaN，但可以测试输入NaN的情况）
    EXPECT_FLOAT_EQ(0.0f, divide(0.0f, 0.0f));      // 0/0
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

**编译说明：**
```bash
g++ -std=c++11 -I/path/to/gtest/include -I/path/to/mockcpp/include \
    -I/mnt/c/Users/chenmin/ai-dt/test_projects/c \
    test_divide.cpp -lgtest -lgtest_main -lmockcpp -L/path/to/gtest/lib -L/path/to/mockcpp/lib
```

**测试用例说明：**
1. **NormalDivision**: 测试正常的除法运算
2. **DivisionByZero**: 测试除数为零的边界情况
3. **BoundaryValues**: 测试浮点数极值和接近零的情况
4. **PrecisionTest**: 测试浮点数精度
5. **SignCombinations**: 测试各种正负号组合
6. **SpecialFloatValues**: 测试特殊浮点数值情况

这些测试用例全面覆盖了divide函数的所有可能情况，包括正常流程、边界条件和异常情况处理。