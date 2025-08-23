#include <gtest/gtest.h>
#include <mockcpp/mockcpp.hpp>
#include <cmath>
#include <stdexcept>

// 假设的异常类定义（根据实际代码调整）
class MathException : public std::exception {
private:
    std::string message;
public:
    explicit MathException(const std::string& msg) : message(msg) {}
    const char* what() const noexcept override {
        return message.c_str();
    }
};

// 假设的全局变量（根据实际代码调整）
extern std::string lastMathError;

// 声明被测试函数
double calculateCircleArea(double radius);

class CalculateCircleAreaTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 测试前的设置
    }

    void TearDown() override {
        // 测试后的清理
    }
};

// 正常流程测试
TEST_F(CalculateCircleAreaTest, PositiveRadiusReturnsCorrectArea) {
    // 测试正常半径值
    double radius = 5.0;
    double expected = M_PI * radius * radius;
    double actual = calculateCircleArea(radius);
    
    EXPECT_DOUBLE_EQ(expected, actual);
}

TEST_F(CalculateCircleAreaTest, ZeroRadiusReturnsZero) {
    // 测试边界条件：半径为0
    double radius = 0.0;
    double expected = 0.0;
    double actual = calculateCircleArea(radius);
    
    EXPECT_DOUBLE_EQ(expected, actual);
}

TEST_F(CalculateCircleAreaTest, SmallPositiveRadiusReturnsCorrectArea) {
    // 测试小正数边界条件
    double radius = 0.001;
    double expected = M_PI * radius * radius;
    double actual = calculateCircleArea(radius);
    
    EXPECT_NEAR(expected, actual, 1e-12);
}

TEST_F(CalculateCircleAreaTest, LargeRadiusReturnsCorrectArea) {
    // 测试大数边界条件
    double radius = 1e6;
    double expected = M_PI * radius * radius;
    double actual = calculateCircleArea(radius);
    
    EXPECT_NEAR(expected, actual, 1e-6);
}

// 异常情况测试
TEST_F(CalculateCircleAreaTest, NegativeRadiusThrowsException) {
    // 测试负半径抛出异常
    double radius = -1.0;
    
    EXPECT_THROW({
        calculateCircleArea(radius);
    }, MathException);
}

TEST_F(CalculateCircleAreaTest, VeryNegativeRadiusThrowsException) {
    // 测试非常负的半径抛出异常
    double radius = -1e6;
    
    EXPECT_THROW({
        calculateCircleArea(radius);
    }, MathException);
}

TEST_F(CalculateCircleAreaTest, NegativeRadiusSetsErrorMessage) {
    // 测试异常消息设置
    double radius = -2.5;
    
    try {
        calculateCircleArea(radius);
        FAIL() << "Expected MathException to be thrown";
    } catch (const MathException& e) {
        EXPECT_STREQ("Radius cannot be negative", e.what());
    }
}

// 浮点数精度边界测试
TEST_F(CalculateCircleAreaTest, FloatingPointPrecisionEdgeCases) {
    // 测试浮点数精度边界
    std::vector<double> testCases = {
        1e-10,  // 极小正数
        1e-5,   // 小正数
        1.0,    // 单位值
        1e5,    // 大正数
        1e10    // 极大正数
    };
    
    for (double radius : testCases) {
        double expected = M_PI * radius * radius;
        double actual = calculateCircleArea(radius);
        
        // 使用相对误差比较，适应不同数量级
        double relativeError = std::abs((actual - expected) / expected);
        EXPECT_LT(relativeError, 1e-12) << "Failed for radius: " << radius;
    }
}

// 特殊值测试
TEST_F(CalculateCircleAreaTest, SpecialValues) {
    // 测试特殊数学常数
    double radius = M_PI;
    double expected = M_PI * M_PI * M_PI;
    double actual = calculateCircleArea(radius);
    
    EXPECT_NEAR(expected, actual, 1e-12);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}