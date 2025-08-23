#include "advanced_math.h"
#include <iostream>
#include <vector>

using namespace AdvancedMath;

void demonstrateVectorMath() {
    std::cout << "=== Vector Math Demo ===" << std::endl;
    
    std::vector<double> v1 = {1.0, 2.0, 3.0};
    std::vector<double> v2 = {4.0, 5.0, 6.0};
    
    try {
        double dot = VectorMath<double>::dotProduct(v1, v2);
        std::cout << "Dot product: " << dot << std::endl;
        
        auto cross = VectorMath<double>::crossProduct(v1, v2);
        std::cout << "Cross product: {" 
                  << cross[0] << ", " << cross[1] << ", " << cross[2] << "}" << std::endl;
        
        double mag = VectorMath<double>::magnitude(v1);
        std::cout << "Magnitude of v1: " << mag << std::endl;
        
        auto normalized = VectorMath<double>::normalize(v1);
        std::cout << "Normalized v1: {" 
                  << normalized[0] << ", " << normalized[1] << ", " << normalized[2] << "}" << std::endl;
        
    } catch (const MathException& e) {
        std::cerr << "Math error: " << e.what() << std::endl;
    }
}

void demonstrateStatistics() {
    std::cout << "\n=== Statistics Demo ===" << std::endl;
    
    std::vector<double> data = {1.2, 2.3, 3.4, 4.5, 5.6, 100.0}; // 100 is an outlier
    
    try {
        double mean_val = Statistics::mean(data);
        double std_dev = Statistics::standardDeviation(data);
        auto outliers = Statistics::detectOutliers(data, 2.0);
        
        std::cout << "Mean: " << mean_val << std::endl;
        std::cout << "Standard deviation: " << std_dev << std::endl;
        std::cout << "Outliers: ";
        for (auto outlier : outliers) {
            std::cout << outlier << " ";
        }
        std::cout << std::endl;
        
    } catch (const MathException& e) {
        std::cerr << "Statistics error: " << e.what() << std::endl;
    }
}

void demonstrateComplexNumbers() {
    std::cout << "\n=== Complex Numbers Demo ===" << std::endl;
    
    Complex c1(3.0, 4.0);
    Complex c2(1.0, 2.0);
    
    try {
        Complex sum = c1 + c2;
        Complex product = c1 * c2;
        Complex quotient = c1 / c2;
        
        std::cout << "c1 + c2 = (" << sum.real << ", " << sum.imaginary << "i)" << std::endl;
        std::cout << "c1 * c2 = (" << product.real << ", " << product.imaginary << "i)" << std::endl;
        std::cout << "c1 / c2 = (" << quotient.real << ", " << quotient.imaginary << "i)" << std::endl;
        std::cout << "|c1| = " << c1.magnitude() << std::endl;
        
    } catch (const MathException& e) {
        std::cerr << "Complex math error: " << e.what() << std::endl;
    }
}

void demonstrateGeometry() {
    std::cout << "\n=== Geometry Demo ===" << std::endl;
    
    try {
        double area = calculateCircleArea(5.0);
        double volume = calculateSphereVolume(3.0);
        
        std::cout << "Circle area (r=5): " << area << std::endl;
        std::cout << "Sphere volume (r=3): " << volume << std::endl;
        
        // Test error case - just call to trigger exception
        calculateCircleArea(-1.0);
        
    } catch (const MathException& e) {
        std::cout << "Expected error: " << e.what() << std::endl;
    }
}

void demonstrateMemoryManagement() {
    std::cout << "\n=== Memory Management Demo ===" << std::endl;
    
    double* array = allocateDoubleArray(10);
    if (array) {
        for (int i = 0; i < 10; ++i) {
            array[i] = i * 1.1;
        }
        
        std::cout << "Allocated array: ";
        for (int i = 0; i < 10; ++i) {
            std::cout << array[i] << " ";
        }
        std::cout << std::endl;
        
        freeDoubleArray(array);
        std::cout << "Array freed successfully" << std::endl;
    }
}

int main() {
    std::cout << "Advanced Math Library Demonstration" << std::endl;
    std::cout << "==================================" << std::endl;
    
    demonstrateVectorMath();
    demonstrateStatistics();
    demonstrateComplexNumbers();
    demonstrateGeometry();
    demonstrateMemoryManagement();
    
    std::cout << "\nDemo completed successfully!" << std::endl;
    return 0;
}