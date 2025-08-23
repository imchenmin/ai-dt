cmake_minimum_required(VERSION 3.10)
project(AdvancedMathDemo)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add executable
add_executable(advanced_math_demo
    main.cpp
    advanced_math.cpp
)

# Include directories
target_include_directories(advanced_math_demo PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Compilation flags
target_compile_options(advanced_math_demo PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Werror
    -O2
)

# Link libraries if needed
target_link_libraries(advanced_math_demo)