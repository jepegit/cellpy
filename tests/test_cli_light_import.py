"""CLI bootstrap must stay light (#837, #839).

Light commands should not drag in the reader stack or optional CLI probes.
Run in a subprocess so prior test imports cannot pollute ``sys.modules``.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script).strip() + "\n"],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.essential
def test_info_version_avoids_cellreader_import():
    completed = _run_script(
        """
        import sys
        from typer.testing import CliRunner

        import cellpy.cli

        assert "cellpy.readers.cellreader" not in sys.modules, sorted(
            m for m in sys.modules if m.startswith("cellpy")
        )

        result = CliRunner().invoke(cellpy.cli.cli, ["info", "--version"])
        assert result.exit_code == 0, result.output
        assert "cellpy " in result.output
        assert "cellpy.readers.cellreader" not in sys.modules, sorted(
            m for m in sys.modules if m.startswith("cellpy")
        )
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.essential
def test_setup_default_avoids_cellreader_and_optional_deps():
    """Default setup must not import cellreader or probe lmfit (#839)."""
    completed = _run_script(
        """
        import sys
        import tempfile
        from pathlib import Path
        from typer.testing import CliRunner

        import cellpy.cli
        from cellpy import config, prmreader

        tmp = Path(tempfile.mkdtemp())
        prmreader.get_user_dir = lambda: tmp
        config.paths.env_file = tmp / ".env_cellpy"
        result = CliRunner().invoke(
            cellpy.cli.cli, ["setup", "--silent", "--test_user", "light_import"]
        )
        assert result.exit_code == 0, result.output
        assert "cellpy.readers.cellreader" not in sys.modules, sorted(
            m for m in sys.modules if "cellpy" in m or m == "lmfit"
        )
        assert "lmfit" not in sys.modules
        assert "sqlalchemy_access" not in sys.modules
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.essential
def test_setup_check_imports_cellreader():
    """``setup --check`` still exercises the reader import path (#839)."""
    completed = _run_script(
        """
        import sys
        import tempfile
        from pathlib import Path
        from typer.testing import CliRunner

        import cellpy.cli
        from cellpy import config, prmreader

        tmp = Path(tempfile.mkdtemp())
        prmreader.get_user_dir = lambda: tmp
        config.paths.env_file = tmp / ".env_cellpy"
        result = CliRunner().invoke(
            cellpy.cli.cli,
            ["setup", "--silent", "--check", "--test_user", "light_import_check"],
        )
        assert result.exit_code == 0, result.output
        assert "cellpy.readers.cellreader" in sys.modules
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.essential
def test_importing_cli_ui_does_not_import_rich():
    """``cli_ui`` defers rich to first output, so importing it stays cheap (#891)."""
    completed = _run_script(
        """
        import sys

        import cellpy.cli_ui

        assert not [m for m in sys.modules if m.startswith("rich")], sorted(
            m for m in sys.modules if m.startswith("rich")
        )
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.essential
def test_setup_deps_probes_optional_modules():
    """``setup --deps`` opts into optional-extra probing (#839)."""
    completed = _run_script(
        """
        import sys
        from typer.testing import CliRunner

        import cellpy.cli

        result = CliRunner().invoke(
            cellpy.cli.cli, ["setup", "--silent", "--dry-run", "--deps"]
        )
        assert result.exit_code == 0, result.output
        assert "lmfit" in sys.modules or "checking dependencies" in result.output
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
