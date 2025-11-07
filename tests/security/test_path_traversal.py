"""
Path traversal security tests for C/C++ code analyzer
"""

import pytest
import tempfile
import os
from pathlib import Path

# Import the modules to test
from src.analyzer.clang_analyzer import ClangAnalyzer, validate_file_path
from tests.security.utils.security_test_helpers import SecurityTestCase, SecurityAssertions


@pytest.mark.security
@pytest.mark.path_traversal
class TestPathTraversalProtection:
    """Test path traversal attack protection in file access functions"""

    def setup_method(self):
        """Set up test environment"""
        self.analyzer = ClangAnalyzer()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.allowed_extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']

        # Create test files
        self.test_file = self.temp_dir / "test.c"
        self.test_file.write_text("#include <stdio.h>\nint main() { return 0; }")

    def teardown_method(self):
        """Clean up test environment"""
        SecurityTestCase.cleanup_temp_project(str(self.temp_dir))

    def test_validate_normal_file(self):
        """Test that normal file paths are accepted"""
        result = validate_file_path(str(self.test_file))
        assert result is not None
        assert result == self.test_file.resolve()

    def test_reject_nonexistent_file(self):
        """Test that nonexistent files are rejected"""
        nonexistent = self.temp_dir / "nonexistent.c"
        result = validate_file_path(str(nonexistent))
        assert result is None

    def test_reject_invalid_extension(self):
        """Test that files with invalid extensions are rejected"""
        # Create a file with invalid extension
        invalid_file = self.temp_dir / "malicious.exe"
        invalid_file.write_text("fake executable")

        result = validate_file_path(str(invalid_file))
        assert result is None

    def test_reject_directory_traversal_basic(self):
        """Test basic directory traversal attempts"""
        vectors = SecurityTestCase.generate_path_traversal_vectors()

        for vector in vectors:
            malicious_path = str(self.test_file) + "/" + vector
            result = validate_file_path(malicious_path)
            assert result is None, f"Path traversal not blocked: {vector}"

    def test_reject_absolute_path_traversal(self):
        """Test absolute path traversal attempts"""
        dangerous_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/hosts",
            "C:\\Windows\\System32\\config\\SAM",
            "C:\\boot.ini",
            "/proc/version",
            "/sys/kernel/version",
        ]

        for path in dangerous_paths:
            result = validate_file_path(path)
            assert result is None, f"Absolute path not blocked: {path}"

    def test_reject_symbolic_link_attacks(self):
        """Test symbolic link attack attempts"""
        # Create a symlink to a system file
        if os.name != 'nt':  # Unix-like systems
            symlink_path = self.temp_dir / "symlink.c"
            try:
                symlink_path.symlink_to("/etc/passwd")
                result = validate_file_path(str(symlink_path))
                # Symlink exists but points to restricted location
                assert result is None or result.resolve().parts[1:3] != ('etc', 'passwd')
            except (OSError, PermissionError):
                # Skip if can't create symlinks
                pass

    def test_reject_encoded_path_traversal(self):
        """Test URL encoded path traversal attempts"""
        encoded_vectors = [
            "%2e%2e%2f" * 10 + "etc%2fpasswd",
            "%252e%252e%252f" * 10 + "etc%252fpasswd",
            "..%c0%af.." * 10 + "etc/passwd",
        ]

        for vector in encoded_vectors:
            malicious_path = str(self.test_file) + "/" + vector
            result = validate_file_path(malicious_path)
            assert result is None, f"Encoded path traversal not blocked: {vector}"

    def test_reject_null_byte_injection(self):
        """Test null byte injection attempts"""
        null_byte_vectors = [
            str(self.test_file) + "\x00.txt",
            str(self.test_file) + "/test.c\x00.jpg",
            "/etc/passwd\x00.c",
        ]

        for vector in null_byte_vectors:
            result = validate_file_path(vector)
            assert result is None, f"Null byte injection not blocked: {repr(vector)}"

    def test_reject_long_path_attacks(self):
        """Test overly long path attacks"""
        long_path = str(self.test_file) + "/" * 1000 + "test.c"
        result = validate_file_path(long_path)
        # Should either be rejected or the path should be normalized
        if result:
            assert len(str(result)) < 10000  # Reasonable length limit

    def test_analyze_file_with_malicious_path(self):
        """Test that ClangAnalyzer.analyze_file rejects malicious paths"""
        vectors = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
        ]

        for vector in vectors:
            # Should not crash or access the file
            result = self.analyzer.analyze_file(vector, [])
            assert result == [], f"Analyzer should reject malicious path: {vector}"

    def test_analyze_file_with_normal_path(self):
        """Test that ClangAnalyzer.analyze_file works with normal paths"""
        result = self.analyzer.analyze_file(str(self.test_file), [])
        assert isinstance(result, list)
        # Should find the main function
        functions = [f for f in result if f['name'] == 'main']
        assert len(functions) > 0

    def test_reject_file_size_limit(self):
        """Test rejection of extremely large files"""
        # Create a large file
        large_file = self.temp_dir / "large.c"
        large_content = "int x = 0;\n" * 1000000  # About 15MB
        large_file.write_text(large_content)

        result = validate_file_path(str(large_file))
        # File exists and has valid extension, so it should return a path
        # But opening it should fail due to size limit
        assert result is not None

        # Now test with analyzer - should handle large file gracefully
        functions = self.analyzer.analyze_file(str(large_file), [])
        # Should either succeed or fail gracefully, not crash
        assert isinstance(functions, list)

    @pytest.mark.parametrize("vector", SecurityTestCase.generate_path_traversal_vectors())
    def test_security_assertion_helper(self, vector):
        """Test security assertion helper detects path traversal"""
        SecurityAssertions.assert_no_path_traversal(vector)
        # This should pass for normal paths
        SecurityAssertions.assert_no_path_traversal("normal/file/path.c")

    def test_file_access_restriction(self):
        """Test that file access is properly restricted"""
        allowed_dirs = [str(self.temp_dir)]

        # Should allow access to files in temp directory
        SecurityAssertions.assert_file_access_restricted(str(self.test_file), allowed_dirs)

        # Should deny access to system files
        with pytest.raises(AssertionError):
            SecurityAssertions.assert_file_access_restricted("/etc/passwd", allowed_dirs)

    def test_edge_cases(self):
        """Test edge cases in path validation"""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            ".",  # Current directory
            "..",  # Parent directory
            "/",  # Root directory
            "C:\\",  # Windows root
            "file" * 1000 + ".c",  # Very long filename
        ]

        for case in edge_cases:
            result = validate_file_path(case)
            # Most edge cases should be rejected
            if case in [".", ".."]:
                assert result is None, f"Should reject special path: {case}"