#include "calculator.h"
#include <iostream>

int main() {
    Calculator calc1;
    Calculator calc2;
    
    int sum = calc1.add(10, 20);
    std::cout << "10 + 20 = " << sum << std::endl;
    
    int diff = calc2.subtract(50, 15);
    std::cout << "50 - 15 = " << diff << std::endl;
    
    std::string formatted = formatResult(sum);
    std::cout << formatted << std::endl;
    
    std::cout << "Total instances: " << Calculator::getInstanceCount() << std::endl;
    
    return 0;
}