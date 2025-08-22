#ifndef CALCULATOR_H
#define CALCULATOR_H

#include <string>

class Calculator {
public:
    Calculator();
    
    // Public methods (should be testable)
    int add(int a, int b);
    double add(double a, double b);
    int subtract(int a, int b);
    
    // Static method (should be testable)
    static int getInstanceCount();
    
private:
    // Private method (should be testable via symbol hijacking)
    void logOperation(const std::string& operation);
    
    int instanceId;
    static int instanceCount;
};

// Free function (should be testable)
std::string formatResult(int result);

#endif // CALCULATOR_H