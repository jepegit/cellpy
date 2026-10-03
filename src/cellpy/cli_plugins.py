"""Discover third-party CLI commands via entry points.

This module discovers plugins and attaches lazy stubs onto the live Typer
group (``attach_plugin_stubs``). ``EntryPoint.load()`` still runs only when
a stub is invoked or asked for its own help.

Discovery is **lazy** — the entry-point group is read on first ``discover()``,
not at ``import cellpy`` or import of this module. ``EntryPoint.load()``
runs only when ``load_plugin`` / ``load_all`` asks for the command object.

Failures are contained: a plugin that cannot be imported, or that is not a
``typer.Typer`` / ``click.Group`` / ``click.Command``, is logged and skipped.
"""

from __future__ import annotations

import logging
from importlib.metadata import EntryPoint, entry_points
from typing import Iterable

import click
import typer
import typer.main
from typer.core import TyperGroup

ENTRY_POINT_GROUP = "cellpy.cli_plugins"

BUILTIN_COMMANDS = frozenset(
    {
        "convert",
        "edit",
        "info",
        "mcp",
        "new",
        "pull",
        "run",
        "serve",
        "setup",
    }
)

_DISCOVERED: dict[str, EntryPoint] | None = None
_LOADED: dict[str, object] | None = None

logger = logging.getLogger(__name__)


def _dist_name(entry_point: EntryPoint) -> str:
    dist = getattr(entry_point, "dist", None)
    if dist is None:
        return "?"
    return getattr(dist, "name", None) or "?"


def _is_cli_plugin(obj: object) -> bool:
    # Typer is not a Click subclass; check it first.
    if isinstance(obj, typer.Typer):
        return True
    return isinstance(obj, click.Command)


def _iter_entry_points() -> Iterable[EntryPoint]:
    return entry_points(group=ENTRY_POINT_GROUP)


def _scan_names() -> dict[str, EntryPoint]:
    found: dict[str, EntryPoint] = {}
    for entry_point in _iter_entry_points():
        name = entry_point.name
        if name in found:
            logger.warning(
                "CLI plugin %r declared more than once; keeping %s, skip %s",
                name,
                _dist_name(found[name]),
                _dist_name(entry_point),
            )
            continue
        found[name] = entry_point
    return found


def discover(*, refresh: bool = False) -> dict[str, EntryPoint]:
    """Entry points keyed by mount name. First name wins. No ``load()``."""
    global _DISCOVERED, _LOADED
    if _DISCOVERED is None or refresh:
        _DISCOVERED = _scan_names()
        if refresh:
            _LOADED = None
    return dict(_DISCOVERED)


def clear() -> None:
    """Forget discovery and load caches (tests; after installing a plugin)."""
    global _DISCOVERED, _LOADED
    _DISCOVERED = None
    _LOADED = None


def load_plugin(name: str) -> typer.Typer | click.Command | None:
    """Load and type-check one plugin. Fail-soft: warnings, never raise."""
    global _LOADED
    if _LOADED is None:
        _LOADED = {}
    if name in _LOADED:
        return _LOADED[name]

    entry_point = discover().get(name)
    if entry_point is None:
        return None

    try:
        obj = entry_point.load()
    except Exception as exc:
        logger.warning(
            "could not load CLI plugin %r from %s (%s): %s",
            name,
            getattr(entry_point, "value", "?"),
            _dist_name(entry_point),
            exc,
        )
        return None

    if not _is_cli_plugin(obj):
        logger.warning(
            "CLI plugin %r from %s (%s) is not a " "typer.Typer / click.Group / click.Command; skipped",
            name,
            getattr(entry_point, "value", "?"),
            _dist_name(entry_point),
        )
        return None

    _LOADED[name] = obj
    return obj


def load_all() -> dict[str, typer.Typer | click.Command]:
    """Load every discovered name; return only plugins that loaded cleanly."""
    loaded: dict[str, typer.Typer | click.Command] = {}
    for name in discover():
        obj = load_plugin(name)
        if obj is not None:
            loaded[name] = obj
    return loaded


def _as_click_command(obj: typer.Typer | click.Command) -> object:
    if isinstance(obj, typer.Typer):
        return typer.main.get_command(obj)
    return obj


class LazyPluginGroup(TyperGroup):
    """Placeholder listed on ``cellpy --help``; loads the plugin on invoke."""

    def __init__(self, name: str) -> None:
        super().__init__(name=name, help="Third-party CLI plugin.")
        self._real: object | None | bool = None

    def _load(self) -> object | None:
        if self._real is False:
            return None
        if self._real is not None:
            return self._real
        obj = load_plugin(self.name)
        if obj is None:
            self._real = False
            return None
        self._real = _as_click_command(obj)
        return self._real

    def invoke(self, ctx):
        real = self._load()
        if real is None:
            return None
        return real.invoke(ctx)

    def get_command(self, ctx, cmd_name: str):
        real = self._load()
        getter = getattr(real, "get_command", None)
        if getter is None:
            return None
        return getter(ctx, cmd_name)

    def list_commands(self, ctx) -> list[str]:
        real = self._load()
        lister = getattr(real, "list_commands", None)
        if lister is None:
            return []
        return list(lister(ctx))

    def format_help(self, ctx, formatter) -> None:
        real = self._load()
        if real is None:
            return None
        return real.format_help(ctx, formatter)


def attach_plugin_stubs(group: TyperGroup) -> None:
    """Register lazy stubs for discovered names. Never replaces a built-in."""
    for name, entry_point in discover().items():
        current = group.commands.get(name)
        taken = current is not None and not isinstance(current, LazyPluginGroup)
        if name in BUILTIN_COMMANDS or taken:
            logger.warning(
                "CLI plugin %r from %s collides with a built-in command; skipped",
                name,
                _dist_name(entry_point),
            )
            continue
        if current is None:
            group.commands[name] = LazyPluginGroup(name)


class CellpyCLIGroup(TyperGroup):
    """Root Click group: attach plugin stubs before command lookup."""

    def list_commands(self, ctx) -> list[str]:
        try:
            attach_plugin_stubs(self)
        except Exception:
            logger.exception("failed to attach CLI plugin stubs")
        return super().list_commands(ctx)

    def get_command(self, ctx, cmd_name: str):
        try:
            attach_plugin_stubs(self)
        except Exception:
            logger.exception("failed to attach CLI plugin stubs")
        return super().get_command(ctx, cmd_name)
