"""Discover third-party CLI commands via entry points.

This module is the contract Stage 2 mounts onto ``cellpy.cli``. It does **not**
register commands itself.

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

ENTRY_POINT_GROUP = "cellpy.cli_plugins"

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
            "CLI plugin %r from %s (%s) is not a "
            "typer.Typer / click.Group / click.Command; skipped",
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
