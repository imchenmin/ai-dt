cmake_minimum_required(VERSION 3.10)
project(simple_c_project LANGUAGES C)

# Set C standard if not set
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Export compile commands for tooling
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Add the library
add_library(utils_lib STATIC utils.c)

# Add the executable
add_executable(simple_c_project main.c)

# Link the library to the executable
target_link_libraries(simple_c_project PRIVATE utils_lib)

# Include current directory for headers
target_include_directories(simple_c_project PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(utils_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})