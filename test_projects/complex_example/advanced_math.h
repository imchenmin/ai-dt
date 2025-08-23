#ifndef ADVANCED_MATH_H
#define ADVANCED_MATH_H

#include <vector>
#include <stdexcept>
#include <cmath>

// Template math utilities for advanced calculations
namespace AdvancedMath {

// Simple math exception class
class MathException : public std::runtime_error {
public:
    explicit MathException(const std::string& msg) : std::runtime_error(msg) {}
};

// Template vector operations
template<typename T>
class VectorMath {
public:
    static T dotProduct(const std::vector<T>& v1, const std::vector<T>& v2);
    static std::vector<T> crossProduct(const std::vector<T>& v1, const std::vector<T>& v2);
    static T magnitude(const std::vector<T>& vector);
    static std::vector<T> normalize(const std::vector<T>& vector);
};

// Advanced statistical functions
class Statistics {
public:
    template<typename T>
    static double mean(const std::vector<T>& data);
    
    template<typename T>
    static double standardDeviation(const std::vector<T>& data);
    
    template<typename T>
    static double variance(const std::vector<T>& data);
    
    // Outlier detection
    template<typename T>
    static std::vector<T> detectOutliers(const std::vector<T>& data, double threshold = 2.0);
};

// Complex number operations
struct Complex {
    double real;
    double imaginary;
    
    Complex(double r, double i) : real(r), imaginary(i) {}
    
    Complex operator+(const Complex& other) const;
    Complex operator-(const Complex& other) const;
    Complex operator*(const Complex& other) const;
    Complex operator/(const Complex& other) const;
    
    double magnitude() const;
    Complex conjugate() const;
};

// Matrix operations (simplified)
template<typename T, size_t Rows, size_t Cols>
class Matrix {
private:
    T data[Rows][Cols];
    
public:
    Matrix();
    explicit Matrix(const T& initialValue);
    
    T& operator()(size_t row, size_t col);
    const T& operator()(size_t row, size_t col) const;
    
    // Basic matrix operations
    Matrix<T, Rows, Cols> operator+(const Matrix<T, Rows, Cols>& other) const;
    Matrix<T, Rows, Cols> operator-(const Matrix<T, Rows, Cols>& other) const;
    
    template<size_t OtherCols>
    Matrix<T, Rows, OtherCols> operator*(const Matrix<T, Cols, OtherCols>& other) const;
    
    Matrix<T, Rows, Cols> operator*(const T& scalar) const;
    
    // Utility functions
    Matrix<T, Cols, Rows> transpose() const;
    bool isSquare() const { return Rows == Cols; }
    
    // For square matrices only
    T determinant() const;
    Matrix<T, Rows, Cols> inverse() const;
};

// Utility macros for configuration
#define MATH_PRECISION_HIGH 1e-12
#define MATH_PRECISION_MEDIUM 1e-8
#define MATH_PRECISION_LOW 1e-6

#define ENABLE_DEBUG_LOGGING
#ifdef ENABLE_DEBUG_LOGGING
    #define MATH_DEBUG(msg) std::cout << "[MATH_DEBUG] " << msg << std::endl
#else
    #define MATH_DEBUG(msg)
#endif

// Function declarations
double calculateCircleArea(double radius);
double calculateSphereVolume(double radius);
double* allocateDoubleArray(size_t size);
void freeDoubleArray(double* array);

// Error handling functions
const char* getLastMathError();
void clearMathError();

} // namespace AdvancedMath

#endif // ADVANCED_MATH_H