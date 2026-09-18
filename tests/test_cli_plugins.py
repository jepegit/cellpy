"""CLI plugin discovery contract (#1055).

Mirrors ``tests/test_loader_contract.py`` entry-point tests: monkeypatch
``_iter_entry_points``, never rely on installed third-party plugins.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from types import SimpleNamespace

import click
import pytest
import typer

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


@pytest.mark.essential
def test_discover_does_not_load(monkeypatch):
    app = typer.Typer()
    ep = _FakeEntryPoint("connectors", "pkg:app", app)
    _patch_entry_points(monkeypatch, ep)

    found = cli_plugins.discover()
    assert list(found) == ["connectors"]
    assert found["connectors"] is ep
    assert ep.loads == 0

    loaded = cli_plugins.load_plugin("connectors")
    assert loaded is app
    assert ep.loads == 1


@pytest.mark.essential
def test_load_plugin_accepts_click_command(monkeypatch):
    @click.command()
    def ping():
        """Ping."""

    _patch_entry_points(monkeypatch, _FakeEntryPoint("ping", "pkg:ping", ping))
    assert cli_plugins.load_plugin("ping") is ping


@pytest.mark.essential
def test_a_broken_plugin_does_not_break_discovery(monkeypatch, caplog):
    app = typer.Typer()
    _patch_entry_points(
        monkeypatch,
        _FakeEntryPoint("broken", "pkg:Nope", boom=ImportError("no such module")),
        _FakeEntryPoint("good", "pkg:app", app),
    )
    with caplog.at_level(logging.WARNING):
        names = cli_plugins.discover()
        loaded = cli_plugins.load_all()
    assert "broken" in names
    assert "good" in names
    assert "good" in loaded
    assert "broken" not in loaded
    assert loaded["good"] is app
    assert "broken" in caplog.text
    assert "fake-dist" in caplog.text


@pytest.mark.essential
def test_a_non_command_object_is_skipped(monkeypatch, caplog):
    _patch_entry_points(monkeypatch, _FakeEntryPoint("impostor", "pkg:Nope", object()))
    with caplog.at_level(logging.WARNING):
        assert cli_plugins.load_plugin("impostor") is None
        assert cli_plugins.load_all() == {}
    assert "impostor" in caplog.text
    assert "fake-dist" in caplog.text


@pytest.mark.essential
def test_duplicate_names_keep_the_first(monkeypatch, caplog):
    first = _FakeEntryPoint("connectors", "pkg:a", typer.Typer(), dist=SimpleNamespace(name="first-dist"))
    second = _FakeEntryPoint("connectors", "pkg:b", typer.Typer(), dist=SimpleNamespace(name="second-dist"))
    _patch_entry_points(monkeypatch, first, second)
    with caplog.at_level(logging.WARNING):
        found = cli_plugins.discover()
    assert found["connectors"] is first
    assert "second-dist" in caplog.text


@pytest.mark.essential
def test_discovery_is_lazy(monkeypatch):
    calls = []

    def _spy():
        calls.append(1)
        return []

    monkeypatch.setattr(cli_plugins, "_iter_entry_points", _spy)
    cli_plugins.clear()
    assert not calls, "importing/clearing must not scan entry points"
    cli_plugins.discover()
    assert len(calls) == 1
    cli_plugins.discover()
    assert len(calls) == 1, "discovery result should be cached"
    cli_plugins.discover(refresh=True)
    assert len(calls) == 2


@pytest.mark.essential
def test_import_cellpy_does_not_import_cli_plugins():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent("""
                import sys
                import cellpy
                assert "cellpy.cli_plugins" not in sys.modules, sorted(
                    m for m in sys.modules if m.startswith("cellpy")
                )
                """).strip() + "\n",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.essential
def test_we_query_the_documented_entry_point_group(monkeypatch):
    seen = {}

    def _fake_entry_points(*, group):
        seen["group"] = group
        return []

    monkeypatch.setattr(cli_plugins, "entry_points", _fake_entry_points)
    list(cli_plugins._iter_entry_points())
    assert seen["group"] == "cellpy.cli_plugins"
    assert cli_plugins.ENTRY_POINT_GROUP == "cellpy.cli_plugins"


@pytest.mark.essential
def test_unknown_name_returns_none(monkeypatch):
    _patch_entry_points(monkeypatch)
    assert cli_plugins.load_plugin("missing") is None
