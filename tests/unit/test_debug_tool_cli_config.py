import os
import sys
from pathlib import Path
import textwrap

# Ensure repository root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.debug_tool.cli.compile_fix import load_compile_fix_config


def test_load_compile_fix_config_default(tmp_path, monkeypatch):
    # Create a temporary config mirroring compile_fix structure
    cfg_file = tmp_path / "compile_fix.yaml"
    cfg_file.write_text(textwrap.dedent(
        """
        debug_tool:
          compile_fix:
            input_text: "exp/in.txt"
            target_file: "proj/tests/out.cpp"
            project_root: "proj"
            build_dir: "proj/build"
            audit_dir: "exp/logs"
            error_prefix: "out.cpp"
            cmake_target: "generated_suite"
            run_tests: true
            max_iterations: 7
            blacklist:
              - A
              - B
        """
    ))

    cfg = load_compile_fix_config(str(cfg_file))
    assert cfg["input_text"] == "exp/in.txt"
    assert cfg["target_file"] == "proj/tests/out.cpp"
    assert cfg["error_prefix"] == "out.cpp"
    assert cfg["cmake_target"] == "generated_suite"
    assert cfg["run_tests"] is True
    assert cfg["max_iterations"] == 7
    assert cfg["blacklist"] == ["A", "B"]