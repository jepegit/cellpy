"""Live ``cellpy-connectors`` plugin (installed dist, no entry-point monkeypatch)."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from importlib import metadata

import pytest
from typer.testing import CliRunner

from cellpy import cli as cellpy_cli
from cellpy import cli_plugins

PING_MESSAGE = "cellpy-connectors: ok"


def _require_connectors() -> None:
    try:
        metadata.distribution("cellpy-connectors")
    except metadata.PackageNotFoundError:
        pytest.skip("cellpy-connectors not installed (uv sync git pin)")


@pytest.fixture(autouse=True)
def _clean_registry():
    cli_plugins.clear()
    yield
    cli_plugins.clear()


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script).strip() + "\n"],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.essential
def test_help_lists_installed_connectors_without_importing_it():
    _require_connectors()
    completed = _run_script(
        """
        import sys
        from typer.testing import CliRunner

        from cellpy import cli as cellpy_cli
        from cellpy import cli_plugins

        cli_plugins.clear()
        result = CliRunner().invoke(cellpy_cli.cli, ["--help"])
        assert result.exit_code == 0, result.output
        assert "connectors" in result.output
        assert "cellpy_connectors" not in sys.modules
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.essential
def test_connectors_ping_runs_the_installed_plugin():
    _require_connectors()
    result = CliRunner().invoke(cellpy_cli.cli, ["connectors", "ping"])
    assert result.exit_code == 0, result.output
    assert PING_MESSAGE in result.output


@pytest.mark.essential
def test_import_cellpy_does_not_import_connectors():
    _require_connectors()
    completed = _run_script(
        """
        import sys
        import cellpy

        assert "cellpy_connectors" not in sys.modules
        """
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
