#include "calculator.h"
#include <iostream>
#include <sstream>

int Calculator::instanceCount = 0;

Calculator::Calculator() : instanceId(++instanceCount) {
    logOperation("Calculator created");
}

int Calculator::add(int a, int b) {
    logOperation("integer addition");
    return a + b;
}

double Calculator::add(double a, double b) {
    logOperation("double addition");
    return a + b;
}

int Calculator::subtract(int a, int b) {
    logOperation("subtraction");
    return a - b;
}

int Calculator::getInstanceCount() {
    return instanceCount;
}

void Calculator::logOperation(const std::string& operation) {
    std::cout << "Calculator " << instanceId << ": " << operation << std::endl;
}

std::string formatResult(int result) {
    std::ostringstream ss;
    ss << "Result: " << result;
    return ss.str();
}