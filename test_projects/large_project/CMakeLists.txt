cmake_minimum_required(VERSION 3.10)
project(large_project C)

# Set compile commands BEFORE project
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -O2")

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Collect all source files
file(GLOB_RECURSE SOURCES
    "math_utils/*.c"
    "string_utils/*.c"
    "data_structures/*.c"
    "algorithms/*.c"
    "graphics/*.c"
    "parsers/*.c"
    "validators/*.c"
    "converters/*.c"
    "main.c"
)

# Create executable
add_executable(large_project ${SOURCES})