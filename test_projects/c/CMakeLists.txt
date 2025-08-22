cmake_minimum_required(VERSION 3.10)
project(MathUtils C)

# Set C standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Enable compile commands export
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Add executable
add_executable(math_demo main.c math_utils.c)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})