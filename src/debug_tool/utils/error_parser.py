"""
Compiler and test runner error parsing utilities.

Supports:
- Clang/GCC style compile errors: file:line:col: error: message
- GTest runtime failures: lines like "[  FAILED  ] Suite.Name"
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompileError:
    file: str
    line: int
    column: Optional[int]
    level: str  # error, warning, fatal error
    message: str


def parse_compile_errors(output: str, file_prefix_filter: Optional[str] = None) -> List[CompileError]:
    """Parse compiler error text and optionally filter by file prefix substring."""
    errs: List[CompileError] = []
    # clang/gcc typical: path/to/file.cpp:123:45: error: message
    pat = re.compile(r"^(.*?):(\d+)(?::(\d+))?:\s*(error|fatal error|warning):\s*(.*)$")
    for line in output.splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        file = m.group(1)
        ln = int(m.group(2))
        col = int(m.group(3)) if m.group(3) else None
        level = m.group(4)
        msg = m.group(5)
        if file_prefix_filter and (file_prefix_filter not in file):
            continue
        errs.append(CompileError(file=file, line=ln, column=col, level=level, message=msg))
    return errs


@dataclass
class TestFailure:
    suite: Optional[str]
    name: str
    full: str  # e.g., Suite.Name or just name


def parse_gtest_failures(output: str) -> List[TestFailure]:
    """Parse GoogleTest style runtime failures from test binary or ctest output."""
    failures: List[TestFailure] = []
    # Matches lines like: [  FAILED  ] Suite.Name
    pat = re.compile(r"\[\s*FAILED\s*\]\s+([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)")
    for line in output.splitlines():
        m = pat.search(line)
        if m:
            suite, name = m.group(1), m.group(2)
            failures.append(TestFailure(suite=suite, name=name, full=f"{suite}.{name}"))
    return failures