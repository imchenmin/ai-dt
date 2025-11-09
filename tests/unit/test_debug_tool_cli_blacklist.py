import os
import sys
import textwrap
from pathlib import Path

# Ensure repository root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.debug_tool.cli.compile_fix import load_blacklist_sources


def test_load_blacklist_sources_union(tmp_path):
    # Create blacklist text file
    bl_file = tmp_path / "blacklist.txt"
    bl_file.write_text(textwrap.dedent("""
    # comment line
    // comment line
    mock_variadic
    
    ON_CALL(
    """))

    # Create YAML config
    yaml_file = tmp_path / "compile_fix.yaml"
    yaml_file.write_text(textwrap.dedent("""
    debug_tool:
      compile_fix:
        blacklist:
          - "MOCKER("
          - FromYaml
    """))

    cli = ["ExtraPattern", "MOCKER("]
    merged = load_blacklist_sources(cli, str(bl_file), str(yaml_file))
    assert set(merged) == {"ExtraPattern", "MOCKER(", "FromYaml", "mock_variadic", "ON_CALL("}