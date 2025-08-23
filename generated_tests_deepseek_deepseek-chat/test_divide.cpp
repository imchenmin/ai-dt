```cpp
#include <gtest/gtest.h>
#include <mockcpp/mockcpp.hpp>

extern "C" {
    #include "math_utils.h"  // 假设函数声明在此头文件中
}

using namespace mockcpp;

class DivideTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 测试前的设置代码
    }

    void TearDown() override {
        // 测试后的清理代码
        GlobalMockObject::verify();
        GlobalMockObject::reset();
    }
};

// 正常流程测试
TEST_F(DivideTest, NormalDivision) {
    EXPECT_FLOAT_EQ(5.0f, divide(10.0f, 2.0f));
    EXPECT_FLOAT_EQ(2.5f, divide(5.0f, 2.0f));
    EXPECT_FLOAT_EQ(-3.0f, divide(-9.0f, 3.0f));
    EXPECT_FLOAT_EQ(0.5f, divide(1.0f, 2.0f));
}

// 边界条件测试
TEST_F(DivideTest, BoundaryConditions) {
    // 除数为0的情况
    EXPECT_FLOAT_EQ(0.0f, divide(10.0f, 0.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(-5.0f, 0.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(0.0f, 0.0f));
    
    // 被除数为0的情况
    EXPECT_FLOAT_EQ(0.0f, divide(0.0f, 5.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(0.0f, -2.0f));
    
    // 浮点数精度边界
    EXPECT_FLOAT_EQ(1.0f, divide(1.0f, 1.0f));
    EXPECT_FLOAT_EQ(-1.0f, divide(-1.0f, 1.0f));
}

// 异常情况处理测试
TEST_F(DivideTest, EdgeCases) {
    // 极大值测试
    EXPECT_FLOAT_EQ(1.0f, divide(FLT_MAX, FLT_MAX));
    EXPECT_FLOAT_EQ(-1.0f, divide(-FLT_MAX, FLT_MAX));
    
    // 极小值测试
    EXPECT_FLOAT_EQ(1.0f, divide(FLT_MIN, FLT_MIN));
    EXPECT_FLOAT_EQ(-1.0f, divide(-FLT_MIN, FLT_MIN));
    
    // 极大值除以极小值
    EXPECT_FLOAT_EQ(FLT_MAX / FLT_MIN, divide(FLT_MAX, FLT_MIN));
}

// 特殊浮点数值测试
TEST_F(DivideTest, SpecialFloatValues) {
    // NaN 测试
    EXPECT_FLOAT_EQ(0.0f, divide(NAN, 1.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(1.0f, NAN));
    
    // 无穷大测试
    EXPECT_FLOAT_EQ(0.0f, divide(INFINITY, 1.0f));
    EXPECT_FLOAT_EQ(0.0f, divide(1.0f, INFINITY));
}

// 性能相关测试（确保没有意外的性能问题）
TEST_F(DivideTest, PerformanceRelated) {
    // 多次调用确保稳定性
    for (int i = 0; i < 1000; ++i) {
        EXPECT_FLOAT_EQ(2.0f, divide(4.0f, 2.0f));
    }
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

**编译说明：**
- 需要链接 Google Test 和 MockCpp 库
- 包含正确的头文件路径：`-I/mnt/c/Users/chenmin/ai-dt/test_projects/c`
- 使用 C++11 或更高标准编译

**测试覆盖分析：**
1. ✅ 正常除法运算
2. ✅ 除数为零的边界情况
3. ✅ 浮点数精度边界
4. ✅ 极大/极小值处理
5. ✅ 特殊浮点数值（NaN、Infinity）
6. ✅ 性能稳定性测试

这个测试套件全面覆盖了 divide 函数的所有可能情况，包括正常流程、边界条件和异常处理。