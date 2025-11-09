import textwrap
import os
import sys

# Ensure repository root is on path for `import src.*`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.debug_tool.utils.error_parser import parse_compile_errors, parse_gtest_failures


def test_parse_compile_errors_filters_by_prefix():
    err_text = textwrap.dedent(
        """
        /path/to/generated_suite.cpp:42:3: error: 'missing_symbol' was not declared in this scope
        /path/other/file.cpp:10:2: error: something else
        """
    )
    errs = parse_compile_errors(err_text, file_prefix_filter="generated_suite.cpp")
    assert len(errs) == 1
    e = errs[0]
    assert e.file.endswith("generated_suite.cpp")
    assert e.line == 42
    assert e.level.lower() == "error"
    assert "missing_symbol" in e.message


def test_parse_gtest_failures_basic():
    gtest_out = textwrap.dedent(
        """
        [ RUN      ] GeneratedSuite.RuntimeFailure
        /Users/xx/generated_suite.cpp:55: Failure
        Expected equality of these values:
          hash_table_size(t)
          Which is: 0
          999
        [  FAILED  ] GeneratedSuite.RuntimeFailure (0 ms)
        [  PASSED  ] 1 test.
        """
    )
    fails = parse_gtest_failures(gtest_out)
    assert len(fails) == 1
    f = fails[0]
    assert f.suite == "GeneratedSuite"
    assert f.name == "RuntimeFailure"