#include <gtest/gtest.h>
#include <mockcpp/mockcpp.hpp>
#include <cmath>
#include <stdexcept>

// 包含被测试函数的头文件
#include "advanced_math.h"

using namespace std;
using namespace testing;

// 定义异常类（根据实际实现调整）
class MathException : public std::runtime_error {
public:
    MathException(const std::string& msg) : std::runtime_error(msg) {}
};

// 声明外部变量（根据实际实现调整）
extern std::string lastMathError;

class CalculateSphereVolumeTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 每个测试用例前的设置
    }

    void TearDown() override {
        // 每个测试用例后的清理
    }
};

// 正常流程测试
TEST_F(CalculateSphereVolumeTest, PositiveRadiusReturnsCorrectVolume) {
    // 测试正常正数半径
    double radius = 3.0;
    double expected = (4.0 / 3.0) * M_PI * radius * radius * radius;
    
    EXPECT_NEAR(calculateSphereVolume(radius), expected, 1e-10);
}

TEST_F(CalculateSphereVolumeTest, LargeRadiusReturnsCorrectVolume) {
    // 测试大数值半径
    double radius = 1000.0;
    double expected = (4.0 / 3.0) * M_PI * radius * radius * radius;
    
    EXPECT_NEAR(calculateSphereVolume(radius), expected, 1e-10);
}

TEST_F(CalculateSphereVolumeTest, SmallPositiveRadiusReturnsCorrectVolume) {
    // 测试小数值正数半径
    double radius = 0.001;
    double expected = (4.0 / 3.0) * M_PI * radius * radius * radius;
    
    EXPECT_NEAR(calculateSphereVolume(radius), expected, 1e-15);
}

// 边界条件测试
TEST_F(CalculateSphereVolumeTest, ZeroRadiusReturnsZero) {
    // 测试零半径
    EXPECT_DOUBLE_EQ(calculateSphereVolume(0.0), 0.0);
}

// 异常情况处理测试
TEST_F(CalculateSphereVolumeTest, NegativeRadiusThrowsException) {
    // 测试负数半径抛出异常
    EXPECT_THROW({
        calculateSphereVolume(-1.0);
    }, MathException);
}

TEST_F(CalculateSphereVolumeTest, VeryNegativeRadiusThrowsException) {
    // 测试很大的负数半径抛出异常
    EXPECT_THROW({
        calculateSphereVolume(-1000.0);
    }, MathException);
}

TEST_F(CalculateSphereVolumeTest, NegativeRadiusSetsErrorMessage) {
    // 测试异常消息设置
    try {
        calculateSphereVolume(-5.0);
        FAIL() << "Expected MathException";
    } catch (const MathException& e) {
        EXPECT_STREQ(e.what(), "Radius cannot be negative");
    }
}

// 浮点数精度边界测试
TEST_F(CalculateSphereVolumeTest, VerySmallPositiveRadius) {
    // 测试极小正数半径
    double radius = 1e-10;
    double expected = (4.0 / 3.0) * M_PI * radius * radius * radius;
    
    EXPECT_NEAR(calculateSphereVolume(radius), expected, 1e-30);
}

// 主函数
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}