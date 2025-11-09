import textwrap
import os
import sys

# Ensure repository root is on path for `import src.*`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.debug_tool.utils.test_parser import (
    preprocess_text,
    parse_test_cases,
    delete_spans,
    find_spans_by_line,
    apply_blacklist,
)


def test_preprocess_removes_markdown_and_explanations():
    raw = textwrap.dedent(
        """
        ```cpp
        // Explanation: remove this
        #include <gtest/gtest.h>
        TEST(SuiteA, Case1) { EXPECT_TRUE(true); }
        ```
        """
    )
    cleaned = preprocess_text(raw)
    assert "```" not in cleaned
    assert "Explanation:" not in cleaned
    assert "#include <gtest/gtest.h>" in cleaned


def test_parse_and_delete_spans():
    code = textwrap.dedent(
        """
        #include <gtest/gtest.h>
        TEST(SuiteA, Case1) { int a=1; EXPECT_EQ(a,1); }
        TEST(SuiteA, Case2) { int b=2; EXPECT_EQ(b,2); }
        """
    )
    spans = parse_test_cases(code)
    assert len(spans) == 2
    # delete first
    new_code = delete_spans(code, [spans[0]])
    assert "Case1" not in new_code
    assert "Case2" in new_code


def test_find_spans_by_line_and_blacklist():
    code = textwrap.dedent(
        """
        #include <gtest/gtest.h>
        TEST(SuiteA, Case1) {
            MOCKER(f); EXPECT_TRUE(true);
        }
        """
    )
    spans = parse_test_cases(code)
    # blacklist deletes the span
    cleaned, deleted = apply_blacklist(code, spans, ["MOCKER("])
    assert "Case1" not in cleaned
    assert len(deleted) == 1
    # line inside original span maps to the span
    # find a line roughly in the middle
    mid_line = cleaned.count("\n") + 1  # not in cleaned; just sanity on API
    # Use the original code to test find by line
    mid_line_original = next(i + 1 for i, l in enumerate(code.splitlines()) if "MOCKER(" in l)
    hit = find_spans_by_line(spans, mid_line_original)
    assert hit is not None