#include <gtest/gtest.h>
#include "../../utils.h"

class utils_test : public ::testing::Test {
protected:
    void SetUp() override {
        //h
    }

    void TearDown() override {
    }
};

TEST_F(utils_test, process_data_When_PositiveInput_Should_ReturnDouble) {
    int input = 10;
    int expected_output = 20;
    int actual_output = process_data(input);
    EXPECT_EQ(expected_output, actual_output);
}