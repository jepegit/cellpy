# -*- coding: utf-8 -*-

"""cellpy — battery cell cycling data tools."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from cellpy._version import __version__

__author__ = (
    "Jan Petter Maehlen",
    "Asbjoern Ulvestad",
    "Muhammad Abdelhamid",
    "Julia Wind",
)
__email__ = (
    "jepe@ife.no",
    "Asbjorn.Ulvestad@ife.no",
    "Muhammad.Abdelhamid@ife.no",
    "julia.wind@ife.no",
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Config loads lazily on first ``cellpy.config`` / ``config.*`` access, or via
# ``cellpy.parameters.prmreader.initialize()`` (issue #453).
#
# Heavy submodules (readers / cellreader / …) are also lazy so ``import cellpy``
# and the CLI entry point stay light (#837).

# Sanctioned top-level API (v2, issue #509): ``cellpy.get`` is the primary
# entry point; ``cellpy.merge_cells`` and ``cellpy.print_instruments`` are the
# supporting conveniences. ``cellpy.read_meta`` peeks cellpy-file metadata
# without loading frames (issue #799). Everything else is reached via explicit
# module paths (``cellpy.cellreader``, ``cellpy.config`` / ``cellpy.config.session``).

__all__ = [
    "cellreader",
    "dbreader",
    "prmreader",
    "prms",
    "filefinder",
    "get",
    "merge_cells",
    "print_instruments",
    "list_instruments",
    "instrument_meta_schema",
    "read_meta",
    "do",
]

_LAZY_MODULES = {
    "parameters": "cellpy.parameters",
    "readers": "cellpy.readers",
    "prms": "cellpy.parameters.prms",
    "prmreader": "cellpy.parameters.prmreader",
    "cellreader": "cellpy.readers.cellreader",
    "dbreader": "cellpy.readers.dbreader",
    "filefinder": "cellpy.readers.filefinder",
    "do": "cellpy.readers.do",
    "data_structures": "cellpy.readers.data_structures",
}

_LAZY_ATTRS = {
    "get": ("cellpy.readers.cellreader", "get"),
    "merge_cells": ("cellpy.readers.cellreader", "merge_cells"),
    "print_instruments": ("cellpy.readers.cellreader", "print_instruments"),
    "list_instruments": ("cellpy.readers.data_structures", "list_instruments"),
    "instrument_meta_schema": (
        "cellpy.readers.data_structures",
        "instrument_meta_schema",
    ),
}


def read_meta(path):
    """Read cellpy-file metadata without loading raw/steps/summary frames.

    See ``cellpy.readers.cellpy_file.read_meta`` for details.
    """
    from cellpy.readers.cellpy_file import read_meta as _read_meta

    return _read_meta(path)


def __getattr__(name: str) -> Any:
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name])
        globals()[name] = mod
        return mod
    if name in _LAZY_ATTRS:
        mod_name, attr = _LAZY_ATTRS[name]
        value = getattr(importlib.import_module(mod_name), attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_LAZY_MODULES) + list(_LAZY_ATTRS))
