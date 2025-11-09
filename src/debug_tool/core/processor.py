"""
Core processor orchestrating the compile-fix workflow:
- Preprocess aggregated test text
- Apply blacklist-based deletions
- Write to target file
- Build with CMake and parse compile errors
- Delete problematic tests by line-spans (no double deletion)
- Optionally run tests and delete failing ones
- Record audit logs
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from src.utils.logging_utils import get_logger, setup_logging
from src.debug_tool.utils.test_parser import (
    parse_test_cases,
    delete_spans,
    find_spans_by_line,
    find_spans_by_names,
    preprocess_text,
    apply_blacklist,
    TestCaseSpan,
)
from src.debug_tool.utils.error_parser import parse_compile_errors, parse_gtest_failures
from src.debug_tool.utils.audit import AuditLogger


logger = get_logger(__name__)


class CompileFixProcessor:
    def __init__(
        self,
        project_root: str,
        build_dir: str,
        audit_dir: str,
        cmake_target: Optional[str] = None,
        # Optional command customizations
        cmake_command: Optional[str] = None,
        cmake_configure_args: Optional[List[str]] = None,
        cmake_build_args: Optional[List[str]] = None,
        ctest_args: Optional[List[str]] = None,
        ctest_regex: Optional[str] = None,
        ctest_exclude_regex: Optional[str] = None,
        ctest_workdir: Optional[str] = None,
        ctest_command: Optional[str] = None,
    ):
        self.project_root = Path(project_root)
        self.build_dir = Path(build_dir)
        self.audit = AuditLogger(audit_dir)
        self.cmake_target = cmake_target
        # Command overrides
        self.cmake_command = cmake_command or "cmake"
        self.cmake_configure_args = cmake_configure_args
        self.cmake_build_args = cmake_build_args
        self.ctest_args = ctest_args
        self.ctest_regex = ctest_regex
        self.ctest_exclude_regex = ctest_exclude_regex
        self.ctest_workdir = Path(ctest_workdir) if ctest_workdir else None
        self.ctest_command = ctest_command or "ctest"
        setup_logging(output_dir=audit_dir)

    def _run(self, cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        logger.info(f"Running: {' '.join(cmd)} (cwd={cwd or os.getcwd()})")
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        logger.debug(out)
        if err:
            logger.debug(err)
        return proc.returncode, out, err

    def cmake_configure(self) -> None:
        self.build_dir.mkdir(parents=True, exist_ok=True)
        if self.cmake_configure_args:
            cmd = [self.cmake_command] + self.cmake_configure_args
        else:
            cmd = [self.cmake_command, "-S", str(self.project_root), "-B", str(self.build_dir)]
        rc, out, err = self._run(cmd)
        if rc != 0:
            raise RuntimeError(f"CMake configure failed: {err}\n{out}")

    def cmake_build(self) -> Tuple[bool, str, str]:
        if self.cmake_build_args:
            cmd = [self.cmake_command] + self.cmake_build_args
        else:
            cmd = [self.cmake_command, "--build", str(self.build_dir)]
            if self.cmake_target:
                cmd += ["--target", self.cmake_target]
        rc, out, err = self._run(cmd)
        return rc == 0, out, err

    def ctest_run(self) -> Tuple[bool, str, str]:
        base_args = self.ctest_args if self.ctest_args is not None else ["--output-on-failure"]
        cmd = [self.ctest_command] + base_args
        if self.ctest_regex:
            cmd += ["-R", self.ctest_regex]
        if self.ctest_exclude_regex:
            cmd += ["-E", self.ctest_exclude_regex]
        workdir = str(self.ctest_workdir) if self.ctest_workdir else str(self.build_dir)
        rc, out, err = self._run(cmd, cwd=workdir)
        return rc == 0, out, err

    def preprocess_and_write(self, input_text: str, target_file: str, blacklist: List[str]) -> Tuple[str, List[TestCaseSpan], List[TestCaseSpan]]:
        """Preprocess raw text, parse spans, apply blacklist, and write to target."""
        clean = preprocess_text(input_text)
        spans = parse_test_cases(clean)
        clean2, deleted_by_blacklist = apply_blacklist(clean, spans, blacklist)
        if deleted_by_blacklist:
            # Re-parse spans since content changed
            spans = parse_test_cases(clean2)
        Path(target_file).parent.mkdir(parents=True, exist_ok=True)
        Path(target_file).write_text(clean2, encoding="utf-8")
        # Audit
        self.audit.write_header("Preprocess")
        self.audit.log_input(input_text_path=None, target_file=target_file, file_prefix=None)
        deleted_names = [f"{s.suite}.{s.name}" if s.suite else s.name for s in deleted_by_blacklist]
        self.audit.log_preprocessing(removed_fences=True, blacklist_patterns=blacklist, deleted_count=len(deleted_by_blacklist), deleted_names=deleted_names)
        return clean2, spans, deleted_by_blacklist

    def fix_compile_errors(self, source_code: str, spans: List[TestCaseSpan], compile_err_text: str, file_prefix: Optional[str]) -> Tuple[str, List[str]]:
        """Delete tests implicated by compile errors; do not delete same test twice."""
        comp_errs = parse_compile_errors(compile_err_text, file_prefix_filter=file_prefix)
        self.audit.log_compile_errors([f"{e.file}:{e.line}: {e.level}: {e.message}" for e in comp_errs])
        to_delete: List[TestCaseSpan] = []
        for e in comp_errs:
            s = find_spans_by_line(spans, e.line)
            if s:
                to_delete.append(s)
        # Deduplicate by identity
        unique: List[TestCaseSpan] = []
        seen = set()
        for s in to_delete:
            key = (s.kind, s.suite, s.name, s.start_index)
            if key not in seen:
                seen.add(key)
                unique.append(s)
        new_code = delete_spans(source_code, unique)
        deleted_names = [f"{s.suite}.{s.name}" if s.suite else s.name for s in unique]
        self.audit.log_deleted_tests(deleted_names)
        return new_code, deleted_names

    def fix_runtime_failures(self, source_code: str, spans: List[TestCaseSpan], ctest_output: str) -> Tuple[str, List[str]]:
        failures = parse_gtest_failures(ctest_output)
        names = [(f.suite, f.name) for f in failures]
        hit_spans = find_spans_by_names(spans, names)
        new_code = delete_spans(source_code, hit_spans)
        deleted_names = [f.full for f in failures]
        self.audit.log_runtime_failures(deleted_names)
        return new_code, deleted_names