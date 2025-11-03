"""
Test compilation database parser
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.parser.compilation_db import CompilationDatabaseParser


class TestCompilationDatabaseParser:
    """Test compilation database parser functionality"""

    def test_init_with_path(self):
        """Test parser initialization"""
        parser = CompilationDatabaseParser("/path/to/compile_commands.json")
        assert parser.compile_commands_path == Path("/path/to/compile_commands.json")

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error"""
        parser = CompilationDatabaseParser("/non/existent/file.json")

        with pytest.raises(FileNotFoundError, match="compile_commands.json not found"):
            parser.parse()

    def test_parse_valid_json_with_command_format(self):
        """Test parsing valid compile_commands.json with command format"""
        compile_commands_data = [
            {
                "directory": "/project",
                "file": "src/main.c",
                "command": "gcc -I/include -DDEBUG -o main.o src/main.c"
            },
            {
                "directory": "/project",
                "file": "src/utils.c",
                "command": "clang -I/usr/include -O2 -c src/utils.c"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)
            result = parser.parse()

            assert len(result) == 2

            # Check first compilation unit
            unit1 = result[0]
            assert unit1['file'] == "/project/src/main.c"
            assert unit1['directory'] == "/project"
            assert '-I/include' in unit1['arguments']
            assert '-DDEBUG' in unit1['arguments']
            assert 'gcc' not in unit1['arguments'][0]  # Compiler executable filtered
            assert '-o' not in unit1['arguments']  # Output flag filtered
            assert 'src/main.c' not in unit1['arguments']  # Source file filtered

            # Check second compilation unit
            unit2 = result[1]
            assert unit2['file'] == "/project/src/utils.c"
            assert '-I/usr/include' in unit2['arguments']
            assert '-O2' in unit2['arguments']

        finally:
            Path(temp_path).unlink()

    def test_parse_valid_json_with_arguments_format(self):
        """Test parsing compile_commands.json with arguments array format"""
        compile_commands_data = [
            {
                "directory": "/project",
                "file": "src/main.c",
                "arguments": ["gcc", "-I/include", "-DDEBUG", "-o", "main.o", "src/main.c"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)
            result = parser.parse()

            assert len(result) == 1
            unit = result[0]
            assert unit['file'] == "/project/src/main.c"
            assert '-I/include' in unit['arguments']
            assert '-DDEBUG' in unit['arguments']
            assert 'gcc' not in unit['arguments']
            assert '-o' not in unit['arguments']

        finally:
            Path(temp_path).unlink()

    def test_parse_missing_command_and_arguments(self):
        """Test parsing entry with neither command nor arguments raises error"""
        compile_commands_data = [
            {
                "directory": "/project",
                "file": "src/main.c"
                # Missing both 'command' and 'arguments'
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)

            with pytest.raises(ValueError, match="No 'command' or 'arguments' field found"):
                parser.parse()

        finally:
            Path(temp_path).unlink()

    def test_parse_with_include_patterns(self):
        """Test parsing with include patterns filter"""
        compile_commands_data = [
            {
                "directory": "/project",
                "file": "src/main.c",
                "command": "gcc -c src/main.c"
            },
            {
                "directory": "/project",
                "file": "src/utils/math.c",
                "command": "gcc -c src/utils/math.c"
            },
            {
                "directory": "/project",
                "file": "test/test_main.c",
                "command": "gcc -c test/test_main.c"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)

            # Test include directory pattern
            result = parser.parse(include_patterns=["src/utils/"])
            assert len(result) == 1
            assert "math.c" in result[0]['file']

            # Test include file pattern - will match both src/main.c and test/test_main.c
            result = parser.parse(include_patterns=["main.c"])
            assert len(result) == 2
            assert all("main.c" in unit['file'] for unit in result)

            # Test multiple include patterns
            result = parser.parse(include_patterns=["src/utils/", "test/"])
            assert len(result) == 2

        finally:
            Path(temp_path).unlink()

    def test_parse_with_exclude_patterns(self):
        """Test parsing with exclude patterns filter"""
        compile_commands_data = [
            {
                "directory": "/project",
                "file": "src/main.c",
                "command": "gcc -c src/main.c"
            },
            {
                "directory": "/project",
                "file": "src/utils/math.c",
                "command": "gcc -c src/utils/math.c"
            },
            {
                "directory": "/project",
                "file": "test/test_main.c",
                "command": "gcc -c test/test_main.c"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)

            # Test exclude directory pattern
            result = parser.parse(exclude_patterns=["test/"])
            assert len(result) == 2
            assert all("test/" not in unit['file'] for unit in result)

            # Test exclude file pattern
            result = parser.parse(exclude_patterns=["math.c"])
            assert len(result) == 2
            assert all("math.c" not in unit['file'] for unit in result)

        finally:
            Path(temp_path).unlink()

    def test_parse_with_relative_file_paths(self):
        """Test parsing with relative file paths resolves correctly"""
        compile_commands_data = [
            {
                "directory": "/project/src",
                "file": "main.c",
                "command": "gcc -c main.c"
            },
            {
                "directory": "/project",
                "file": "./src/utils.c",
                "command": "gcc -c ./src/utils.c"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)
            result = parser.parse()

            assert len(result) == 2
            assert result[0]['file'] == "/project/src/main.c"
            assert result[1]['file'] == "/project/src/utils.c"

        finally:
            Path(temp_path).unlink()

    def test_parse_arguments_filtering(self):
        """Test argument parsing and filtering logic"""
        parser = CompilationDatabaseParser("dummy.json")

        # Test basic filtering
        command = "gcc -I/include -DDEBUG -O2 -o output.o source.c"
        args = parser._parse_arguments(command)

        assert '-I/include' in args
        assert '-DDEBUG' in args
        assert '-O2' in args
        assert 'gcc' not in args
        assert '-o' not in args
        assert 'output.o' not in args
        assert 'source.c' not in args

    def test_filter_arguments_array(self):
        """Test filtering arguments from array format"""
        parser = CompilationDatabaseParser("dummy.json")

        arguments = [
            "g++", "-I/include", "-DDEBUG", "-std=c++11",
            "-O2", "-o", "output.o", "source.cpp", "-MMD"
        ]

        filtered = parser._filter_arguments(arguments)

        assert '-I/include' in filtered
        assert '-DDEBUG' in filtered
        assert '-std=c++11' in filtered
        assert '-O2' in filtered
        # Note: -MMD doesn't start with expected patterns, so it's filtered out
        assert 'g++' not in filtered
        assert '-o' not in filtered
        assert 'output.o' not in filtered
        assert 'source.cpp' not in filtered

    def test_matches_patterns_directory(self):
        """Test directory pattern matching"""
        parser = CompilationDatabaseParser("dummy.json")

        # Directory pattern should match
        assert parser._matches_patterns("/project/src/utils/file.c", ["src/utils/"])
        assert parser._matches_patterns("/project/src/utils.c", ["src/"])

        # Directory pattern should not match
        assert not parser._matches_patterns("/project/lib/file.c", ["src/utils/"])

    def test_matches_patterns_file(self):
        """Test file pattern matching"""
        parser = CompilationDatabaseParser("dummy.json")

        # File pattern should match
        assert parser._matches_patterns("/project/src/main.c", ["main.c"])
        assert parser._matches_patterns("/project/src/utils/math.c", ["math.c"])

        # Partial path should match
        assert parser._matches_patterns("/project/src/utils/math.c", ["src/utils/math.c"])

    def test_matches_patterns_relative(self):
        """Test relative path pattern matching"""
        parser = CompilationDatabaseParser("dummy.json")

        assert parser._matches_patterns("/project/src/utils/math.c", ["src/utils/math.c"])
        assert parser._matches_patterns("/project/src/utils/math.c", ["project/src/utils"])

    def test_get_file_dependencies(self):
        """Test getting file dependencies (TODO method)"""
        parser = CompilationDatabaseParser("dummy.json")

        # Currently returns empty list as it's TODO
        deps = parser.get_file_dependencies("/project/src/main.c")
        assert deps == []

    def test_get_compilation_flags(self):
        """Test getting compilation flags (TODO method)"""
        parser = CompilationDatabaseParser("dummy.json")

        # Currently returns empty dict as it's TODO
        flags = parser.get_compilation_flags("/project/src/main.c")
        assert flags == {}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)

            with pytest.raises(json.JSONDecodeError):
                parser.parse()

        finally:
            Path(temp_path).unlink()

    def test_parse_empty_json_array(self):
        """Test parsing empty compilation database"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)
            result = parser.parse()

            assert result == []

        finally:
            Path(temp_path).unlink()

    def test_parse_with_special_characters_in_paths(self):
        """Test parsing paths with special characters"""
        compile_commands_data = [
            {
                "directory": "/project",
                "file": "src/utils with spaces/main.c",
                "command": "gcc -c 'src/utils with spaces/main.c'"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(compile_commands_data, f)
            temp_path = f.name

        try:
            parser = CompilationDatabaseParser(temp_path)
            result = parser.parse()

            assert len(result) == 1
            assert "utils with spaces" in result[0]['file']

        finally:
            Path(temp_path).unlink()

    def test_parse_cxx_file_extensions(self):
        """Test parsing different C++ file extensions"""
        extensions = ['.cpp', '.cc', '.cxx', '.c++']

        for ext in extensions:
            compile_commands_data = [
                {
                    "directory": "/project",
                    "file": f"src/main{ext}",
                    "command": f"g++ -c src/main{ext}"
                }
            ]

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(compile_commands_data, f)
                temp_path = f.name

            try:
                parser = CompilationDatabaseParser(temp_path)
                result = parser.parse()

                assert len(result) == 1
                assert result[0]['file'].endswith(ext)

            finally:
                Path(temp_path).unlink()