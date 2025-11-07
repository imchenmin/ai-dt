"""
Edge case tests for C/C++ components to ensure robustness
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import the modules to test
from src.analyzer.clang_analyzer import ClangAnalyzer
from src.utils.compile_db_generator import CompileDBGenerator
from src.utils.prompt_template_loader import PromptTemplateLoader, TemplateValidationError
from tests.security.utils.security_test_helpers import SecurityTestCase


@pytest.mark.security
class TestEdgeCases:
    """Test edge cases and boundary conditions in C/C++ components"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment"""
        SecurityTestCase.cleanup_temp_project(str(self.temp_dir))

    # =============== Clang Analyzer Edge Cases ===============

    def test_analyze_empty_file(self):
        """Test analysis of empty files"""
        empty_file = self.temp_dir / "empty.c"
        empty_file.write_text("")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(empty_file), [])
        assert functions == []

    def test_analyze_file_with_only_comments(self):
        """Test analysis of files with only comments"""
        comment_file = self.temp_dir / "comments.c"
        comment_file.write_text("""
/*
 * This file contains only comments
 * No actual code
 */
// Single line comment
/* Multi-line
   comment */
""")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(comment_file), [])
        assert functions == []

    def test_analyze_file_with_syntax_errors(self):
        """Test analysis of files with syntax errors"""
        syntax_error_file = self.temp_dir / "syntax_error.c"
        syntax_error_file.write_text("""
int main() {
    printf("Hello
    return 0  // Missing semicolon
    // Unclosed brace
""")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(syntax_error_file), [])
        # Should return empty list or handle gracefully
        assert isinstance(functions, list)

    def test_analyze_very_large_file(self):
        """Test analysis of very large files"""
        large_file = self.temp_dir / "large.c"
        # Create a file with many functions
        content = ["#include <stdio.h>\\n"]
        for i in range(1000):
            content.append(f"""
int function_{i}(int x) {{
    return x * {i};
}}

int another_function_{i}(int a, int b) {{
    return a + b + {i};
}}
""")

        large_file.write_text("".join(content))

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(large_file), [])

        # Should find many functions
        assert len(functions) == 2000
        # Should handle memory gracefully
        assert all('name' in func for func in functions)

    def test_analyze_file_with_unicode_content(self):
        """Test analysis of files with Unicode content"""
        unicode_file = self.temp_dir / "unicode.c"
        unicode_file.write_text("""
#include <stdio.h>

// Comments with Unicode: 你好世界 🌍 café résumé
int test_unicode() {
    char *msg = "Hello 世界";
    printf("%s\\n", msg);
    return 0;
}

// Function with Unicode in name (invalid in C but test edge case)
int 测试函数() {
    return 42;
}
""")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(unicode_file), [])

        # Should find valid functions
        valid_funcs = [f for f in functions if f['name'] == 'test_unicode']
        assert len(valid_funcs) > 0

    def test_analyze_file_with_nested_structures(self):
        """Test analysis of files with deeply nested structures"""
        nested_file = self.temp_dir / "nested.c"
        nested_file.write_text("""
struct Level1 {
    struct Level2 {
        struct Level3 {
            struct Level4 {
                struct Level5 {
                    int value;
                } level5;
            } level4;
        } level3;
    } level2;
} level1;

int nested_function(struct Level1 *l1) {
    return l1->level2.level3.level4.level5.value;
}
""")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(nested_file), [])

        # Should handle nested structures
        nested_func = [f for f in functions if f['name'] == 'nested_function']
        assert len(nested_func) > 0

    def test_analyze_file_with_macros(self):
        """Test analysis of files with complex macros"""
        macro_file = self.temp_dir / "macros.c"
        macro_file.write_text("""
#define COMPLEX_MACRO(x, y) \\
    do { \\
        if ((x) != NULL) { \\
            *(x) = (y); \\
        } \\
    } while(0)

#define CONCAT(a, b) a##b
#define STRINGIFY(x) #x
#define INDIRECT_STRINGIFY(x) STRINGIFY(x)

int macro_test() {
    int value = 0;
    COMPLEX_MACRO(&value, 42);

    int CONCAT(var, 1) = 10;
    printf("%s\\n", INDIRECT_STRINGIFY(Hello));

    return value;
}
""")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(macro_file), [])

        # Should find functions even with macros
        assert len(functions) > 0

    def test_analyze_file_with_templates_cpp(self):
        """Test analysis of C++ template code"""
        template_file = self.temp_dir / "templates.cpp"
        template_file.write_text("""
#include <vector>
#include <memory>

template<typename T>
class TemplateClass {
private:
    T value;
    std::vector<T> items;

public:
    TemplateClass(T v) : value(v) {}

    T getValue() const { return value; }

    template<typename U>
    U convert() const {
        return static_cast<U>(value);
    }
};

template<typename T, int N>
class ArrayClass {
    T data[N];
public:
    T& operator[](int index) { return data[index]; }
};

int template_test() {
    TemplateClass<int> obj(42);
    auto result = obj.convert<double>();

    ArrayClass<int, 10> arr;
    arr[0] = 100;

    return 0;
}
""")

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(template_file), [])

        # Should handle C++ templates
        template_funcs = [f for f in functions if f['name'] == 'template_test']
        assert len(template_funcs) > 0

    # =============== Compile DB Generator Edge Cases ===============

    def test_compile_db_with_no_source_files(self):
        """Test compile DB generation with no source files"""
        generator = CompileDBGenerator(str(self.temp_dir))
        result = generator.generate_simple_compile_db([])
        assert result is False  # Should return False for empty list

    def test_compile_db_with_nonexistent_files(self):
        """Test compile DB generation with nonexistent files"""
        generator = CompileDBGenerator(str(self.temp_dir))
        nonexistent_files = [
            str(self.temp_dir / "nonexistent1.c"),
            str(self.temp_dir / "nonexistent2.cpp"),
        ]

        result = generator.generate_simple_compile_db(nonexistent_files)
        # Should handle gracefully (either fail or generate empty DB)
        assert isinstance(result, bool)

    def test_compile_db_with_mixed_file_types(self):
        """Test compile DB generation with mixed file types"""
        # Create files of different types
        files_to_create = [
            ("test.c", "int main() { return 0; }"),
            ("test.cpp", "#include <iostream>\\nint main() { return 0; }"),
            ("test.h", "#define TEST 1"),
            ("test.txt", "Not a source file"),
            ("test.py", "print('Python file')"),
            ("test.java", "public class Test {}"),
        ]

        for filename, content in files_to_create:
            file_path = self.temp_dir / filename
            file_path.write_text(content)

        generator = CompileDBGenerator(str(self.temp_dir))
        all_files = [str(self.temp_dir / f[0]) for f in files_to_create]

        result = generator.generate_simple_compile_db(all_files)

        if result:
            # Check generated compile commands
            compile_commands_path = self.temp_dir / "compile_commands.json"
            if compile_commands_path.exists():
                import json
                with open(compile_commands_path) as f:
                    commands = json.load(f)

                # Should only include C/C++ files
                for cmd in commands:
                    assert cmd['file'].endswith(('.c', '.cpp', '.cc', '.cxx'))

    def test_compile_db_with_invalid_filenames(self):
        """Test compile DB generation with invalid filenames"""
        generator = CompileDBGenerator(str(self.temp_dir))

        invalid_names = [
            "test.c; rm -rf /",
            "file && echo pwned.cpp",
            "normal$(id).c",
            "test`whoami`.cpp",
            "../../../etc/passwd.c",
        ]

        # Create files with these names (if possible)
        for name in invalid_names:
            try:
                file_path = self.temp_dir / name
                file_path.write_text("// Test")
                invalid_names = [str(file_path)]
            except (OSError, ValueError):
                # Some names might not be valid filenames
                pass

        # Should handle invalid filenames gracefully
        result = generator.generate_simple_compile_db(invalid_names)
        assert isinstance(result, bool)

    # =============== Template Loader Edge Cases ===============

    def test_template_loader_with_missing_directory(self):
        """Test template loader with nonexistent template directory"""
        nonexistent_dir = self.temp_dir / "nonexistent"
        loader = PromptTemplateLoader(templates_dir=str(nonexistent_dir))

        # Should handle missing directory gracefully
        assert loader.templates_dir == nonexistent_dir
        assert loader.load_template("any") is None  # Or should raise appropriate error

    def test_template_loader_with_malformed_templates(self):
        """Test template loader with malformed templates"""
        templates_dir = self.temp_dir / "templates"
        templates_dir.mkdir()

        # Create malformed templates
        malformed_templates = [
            ("unclosed_brace.txt", "Template with {unclosed brace"),
            ("nested_braces.txt", "Template with {nested {braces}}"),
            ("empty_placeholders.txt", "Template with {} empty placeholder"),
            ("special_chars.txt", "Template with \\n\\t\\r escape sequences"),
            ("unicode.txt", "Template with 你好世界 🌍"),
        ]

        for name, content in malformed_templates:
            (templates_dir / name).write_text(content)

        loader = PromptTemplateLoader(templates_dir=str(templates_dir))

        for name, _ in malformed_templates:
            template_name = name.replace('.txt', '')
            template = loader.load_template(template_name)

            if template:
                # Should detect syntax errors
                errors = loader.validate_template_syntax(template)
                if template_name in ['unclosed_brace', 'nested_braces']:
                    assert len(errors) > 0

    def test_template_substitution_edge_cases(self):
        """Test template substitution with edge cases"""
        templates_dir = self.temp_dir / "templates"
        templates_dir.mkdir()

        # Create test template
        template_file = templates_dir / "test.txt"
        template_file.write_text("Value: {value}, Number: {number}")

        loader = PromptTemplateLoader(templates_dir=str(templates_dir))
        template = loader.load_template("test")

        # Test edge cases
        edge_cases = [
            # Non-string values
            {"value": 123, "number": 456.789},
            # None values
            {"value": None, "number": "test"},
            # Empty strings
            {"value": "", "number": ""},
            # Very long strings
            {"value": "A" * 10000, "number": "B" * 10000},
            # Special characters
            {"value": "\\n\\t\\r\\x00\\uffff", "number": "!@#$%^&*()"},
            # Unicode
            {"value": "你好世界 🌍", "number": "café résumé"},
        ]

        for variables in edge_cases:
            # Should handle all cases without crashing
            try:
                result = loader.substitute_template(template, variables, strict=False)
                assert isinstance(result, str)
            except Exception as e:
                # Some cases might fail in strict mode
                assert not isinstance(e, AttributeError)

    def test_template_loader_with_circular_references(self):
        """Test template loader with circular references in context"""
        templates_dir = self.temp_dir / "templates"
        templates_dir.mkdir()

        loader = PromptTemplateLoader(templates_dir=str(templates_dir))

        # Create circular reference
        circular_dict = {}
        circular_dict['self'] = circular_dict

        # Should handle circular references without infinite recursion
        sanitized = loader.substitute_template("Test {self}", {"self": circular_dict}, strict=False)
        assert isinstance(sanitized, str)

    def test_template_loader_performance(self):
        """Test template loader performance with large templates"""
        templates_dir = self.temp_dir / "templates"
        templates_dir.mkdir()

        # Create large template
        large_template_content = "Start: " + "{var}\\n" * 10000 + " End"
        large_template = templates_dir / "large.txt"
        large_template.write_text(large_template_content)

        loader = PromptTemplateLoader(templates_dir=str(templates_dir))

        # Create large context
        large_context = {f"var{i}": f"value{i}" for i in range(10000)}

        import time
        start_time = time.time()
        template = loader.load_template("large")
        result = loader.substitute_template(template, large_context, strict=False)
        end_time = time.time()

        # Should complete in reasonable time
        assert end_time - start_time < 5.0  # 5 second limit
        assert isinstance(result, str)

    # =============== Integration Edge Cases ===============

    def test_full_workflow_with_malicious_project(self):
        """Test full workflow with a project containing malicious code"""
        # Create a project with various issues
        project_dir = SecurityTestCase.create_temp_project_structure("cpp")

        # Add malicious files
        malicious_code = """
#include <system.h>  // Nonexistent header
#include "../etc/passwd"  # Path traversal attempt

int malicious_function() {
    char buffer[10];
    strcpy(buffer, "This is way too long for this buffer");
    system("rm -rf /");  // Command injection
    printf(buffer);  // Format string vulnerability
    return 0;
}
"""
        malicious_file = Path(project_dir) / "src" / "malicious.cpp"
        malicious_file.write_text(malicious_code)

        # Test analyzer
        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(malicious_file), [])

        # Should handle malicious code gracefully
        assert isinstance(functions, list)

        # Test compile DB generation
        generator = CompileDBGenerator(project_dir)
        result = generator.generate_simple_compile_db([str(malicious_file)])
        assert isinstance(result, bool)

    def test_concurrent_access(self):
        """Test components under concurrent access"""
        import threading
        import time

        # Create test file
        test_file = self.temp_dir / "concurrent.c"
        test_file.write_text("int test() { return 0; }")

        results = []
        errors = []

        def analyze_file():
            try:
                analyzer = ClangAnalyzer()
                functions = analyzer.analyze_file(str(test_file), [])
                results.append(len(functions))
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=analyze_file)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should handle concurrent access
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(r == 1 for r in results)  # Should find 1 function

    def test_memory_usage_with_large_inputs(self):
        """Test memory usage doesn't grow excessively with large inputs"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Process many large files
        for i in range(10):
            large_content = f"int func_{i}() {{ return {i}; }}\n" * 10000
            large_file = self.temp_dir / f"large_{i}.c"
            large_file.write_text(large_content)

            analyzer = ClangAnalyzer()
            analyzer.analyze_file(str(large_file), [])

            # Clear reference
            del analyzer

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f} MB"

    def test_error_recovery(self):
        """Test error recovery after failures"""
        analyzer = ClangAnalyzer()

        # First, analyze a file that will fail
        invalid_file = self.temp_dir / "invalid.c"
        invalid_file.write_text("This is not valid C code")

        result1 = analyzer.analyze_file(str(invalid_file), [])
        assert isinstance(result1, list)

        # Then analyze a valid file
        valid_file = self.temp_dir / "valid.c"
        valid_file.write_text("int test() { return 0; }")

        result2 = analyzer.analyze_file(str(valid_file), [])
        assert isinstance(result2, list)
        assert len(result2) > 0

        # Analyzer should recover from failure

    def test_extreme_function_signatures(self):
        """Test analysis of functions with extreme signatures"""
        extreme_code = """
// Function with many parameters
int many_params(int a1, int a2, int a3, int a4, int a5,
                int a6, int a7, int a8, int a9, int a10,
                int a11, int a12, int a13, int a14, int a15,
                int a16, int a17, int a18, int a19, int a20) {
    return a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9 + a10 +
           a11 + a12 + a13 + a14 + a15 + a16 + a17 + a18 + a19 + a20;
}

// Function with complex return type
struct VeryLongStructNameThatMightCauseIssues {
    int field1;
    char field2[100];
    double field3;
    struct {
        int nested;
    } deeply_nested[10];
};

struct VeryLongStructNameThatMightCauseIssues complex_return(
    struct VeryLongStructNameThatMightCauseIssues input) {
    return input;
}

// Function with pointer to function parameter
void callback_param(void (*callback)(int), int value) {
    callback(value);
}
"""

        extreme_file = self.temp_dir / "extreme.c"
        extreme_file.write_text(extreme_code)

        analyzer = ClangAnalyzer()
        functions = analyzer.analyze_file(str(extreme_file), [])

        # Should find all functions
        assert len(functions) >= 3

        # Should handle complex signatures
        for func in functions:
            assert 'parameters' in func
            assert 'return_type' in func
            assert isinstance(func['parameters'], list)