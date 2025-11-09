#!/usr/bin/env python3
"""
CLI for automated compile-fix of aggregated GoogleTest files.

Usage examples:

  1) Full CLI args:
     python -m src.debug_tool.cli.compile_fix \
       --input-text experiment/deepseek_generated_tests/3_pure_tests/combined.txt \
       --target-file test_projects/fix_bugs_project/tests/generated_suite.cpp \
       --project-root test_projects/fix_bugs_project --build-dir test_projects/fix_bugs_project/build \
       --error-prefix generated_suite.cpp \
       --blacklist "MOCKER(" "mock_variadic" \
       --run-tests --cmake-target generated_suite --max-iterations 10 \
       --cmake-configure-args -S test_projects/fix_bugs_project -B test_projects/fix_bugs_project/build \
       --cmake-build-args --build test_projects/fix_bugs_project/build --target generated_suite \
       --ctest-args --output-on-failure --ctest-regex GeneratedSuite

  2) Config-driven (recommended for reuse):
     python -m src.debug_tool.cli.compile_fix --config config/compile_fix.yaml
     # CLI args override config values if provided
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import yaml

from src.utils.logging_utils import get_logger
from src.debug_tool.core.processor import CompileFixProcessor
from src.debug_tool.utils.test_parser import parse_test_cases


logger = get_logger(__name__)


def load_blacklist_sources(cli_patterns: List[str], blacklist_file: Optional[str], blacklist_config: Optional[str]) -> List[str]:
    """Load blacklist patterns from CLI, file, and YAML config.

    Merge and deduplicate. File format: one pattern per line, supports '#' or '//' comments.
    YAML keys searched:
      - top-level 'blacklist'
      - 'debug_tool.blacklist'
      - 'debug_tool.compile_fix.blacklist'
    """
    patterns: List[str] = []
    # CLI provided
    for p in cli_patterns or []:
        if p:
            patterns.append(p)

    # From file
    if blacklist_file:
        fp = Path(blacklist_file)
        if fp.exists():
            for ln in fp.read_text(encoding="utf-8").splitlines():
                s = ln.strip()
                if not s:
                    continue
                if s.startswith('#') or s.startswith('//'):
                    continue
                patterns.append(s)

    # From YAML config
    if blacklist_config:
        cp = Path(blacklist_config)
        if cp.exists():
            try:
                data = yaml.safe_load(cp.read_text(encoding="utf-8")) or {}
                # Try hierarchical keys
                keys_to_try = [
                    ([], 'blacklist'),
                    (['debug_tool'], 'blacklist'),
                    (['debug_tool', 'compile_fix'], 'blacklist'),
                ]
                for path, key in keys_to_try:
                    node = data
                    ok = True
                    for seg in path:
                        if isinstance(node, dict) and seg in node:
                            node = node[seg]
                        else:
                            ok = False
                            break
                    if ok and isinstance(node, dict) and key in node:
                        vals = node[key]
                        if isinstance(vals, list):
                            for v in vals:
                                if v:
                                    patterns.append(str(v))
                        break
            except Exception:
                # fall back silently
                pass

    # Deduplicate while preserving order
    seen = set()
    merged: List[str] = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            merged.append(p)
    return merged


def _extract_cfg_node(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the compile-fix node from YAML data.
    Tries paths: debug_tool.compile_fix -> compile_fix -> top-level.
    """
    if not isinstance(data, dict):
        return {}
    node = data
    if 'debug_tool' in node and isinstance(node['debug_tool'], dict):
        dt = node['debug_tool']
        if 'compile_fix' in dt and isinstance(dt['compile_fix'], dict):
            return dt['compile_fix']
        # fallback: debug_tool level
        if isinstance(dt, dict):
            return dt
    if 'compile_fix' in node and isinstance(node['compile_fix'], dict):
        return node['compile_fix']
    return node


