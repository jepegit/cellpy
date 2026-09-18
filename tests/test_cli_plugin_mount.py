"""Live CLI mount for ``cellpy.cli_plugins`` (#1058)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from types import SimpleNamespace

import click
import pytest
import typer
from typer.testing import CliRunner

from cellpy import cli as cellpy_cli
from cellpy import cli_plugins


@dataclass
class _FakeEntryPoint:
    name: str
    value: str
    target: object = None
    boom: Exception | None = None
    dist: object = field(default_factory=lambda: SimpleNamespace(name="fake-dist"))
    loads: int = 0

    def load(self):
        self.loads += 1
        if self.boom is not None:
            raise self.boom
        return self.target


def _patch_entry_points(monkeypatch, *eps):
    monkeypatch.setattr(cli_plugins, "_iter_entry_points", lambda: list(eps))
    cli_plugins.clear()


@pytest.fixture(autouse=True)
def _clean_registry():
    cli_plugins.clear()
    yield
    cli_plugins.clear()


def _typer_plugin(message: str = "PLUGIN_OK") -> typer.Typer:
    app = typer.Typer()

    @app.callback(invoke_without_command=True)
    def _root():
        typer.echo(message)

    return app


@pytest.mark.essential
def test_help_lists_a_plugin_without_loading_it(monkeypatch):
    app = _typer_plugin()
    ep = _FakeEntryPoint("connectors", "pkg:app", app)
    _patch_entry_points(monkeypatch, ep)

    result = CliRunner().invoke(cellpy_cli.cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "connectors" in result.output
    assert ep.loads == 0


@pytest.mark.essential
def test_invoking_a_typer_plugin_runs_it(monkeypatch):
    app = _typer_plugin()
    ep = _FakeEntryPoint("connectors", "pkg:app", app)
    _patch_entry_points(monkeypatch, ep)

    result = CliRunner().invoke(cellpy_cli.cli, ["connectors"])
    assert result.exit_code == 0, result.output
    assert "PLUGIN_OK" in result.output
    assert ep.loads >= 1


@pytest.mark.essential
def test_invoking_a_click_command_plugin_runs_it(monkeypatch):
    @click.command()
    def ping():
        click.echo("PONG")

    ep = _FakeEntryPoint("ping", "pkg:ping", ping)
    _patch_entry_points(monkeypatch, ep)

    result = CliRunner().invoke(cellpy_cli.cli, ["ping"])
    assert result.exit_code == 0, result.output
    assert "PONG" in result.output


@pytest.mark.essential
def test_a_broken_plugin_invoke_is_fail_soft(monkeypatch, caplog):
    ep = _FakeEntryPoint("broken", "pkg:Nope", boom=ImportError("no such module"))
    _patch_entry_points(monkeypatch, ep)

    with caplog.at_level(logging.WARNING):
        result = CliRunner().invoke(cellpy_cli.cli, ["broken"])
    assert result.exit_code == 0, result.output
    assert "broken" in caplog.text
    assert "fake-dist" in caplog.text


@pytest.mark.essential
def test_a_plugin_named_info_does_not_replace_the_builtin(monkeypatch, caplog):
    app = _typer_plugin("STOLEN")
    _patch_entry_points(monkeypatch, _FakeEntryPoint("info", "pkg:app", app))

    with caplog.at_level(logging.WARNING):
        help_result = CliRunner().invoke(cellpy_cli.cli, ["--help"])
        version = CliRunner().invoke(cellpy_cli.cli, ["info", "--version"])
    assert help_result.exit_code == 0, help_result.output
    assert version.exit_code == 0, version.output
    assert "cellpy " in version.output
    assert "STOLEN" not in version.output
    assert "info" in caplog.text
    assert "fake-dist" in caplog.text


@pytest.mark.essential
def test_surface_snapshot_ignores_registered_plugins(monkeypatch):
    import json
    from pathlib import Path

    from tests.test_cli_surface import _live_surface

    app = _typer_plugin()
    _patch_entry_points(monkeypatch, _FakeEntryPoint("connectors", "pkg:app", app))
    snapshot = json.loads((Path(__file__).parent / "data" / "cli_surface.json").read_text(encoding="utf-8"))
    live = _live_surface()
    assert [c["name"] for c in live["commands"]] == [c["name"] for c in snapshot["commands"]]
    assert "connectors" not in [c["name"] for c in live["commands"]]
