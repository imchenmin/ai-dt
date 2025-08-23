#!/bin/bash

# Test compilation script for generated tests

echo "Compiling generated tests..."

# Set up include paths
INCLUDE_DIRS="-I. -I/mnt/c/Users/chenmin/ai-dt/test_projects/complex_c_project -I/mnt/c/Users/chenmin/ai-dt/test_projects/complex_c_project/data_structures -I/mnt/c/Users/chenmin/ai-dt/test_projects/complex_c_project/utils"

# Try to compile each test file
for test_file in test_*.cpp; do
    echo "Compiling $test_file..."
    
    # Create a simple test executable
    g++ -std=c++11 $INCLUDE_DIRS -lgtest -lgtest_main -pthread \
        "$test_file" \
        /mnt/c/Users/chenmin/ai-dt/test_projects/complex_c_project/data_structures/linked_list.c \
        -o "${test_file%.cpp}_test" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Success: $test_file compiled"
        # Clean up
        rm -f "${test_file%.cpp}_test"
    else
        echo "  ✗ Failed: $test_file compilation failed"
    fi
done

echo "Test compilation completed!"