def load_compile_fix_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load compile-fix configuration from YAML.

    If path not provided, try default 'config/compile_fix.yaml'. Returns a flat dict of options.
    """
    candidates: List[Path] = []
    if config_path:
        candidates.append(Path(config_path))
    else:
        # Optional env var override
        env_path = os.environ.get('COMPILE_FIX_CONFIG')
        if env_path:
            candidates.append(Path(env_path))
    candidates.append(Path('config/compile_fix.yaml'))

    data: Dict[str, Any] = {}
    for p in candidates:
        if p.exists():
            try:
                data = yaml.safe_load(p.read_text(encoding='utf-8')) or {}
                break
            except Exception:
                data = {}

    node = _extract_cfg_node(data)
    if not isinstance(node, dict):
        return {}
    return node


def main() -> int:
    ap = argparse.ArgumentParser(description="Automated compile-fix for aggregated test files")
    ap.add_argument("--config", default=None, help="YAML config file for compile-fix options (defaults to config/compile_fix.yaml)")
    ap.add_argument("--input-text", required=False, default=None, help="Path to aggregated test text file")
    ap.add_argument("--target-file", required=False, default=None, help="Path to .cpp test file to write")
    ap.add_argument("--project-root", required=False, default=None, help="CMake project root directory")
    ap.add_argument("--build-dir", required=False, default=None, help="CMake build directory")
    ap.add_argument("--audit-dir", default="./experiment/compile_fix_logs", help="Directory to write audit logs")
    ap.add_argument("--error-prefix", default=None, help="Filter compile errors to this file prefix substring")
    ap.add_argument("--blacklist", nargs='*', default=[], help="Blacklist patterns; delete entire test span if matched")
    ap.add_argument("--blacklist-file", default=None, help="Text file of blacklist patterns (one per line)")
    ap.add_argument("--blacklist-config", default=None, help="YAML config file with blacklist entries")
    ap.add_argument("--cmake-target", default=None, help="Optional target to build (e.g., generated_suite)")
    ap.add_argument("--run-tests", action="store_true", help="Run ctest after successful build and delete failing tests")
    ap.add_argument("--max-iterations", type=int, default=None, help="Max iterations of compile-fix deletion loop")
    # Optional command customizations
    ap.add_argument("--cmake-command", default=None, help="Override 'cmake' executable (e.g., custom path or wrapper)")
    ap.add_argument("--cmake-configure-args", nargs='*', default=None, help="Override args passed to 'cmake' during configure phase")
    ap.add_argument("--cmake-build-args", nargs='*', default=None, help="Override args passed to 'cmake' during build phase")
    ap.add_argument("--ctest-command", default=None, help="Override 'ctest' executable (e.g., custom path or wrapper)")
    ap.add_argument("--ctest-args", nargs='*', default=None, help="Additional args passed to 'ctest' (defaults to --output-on-failure)")
    ap.add_argument("--ctest-regex", default=None, help="Regex for ctest '-R' to include tests")
    ap.add_argument("--ctest-exclude-regex", default=None, help="Regex for ctest '-E' to exclude tests")
    ap.add_argument("--ctest-workdir", default=None, help="Working directory for running ctest (defaults to build_dir)")

    args = ap.parse_args()

    # Load config and merge with CLI args
    cfg = load_compile_fix_config(args.config)

    def pick(key: str, cli_val, default=None):
        return cli_val if cli_val is not None else cfg.get(key, default)

    input_text = pick('input_text', args.input_text)
    target_file = pick('target_file', args.target_file)
    project_root = pick('project_root', args.project_root)
    build_dir = pick('build_dir', args.build_dir)
    audit_dir = pick('audit_dir', args.audit_dir)
    error_prefix = pick('error_prefix', args.error_prefix)
    cmake_target = pick('cmake_target', args.cmake_target)
    run_tests = bool(pick('run_tests', args.run_tests))
    max_iterations = pick('max_iterations', args.max_iterations, 10)
    # Command customizations
    cmake_command = pick('cmake_command', args.cmake_command)
    cmake_configure_args = pick('cmake_configure_args', args.cmake_configure_args)
    cmake_build_args = pick('cmake_build_args', args.cmake_build_args)
    ctest_command = pick('ctest_command', args.ctest_command)
    ctest_args = pick('ctest_args', args.ctest_args)
    ctest_regex = pick('ctest_regex', args.ctest_regex)
    ctest_exclude_regex = pick('ctest_exclude_regex', args.ctest_exclude_regex)
    ctest_workdir = pick('ctest_workdir', args.ctest_workdir)

    # Validate required fields
    missing = [name for name, val in {
        'input_text': input_text,
        'target_file': target_file,
        'project_root': project_root,
        'build_dir': build_dir,
    }.items() if not val]
    if missing:
        logger.error(f"Missing required options: {', '.join(missing)}. Provide via --config or CLI args.")
        return 1

    input_text_path = Path(input_text)
    if not input_text_path.exists():
        logger.error(f"Input text file not found: {input_text_path}")
        return 1

    raw_text = input_text_path.read_text(encoding="utf-8")
    proc = CompileFixProcessor(
        project_root=project_root,
        build_dir=build_dir,
        audit_dir=audit_dir,
        cmake_target=cmake_target,
        cmake_command=cmake_command,
        cmake_configure_args=cmake_configure_args,
        cmake_build_args=cmake_build_args,
        ctest_command=ctest_command,
        ctest_args=ctest_args,
        ctest_regex=ctest_regex,
        ctest_exclude_regex=ctest_exclude_regex,
        ctest_workdir=ctest_workdir,
    )

    # Load blacklist from CLI/file/config
    # Resolve blacklist sources: CLI + file from config + YAML config (prefer explicit --blacklist-config, otherwise use --config)
    bl_file_from_cfg = cfg.get('blacklist_file')
    bl_yaml_path = args.blacklist_config or args.config
    blacklist_patterns = load_blacklist_sources(args.blacklist, bl_file_from_cfg or args.blacklist_file, bl_yaml_path)

    # Write preprocessed content and apply blacklist
    clean_code, spans, deleted_blacklist = proc.preprocess_and_write(
        raw_text, target_file, blacklist_patterns
    )
    logger.info(f"Initial spans parsed: {len(spans)}; deleted by blacklist: {len(deleted_blacklist)}")

    # Configure and initial build
    try:
        proc.cmake_configure()
    except Exception as e:
        logger.error(f"CMake configure failed: {e}")
        return 2

    success, out, err = proc.cmake_build()
    iteration = 0

    # Iteratively fix compile errors by deleting implicated tests
    while not success and iteration < max_iterations:
        iteration += 1
        logger.info(f"Compile failed. Iteration {iteration}")

        new_code, deleted_names = proc.fix_compile_errors(clean_code, spans, err, error_prefix)
        if not deleted_names:
            logger.error("No deletions inferred from compile errors; aborting.")
            break

        # Update file and spans
        clean_code = new_code
        Path(target_file).write_text(clean_code, encoding="utf-8")
        spans = parse_test_cases(clean_code)
        logger.info(f"Deleted tests: {deleted_names}. Remaining spans: {len(spans)}")

        # Rebuild
        success, out, err = proc.cmake_build()

    if not success:
        logger.error("Build failed after iterative deletions.")
        return 3

    # Optionally run tests and delete failing ones, then rebuild once
    if run_tests:
        ok, t_out, t_err = proc.ctest_run()
        if not ok:
            new_code, deleted_runtime = proc.fix_runtime_failures(clean_code, spans, t_out + "\n" + t_err)
            if deleted_runtime:
                Path(target_file).write_text(new_code, encoding="utf-8")
                spans = parse_test_cases(new_code)
                logger.info(f"Deleted failing tests: {deleted_runtime}. Rebuilding...")
                success, out, err = proc.cmake_build()
                if not success:
                    logger.error("Rebuild failed after deleting failing tests.")
                    return 4

    logger.info("Compile-fix workflow completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())