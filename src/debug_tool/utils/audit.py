"""
Audit logging helpers for the compile-fix workflow.

Writes structured text audit files alongside regular logs.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import List, Optional


class AuditLogger:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_path = self.base_dir / f"audit_{ts}.txt"

    def write_header(self, title: str) -> None:
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write(f"=== {title} ===\n")

    def log_input(self, input_text_path: Optional[str], target_file: str, file_prefix: Optional[str]) -> None:
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write(f"InputText: {input_text_path}\n")
            f.write(f"TargetFile: {target_file}\n")
            f.write(f"ErrorFilePrefix: {file_prefix}\n")

    def log_preprocessing(self, removed_fences: bool, blacklist_patterns: List[str], deleted_count: int, deleted_names: Optional[List[str]] = None) -> None:
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write(f"Preprocess: removed_fences={removed_fences}, blacklist={blacklist_patterns}, deleted={deleted_count}\n")
            if deleted_names:
                f.write("PreprocessDeleted:\n")
                for n in deleted_names:
                    f.write(f"  - {n}\n")

    def log_compile_errors(self, errors: List[str]) -> None:
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write("CompileErrors:\n")
            for e in errors:
                f.write(f"  - {e}\n")

    def log_deleted_tests(self, deleted_names: List[str]) -> None:
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write("DeletedTests:\n")
            for n in deleted_names:
                f.write(f"  - {n}\n")

    def log_runtime_failures(self, failures: List[str]) -> None:
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write("RuntimeFailures:\n")
            for n in failures:
                f.write(f"  - {n}\n")