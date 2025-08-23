#include "advanced_math.h"
#include <iostream>
#include <numeric>
#include <algorithm>
#include <limits>

namespace AdvancedMath {

// Thread-local error storage
thread_local std::string lastMathError;

const char* getLastMathError() {
    return lastMathError.c_str();
}

void clearMathError() {
    lastMathError.clear();
}

// Template vector operations implementation
template<typename T>
T VectorMath<T>::dotProduct(const std::vector<T>& v1, const std::vector<T>& v2) {
    if (v1.size() != v2.size()) {
        lastMathError = "Vector sizes don't match for dot product";
        throw MathException(lastMathError);
    }
    
    T result = 0;
    for (size_t i = 0; i < v1.size(); ++i) {
        result += v1[i] * v2[i];
    }
    return result;
}

template<typename T>
std::vector<T> VectorMath<T>::crossProduct(const std::vector<T>& v1, const std::vector<T>& v2) {
    if (v1.size() != 3 || v2.size() != 3) {
        lastMathError = "Cross product requires 3D vectors";
        throw MathException(lastMathError);
    }
    
    return {
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0]
    };
}

template<typename T>
T VectorMath<T>::magnitude(const std::vector<T>& vector) {
    if (vector.empty()) {
        return 0;
    }
    
    T sum = 0;
    for (const auto& val : vector) {
        sum += val * val;
    }
    return std::sqrt(sum);
}

template<typename T>
std::vector<T> VectorMath<T>::normalize(const std::vector<T>& vector) {
    T mag = magnitude(vector);
    if (mag < MATH_PRECISION_HIGH) {
        lastMathError = "Cannot normalize zero vector";
        throw MathException(lastMathError);
    }
    
    std::vector<T> result;
    result.reserve(vector.size());
    for (const auto& val : vector) {
        result.push_back(val / mag);
    }
    return result;
}

// Statistics implementation
template<typename T>
double Statistics::mean(const std::vector<T>& data) {
    if (data.empty()) {
        lastMathError = "Cannot calculate mean of empty dataset";
        throw MathException(lastMathError);
    }
    
    double sum = std::accumulate(data.begin(), data.end(), 0.0);
    return sum / data.size();
}

template<typename T>
double Statistics::variance(const std::vector<T>& data) {
    if (data.size() < 2) {
        lastMathError = "Variance requires at least 2 data points";
        throw MathException(lastMathError);
    }
    
    double mean_val = mean(data);
    double sum = 0.0;
    for (const auto& val : data) {
        sum += (val - mean_val) * (val - mean_val);
    }
    return sum / (data.size() - 1);
}

template<typename T>
double Statistics::standardDeviation(const std::vector<T>& data) {
    return std::sqrt(variance(data));
}

template<typename T>
std::vector<T> Statistics::detectOutliers(const std::vector<T>& data, double threshold) {
    if (data.empty()) {
        return {};
    }
    
    double mean_val = mean(data);
    double std_dev = standardDeviation(data);
    
    std::vector<T> outliers;
    for (const auto& val : data) {
        if (std::abs(val - mean_val) > threshold * std_dev) {
            outliers.push_back(val);
        }
    }
    return outliers;
}

// Complex number operations
Complex Complex::operator+(const Complex& other) const {
    return {real + other.real, imaginary + other.imaginary};
}

Complex Complex::operator-(const Complex& other) const {
    return {real - other.real, imaginary - other.imaginary};
}

Complex Complex::operator*(const Complex& other) const {
    return {
        real * other.real - imaginary * other.imaginary,
        real * other.imaginary + imaginary * other.real
    };
}

Complex Complex::operator/(const Complex& other) const {
    double denominator = other.real * other.real + other.imaginary * other.imaginary;
    if (denominator < MATH_PRECISION_HIGH) {
        lastMathError = "Division by zero in complex number operation";
        throw MathException(lastMathError);
    }
    
    return {
        (real * other.real + imaginary * other.imaginary) / denominator,
        (imaginary * other.real - real * other.imaginary) / denominator
    };
}

double Complex::magnitude() const {
    return std::sqrt(real * real + imaginary * imaginary);
}

Complex Complex::conjugate() const {
    return {real, -imaginary};
}

// Matrix implementation
template<typename T, size_t Rows, size_t Cols>
Matrix<T, Rows, Cols>::Matrix() {
    for (size_t i = 0; i < Rows; ++i) {
        for (size_t j = 0; j < Cols; ++j) {
            data[i][j] = T{};
        }
    }
}

template<typename T, size_t Rows, size_t Cols>
Matrix<T, Rows, Cols>::Matrix(const T& initialValue) {
    for (size_t i = 0; i < Rows; ++i) {
        for (size_t j = 0; j < Cols; ++j) {
            data[i][j] = initialValue;
        }
    }
}

template<typename T, size_t Rows, size_t Cols>
T& Matrix<T, Rows, Cols>::operator()(size_t row, size_t col) {
    if (row >= Rows || col >= Cols) {
        lastMathError = "Matrix index out of bounds";
        throw MathException(lastMathError);
    }
    return data[row][col];
}

template<typename T, size_t Rows, size_t Cols>
const T& Matrix<T, Rows, Cols>::operator()(size_t row, size_t col) const {
    if (row >= Rows || col >= Cols) {
        lastMathError = "Matrix index out of bounds";
        throw MathException(lastMathError);
    }
    return data[row][col];
}

// Explicit template instantiations
template class VectorMath<double>;
template class VectorMath<float>;
template class VectorMath<int>;

// Explicit template instantiation for Statistics functions
template double Statistics::mean<double>(const std::vector<double>&);
template double Statistics::mean<float>(const std::vector<float>&);
template double Statistics::mean<int>(const std::vector<int>&);

template double Statistics::variance<double>(const std::vector<double>&);
template double Statistics::variance<float>(const std::vector<float>&);
template double Statistics::variance<int>(const std::vector<int>&);

template double Statistics::standardDeviation<double>(const std::vector<double>&);
template double Statistics::standardDeviation<float>(const std::vector<float>&);
template double Statistics::standardDeviation<int>(const std::vector<int>&);

template std::vector<double> Statistics::detectOutliers<double>(const std::vector<double>&, double);
template std::vector<float> Statistics::detectOutliers<float>(const std::vector<float>&, double);
template std::vector<int> Statistics::detectOutliers<int>(const std::vector<int>&, double);

// Simple geometry functions
double calculateCircleArea(double radius) {
    if (radius < 0) {
        lastMathError = "Radius cannot be negative";
        throw MathException(lastMathError);
    }
    return M_PI * radius * radius;
}

double calculateSphereVolume(double radius) {
    if (radius < 0) {
        lastMathError = "Radius cannot be negative";
        throw MathException(lastMathError);
    }
    return (4.0 / 3.0) * M_PI * radius * radius * radius;
}

double* allocateDoubleArray(size_t size) {
    if (size == 0) {
        return nullptr;
    }
    return new double[size];
}

void freeDoubleArray(double* array) {
    delete[] array;
}

} // namespace AdvancedMath