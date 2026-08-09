"""Parallel pydantic-settings configuration stack.

Production code should use ``cellpy.config`` directly. Legacy ``cellpy.parameters.prms``
forwards here via a deprecated shim.
"""

from __future__ import annotations

from typing import Any

from cellpy.config.loader import ActiveConfigFile, LoadOptions, active_config_file
from cellpy.config.models import CellpyConfig
from cellpy.config.session import (
    get_config,
    override,
    reload,
    reset_session,
    set_load_options,
    sources,
)

_SECTION_NAMES = frozenset(
    {
        "paths",
        "file_names",
        "reader",
        "db",
        "db_cols",
        "batch",
        "instruments",
        "defaults",
        "units",
        "secrets",
    }
)

__all__ = [
    "ActiveConfigFile",
    "CellpyConfig",
    "LoadOptions",
    "active_config_file",
    "get_config",
    "override",
    "reload",
    "reset_session",
    "set_load_options",
    "sources",
]


def __getattr__(name: str) -> Any:
    if name in _SECTION_NAMES:
        return getattr(get_config(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
