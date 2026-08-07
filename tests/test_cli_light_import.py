"""CLI bootstrap must stay light (#837).

``cellpy info --version`` should not drag in the reader stack. Run in a
subprocess so prior test imports cannot pollute ``sys.modules``.
"""

from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.essential
def test_info_version_avoids_cellreader_import():
    script = r"""
import sys
from typer.testing import CliRunner

import cellpy.cli

assert "cellpy.readers.cellreader" not in sys.modules, sorted(
    m for m in sys.modules if m.startswith("cellpy")
)

result = CliRunner().invoke(cellpy.cli.cli, ["info", "--version"])
assert result.exit_code == 0, result.output
assert "[cellpy] version:" in result.output
assert "cellpy.readers.cellreader" not in sys.modules, sorted(
    m for m in sys.modules if m.startswith("cellpy")
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
