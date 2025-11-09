"""
Test case parser utilities for C/C++ GoogleTest-style suites.

Supports parsing and deleting blocks for:
- TEST(Suite, Name)
- TEST_F(Fixture, Name)
- void test_xxx(...)

Provides reverse-order deletion to keep line numbers stable for subsequent fixes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TestCaseSpan:
    kind: str  # "TEST" | "TEST_F" | "FUNC"
    suite: Optional[str]
    name: str
    start_index: int
    header_end_index: int
    body_start_index: int
    body_end_index: int
    start_line: int
    end_line: int


def _find_matching_brace(content: str, start_pos: int) -> int:
    """Find the matching closing brace for the block starting at the first '{' after start_pos.
    Returns index of the closing '}', or len(content) - 1 if unmatched.
    """
    brace_start = content.find('{', start_pos)
    if brace_start == -1:
        return len(content) - 1

    brace_count = 1
    pos = brace_start + 1
    while pos < len(content) and brace_count > 0:
        ch = content[pos]
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
        pos += 1

    return pos - 1 if brace_count == 0 else len(content) - 1


def _compute_line_number_map(content: str) -> List[int]:
    """Return list of indices where each line starts (0-based)."""
    starts = [0]
    for i, ch in enumerate(content):
        if ch == '\n':
            starts.append(i + 1)
    return starts


def _index_to_line(line_starts: List[int], index: int) -> int:
    """Find 1-based line number for a given index using binary search over line starts."""
    # Simple linear fallback for moderate file sizes
    line = 1
    for i, s in enumerate(line_starts):
        if s > index:
            return i
        line = i + 1
    return line


def parse_test_cases(content: str) -> List[TestCaseSpan]:
    """Parse test cases and return spans with positions and names.

    This function is resilient to extra whitespace and comments and handles nested braces in bodies.
    """
    spans: List[TestCaseSpan] = []

    # Patterns
    pat_test = re.compile(r'TEST\s*\(\s*([^,]+)\s*,\s*([^\)]+)\s*\)', re.MULTILINE)
    pat_test_f = re.compile(r'TEST_F\s*\(\s*([^,]+)\s*,\s*([^\)]+)\s*\)', re.MULTILINE)
    pat_func = re.compile(r'(?:void|int)\s+(test_[A-Za-z0-9_]+)\s*\([^)]*\)', re.MULTILINE)

    line_starts = _compute_line_number_map(content)

    # Helper to create span
    def add_span(kind: str, suite: Optional[str], name: str, start: int, header_end: int) -> None:
        body_end = _find_matching_brace(content, header_end)
        body_start = content.find('{', header_end)
        if body_start == -1:
            body_start = header_end
        start_line = _index_to_line(line_starts, start)
        end_line = _index_to_line(line_starts, body_end)
        spans.append(TestCaseSpan(kind, suite, name.strip(), start, header_end, body_start, body_end, start_line, end_line))

    for m in pat_test.finditer(content):
        add_span('TEST', m.group(1).strip(), m.group(2).strip(), m.start(), m.end())

    for m in pat_test_f.finditer(content):
        add_span('TEST_F', m.group(1).strip(), m.group(2).strip(), m.start(), m.end())

    for m in pat_func.finditer(content):
        # suite is None; name is function name
        add_span('FUNC', None, m.group(1).strip(), m.start(), m.end())

    # Sort by start_index ascending (natural order)
    spans.sort(key=lambda s: s.start_index)
    return spans


def delete_spans(content: str, spans_to_delete: List[TestCaseSpan]) -> str:
    """Delete given spans from content in reverse order to avoid index shifts."""
    if not spans_to_delete:
        return content
    spans_sorted = sorted(spans_to_delete, key=lambda s: s.start_index, reverse=True)
    new_content = content
    for s in spans_sorted:
        # remove from start_index to body_end_index (inclusive). Add 1 to include closing brace.
        end = s.body_end_index + 1 if s.body_end_index + 1 <= len(new_content) else s.body_end_index
        new_content = new_content[:s.start_index] + new_content[end:]
    return new_content


def find_spans_by_line(spans: List[TestCaseSpan], line: int) -> Optional[TestCaseSpan]:
    """Return span containing the line number (1-based)."""
    for s in spans:
        if s.start_line <= line <= s.end_line:
            return s
    return None


def find_spans_by_names(spans: List[TestCaseSpan], names: List[Tuple[Optional[str], str]]) -> List[TestCaseSpan]:
    """Find spans by (suite, name) for TEST/TEST_F or by function name for FUNC.
    Names list contains tuples of (suite_or_fixture, test_name). For FUNC, pass (None, func_name).
    """
    hits: List[TestCaseSpan] = []
    for (suite, name) in names:
        for s in spans:
            if s.kind in ('TEST', 'TEST_F'):
                if s.name == name and (suite is None or s.suite == suite):
                    hits.append(s)
            elif s.kind == 'FUNC':
                if s.name == name:
                    hits.append(s)
    # Deduplicate
    unique: List[TestCaseSpan] = []
    seen = set()
    for s in hits:
        key = (s.kind, s.suite, s.name, s.start_index)
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def preprocess_text(raw: str) -> str:
    """Remove markdown code fences and trivial explanations from aggregated text.

    - Strips ```cpp and closing ``` fences
    - Removes leading BOM and trims trailing whitespace
    """
    text = raw.replace('\r\n', '\n')
    # Remove fences
    text = re.sub(r"```cpp\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)
    # Remove possible language fences like ```c or ```C++
    text = re.sub(r"```[a-zA-Z+]+\s*", "", text)
    # Drop obvious non-code explanatory lines starting with markdown bullets
    lines = text.split('\n')
    filtered = []
    for ln in lines:
        # drop markdown bullet explanations
        if re.match(r"^\s*[-*]\s+", ln):
            continue
        # drop explicit explanation lines
        if re.match(r"^\s*Explanation:\s*", ln, flags=re.IGNORECASE):
            continue
        # drop commented explanation lines starting with // Explanation:
        if re.match(r"^\s*//\s*Explanation:\s*", ln, flags=re.IGNORECASE):
            continue
        filtered.append(ln)
    text = '\n'.join(filtered)
    return text.strip()


def apply_blacklist(content: str, spans: List[TestCaseSpan], patterns: List[str]) -> Tuple[str, List[TestCaseSpan]]:
    """Delete any test span whose code contains one of the blacklist patterns."""
    if not patterns:
        return content, []
    to_delete: List[TestCaseSpan] = []
    for s in spans:
        block = content[s.start_index:s.body_end_index+1]
        for p in patterns:
            if p and p in block:
                to_delete.append(s)
                break
    if not to_delete:
        return content, []
    new_content = delete_spans(content, to_delete)
    return new_content, to_delete