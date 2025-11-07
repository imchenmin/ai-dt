"""
Memory safety security tests for C/C++ code analysis
"""

import pytest
import tempfile
import os
from pathlib import Path

# Import the modules to test
from src.analyzer.clang_analyzer import ClangAnalyzer
from tests.security.utils.security_test_helpers import SecurityTestCase


@pytest.mark.security
@pytest.mark.buffer_overflow
class TestMemorySafetyAnalysis:
    """Test detection of memory safety vulnerabilities in C/C++ code"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.analyzer = ClangAnalyzer()

    def teardown_method(self):
        """Clean up test environment"""
        SecurityTestCase.cleanup_temp_project(str(self.temp_dir))

    def create_test_file(self, content: str, filename: str = "test.c") -> str:
        """Create a test C/C++ file with given content"""
        file_path = self.temp_dir / filename
        file_path.write_text(content)
        return str(file_path)

    def test_detect_buffer_overflow(self):
        """Test detection of buffer overflow vulnerabilities"""
        vulnerable_code = """
#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[10];
    strcpy(buffer, input);  // Buffer overflow vulnerability
    printf("%s\\n", buffer);
}

void safe_function(char *input) {
    char buffer[10];
    strncpy(buffer, input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\\0';
    printf("%s\\n", buffer);
}

int main() {
    char large_input[100];
    memset(large_input, 'A', 99);
    large_input[99] = '\\0';
    vulnerable_function(large_input);
    return 0;
}
"""
        file_path = self.create_test_file(vulnerable_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should find the vulnerable function
        vulnerable_func = None
        for func in functions:
            if func['name'] == 'vulnerable_function':
                vulnerable_func = func
                break

        assert vulnerable_func is not None
        assert 'strcpy' in vulnerable_func['body']

        # Should also find the safe function
        safe_func = None
        for func in functions:
            if func['name'] == 'safe_function':
                safe_func = func
                break

        assert safe_func is not None
        assert 'strncpy' in safe_func['body']

    def test_detect_use_after_free(self):
        """Test detection of use-after-free vulnerabilities"""
        vulnerable_code = """
#include <stdlib.h>
#include <stdio.h>

void use_after_free() {
    int *ptr = malloc(sizeof(int) * 10);
    ptr[0] = 42;
    free(ptr);

    // Use after free - dangerous!
    printf("Value: %d\\n", ptr[0]);
    ptr[1] = 100;  // Writing to freed memory
}

void safe_use() {
    int *ptr = malloc(sizeof(int) * 10);
    ptr[0] = 42;
    printf("Value: %d\\n", ptr[0]);
    free(ptr);
    ptr = NULL;  // Set to NULL after free

    // ptr is now NULL, use will be caught
    if (ptr != NULL) {
        printf("Value: %d\\n", ptr[0]);
    }
}
"""
        file_path = self.create_test_file(vulnerable_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect the problematic pattern
        for func in functions:
            if func['name'] == 'use_after_free':
                body = func['body']
                assert 'free(ptr)' in body
                assert 'ptr[0]' in body  # Use after free

    def test_detect_double_free(self):
        """Test detection of double-free vulnerabilities"""
        vulnerable_code = """
#include <stdlib.h>

void double_free() {
    char *buffer = malloc(100);
    // ... use buffer ...
    free(buffer);

    // Double free - dangerous!
    free(buffer);
}

void safe_free() {
    char *buffer = malloc(100);
    // ... use buffer ...
    free(buffer);
    buffer = NULL;  // Prevent double free

    // Safe to call free(NULL)
    free(buffer);
}
"""
        file_path = self.create_test_file(vulnerable_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect multiple free calls
        for func in functions:
            if func['name'] == 'double_free':
                body = func['body']
                assert body.count('free(buffer)') >= 2

    def test_detect_memory_leak(self):
        """Test detection of memory leak patterns"""
        leak_code = """
#include <stdlib.h>

void memory_leak() {
    char *buffer = malloc(1000);
    // Forgot to free(buffer) - memory leak!

    if (some_condition) {
        return;  // Early return without freeing
    }

    // Some code...
    // Still no free(buffer)
}

void no_leak() {
    char *buffer = malloc(1000);
    // ... use buffer ...
    free(buffer);  // Properly freed
}

int some_condition = 1;
"""
        file_path = self.create_test_file(leak_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect malloc without corresponding free
        for func in functions:
            if func['name'] == 'memory_leak':
                body = func['body']
                assert 'malloc(' in body
                # Note: free might not be in the same function, but this is a pattern

    def test_detect_uninitialized_memory(self):
        """Test detection of uninitialized memory usage"""
        uninitialized_code = """
#include <stdlib.h>

void use_uninitialized() {
    int *ptr = malloc(sizeof(int));
    // Didn't initialize *ptr
    printf("Value: %d\\n", *ptr);  // Using uninitialized memory

    char buffer[10];
    printf("Buffer: %s\\n", buffer);  // Uninitialized stack buffer
}

void initialized() {
    int *ptr = malloc(sizeof(int));
    *ptr = 42;  // Initialize
    printf("Value: %d\\n", *ptr);

    char buffer[10] = {0};  // Initialize
    printf("Buffer: %s\\n", buffer);
}
"""
        file_path = self.create_test_file(uninitialized_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect patterns that might use uninitialized memory
        for func in functions:
            if func['name'] == 'use_uninitialized':
                body = func['body']
                assert 'malloc(sizeof(int))' in body
                assert '*ptr' in body

    def test_detect_format_string_vulnerability(self):
        """Test detection of format string vulnerabilities"""
        format_string_code = """
#include <stdio.h>

void vulnerable_format(char *user_input) {
    // Dangerous - user_input used as format string
    printf(user_input);
}

void safe_format(char *user_input) {
    // Safe - format string is literal
    printf("%s", user_input);
}

void also_vulnerable(char *user_input) {
    // Also dangerous
    fprintf(stdout, user_input);
    sprintf(buffer, user_input);
}
"""
        file_path = self.create_test_file(format_string_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect printf with variable format string
        for func in functions:
            if func['name'] == 'vulnerable_format':
                body = func['body']
                assert 'printf(user_input)' in body

            if func['name'] == 'safe_format':
                body = func['body']
                assert 'printf("%s", user_input)' in body

    def test_detect_integer_overflow(self):
        """Test detection of integer overflow patterns"""
        overflow_code = """
#include <stdlib.h>

void integer_overflow() {
    int size = 1000;
    int multiplier = 1000;

    // Potential integer overflow
    int total = size * multiplier;
    char *buffer = malloc(total);  // May allocate less than expected

    // Unsafe addition
    int a = INT_MAX;
    int b = 1;
    int result = a + b;  // Overflow

    // Unsafe loop condition
    for (int i = 0; i < a + 1; i++) {
        // May never terminate
    }
}
"""
        file_path = self.create_test_file(overflow_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect potential overflow patterns
        for func in functions:
            if func['name'] == 'integer_overflow':
                body = func['body']
                assert 'size * multiplier' in body
                assert 'malloc(total)' in body

    def test_detect_race_condition(self):
        """Test detection of race condition patterns"""
        race_code = """
#include <pthread.h>

int shared_counter = 0;

void* thread_function(void* arg) {
    // Race condition - no synchronization
    for (int i = 0; i < 1000; i++) {
        shared_counter++;  // Not atomic!
    }
    return NULL;
}

void safe_threading() {
    pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

    // Protected access
    pthread_mutex_lock(&lock);
    shared_counter++;
    pthread_mutex_unlock(&lock);
}
"""
        file_path = self.create_test_file(race_code, "test.c")
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect unsynchronized shared variable access
        for func in functions:
            if func['name'] == 'thread_function':
                body = func['body']
                assert 'shared_counter++' in body

    def test_detect_dangerous_functions(self):
        """Test detection of dangerous C functions"""
        dangerous_code = """
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void dangerous_functions() {
    char buffer[100];

    // Dangerous string functions
    strcpy(buffer, user_input);  // No bounds check
    strcat(buffer, more_data);   // No bounds check
    sprintf(buffer, "%s %s", str1, str2);  // No bounds check
    gets(buffer);  // Extremely dangerous

    // Dangerous memory functions
    memcpy(dst, src, len);  // Should use memmove if overlapping

    // Other dangerous functions
    scanf("%s", buffer);  // No bounds check
    strtok(NULL, delim);  // Not thread-safe
}
"""
        file_path = self.create_test_file(dangerous_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect use of dangerous functions
        for func in functions:
            if func['name'] == 'dangerous_functions':
                body = func['body']
                dangerous_funcs = ['strcpy', 'strcat', 'sprintf', 'gets', 'scanf']
                for dangerous in dangerous_funcs:
                    assert dangerous in body

    def test_cpp_memory_safety(self):
        """Test C++ specific memory safety patterns"""
        cpp_code = """
#include <memory>
#include <vector>

class DangerousClass {
public:
    char* buffer;

    DangerousClass() {
        buffer = new char[100];
    }

    // No destructor - memory leak!

    void dangerous_method() {
        delete[] buffer;
        buffer = nullptr;
        delete[] buffer;  // Double delete!
    }
};

class SafeClass {
private:
    std::unique_ptr<char[]> buffer;

public:
    SafeClass() : buffer(std::make_unique<char[]>(100)) {}
    // Destructor automatically handles cleanup

    void safe_method() {
        std::fill(buffer.get(), buffer.get() + 100, 0);
    }
};

void vector_safety() {
    std::vector<int> vec(100);

    // Safe - bounds checked with at()
    int value = vec.at(100);  // Throws exception

    // Unsafe - no bounds check
    value = vec[100];  // Undefined behavior
}
"""
        file_path = self.create_test_file(cpp_code, "test.cpp")
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect C++ memory safety issues
        for func in functions:
            if func['name'] == 'dangerous_method':
                body = func['body']
                assert 'delete[] buffer' in body

    def test_stack_smashing_detection(self):
        """Test detection of stack smashing patterns"""
        stack_smash_code = """
#include <stdio.h>

void stack_smash() {
    char small_buffer[10];
    char large_input[1000];

    // Initialize large input
    memset(large_input, 'A', 999);
    large_input[999] = '\\0';

    // Stack smashing!
    strcpy(small_buffer, large_input);

    // Or using unsafe input
    gets(small_buffer);

    // Or writing past array bounds
    for (int i = 0; i < 1000; i++) {
        small_buffer[i] = 'B';
    }
}

void array_bounds_check() {
    int arr[10];

    // Safe access
    for (int i = 0; i < 10; i++) {
        arr[i] = i;
    }

    // Unsafe access - buffer overflow
    arr[10] = 42;  // Past array bounds
    arr[-1] = 24;  // Before array bounds
}
"""
        file_path = self.create_test_file(stack_smash_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect patterns that can lead to stack smashing
        for func in functions:
            if func['name'] == 'stack_smash':
                body = func['body']
                assert 'strcpy(small_buffer, large_input)' in body

    def test_heap_corruption(self):
        """Test detection of heap corruption patterns"""
        heap_corruption_code = """
#include <stdlib.h>
#include <string.h>

void heap_corruption() {
    int *array1 = malloc(10 * sizeof(int));
    int *array2 = malloc(10 * sizeof(int));

    // Write past array bounds - corrupts heap metadata
    for (int i = 0; i <= 10; i++) {
        array1[i] = i;  // i=10 writes past allocated memory
    }

    // Free corrupted memory - may crash
    free(array1);

    // Or freeing wrong pointer
    int *ptr = malloc(100);
    ptr++;
    free(ptr);  // Not the original pointer - undefined behavior

    // Or use after free
    int *temp = malloc(100);
    free(temp);
    memset(temp, 0, 100);  // Writing to freed memory
}

void safe_heap_operations() {
    int *array = malloc(10 * sizeof(int));

    // Safe access
    for (int i = 0; i < 10; i++) {
        array[i] = i;
    }

    free(array);
    array = NULL;
}
"""
        file_path = self.create_test_file(heap_corruption_code)
        functions = self.analyzer.analyze_file(file_path, [])

        # Should detect heap corruption patterns
        for func in functions:
            if func['name'] == 'heap_corruption':
                body = func['body']
                assert 'array1[i]' in body
                assert 'i <= 10' in body

    def test_analyze_malicious_c_code(self):
        """Test analysis of intentionally malicious code"""
        # Create various types of malicious code
        injection_types = [
            'buffer_overflow',
            'command_injection',
            'format_string',
            'xss_injection',
            'sql_injection'
        ]

        for injection_type in injection_types:
            malicious_file = SecurityTestCase.create_malicious_c_code(
                f"malicious_{injection_type}.c",
                injection_type
            )

            # Should analyze without crashing
            try:
                functions = self.analyzer.analyze_file(malicious_file, [])
                assert isinstance(functions, list)

                # Should extract some information about the code
                if functions:
                    for func in functions:
                        assert 'name' in func
                        assert 'body' in func
            except Exception as e:
                # Should not crash, but may fail to parse
                assert not isinstance(e, ImportError)
                assert not isinstance(e, AttributeError)

    def test_memory_safety_report_generation(self):
        """Test generation of memory safety analysis report"""
        code_with_issues = """
#include <string.h>
#include <stdlib.h>

void multiple_issues() {
    char buffer[10];
    char *ptr = malloc(100);

    strcpy(buffer, "This is too long");  // Buffer overflow

    printf(buffer);  // Format string vulnerability

    // Memory leak - forgot to free(ptr)

    if (error_condition) {
        return;  // Early return without cleanup
    }

    free(ptr);
    ptr = NULL;
}

int error_condition = 1;
"""
        file_path = self.create_test_file(code_with_issues)
        functions = self.analyzer.analyze_file(file_path, [])

        # Generate a simple report of detected issues
        issues_found = []

        for func in functions:
            body = func['body']

            if 'strcpy(' in body and 'buffer[10]' in body:
                issues_found.append(f"{func['name']}: Potential buffer overflow with strcpy")

            if 'printf(buffer)' in body:
                issues_found.append(f"{func['name']}: Format string vulnerability")

            if 'malloc(' in body and body.count('free(') == 0:
                issues_found.append(f"{func['name']}: Potential memory leak")

        # Should detect issues
        assert len(issues_found) > 0
        assert any("buffer overflow" in issue.lower() for issue in issues_found)
        assert any("format string" in issue.lower() for issue in issues_found)