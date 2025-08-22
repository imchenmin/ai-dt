cmake_minimum_required(VERSION 3.10)
project(Calculator CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable compile commands export
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Add executable
add_executable(calculator_demo main.cpp calculator.cpp)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})