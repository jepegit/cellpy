"""cellpy.batch -- the batch v3 subsystem (#696).

A boring, standard architecture for batch processing, replacing the
``utils/batch_tools`` "farm/barn" machinery. Built alongside the old code;
``cellpy.utils.batch`` becomes a thin re-export/shim.

Modules land incrementally (plan sections 4 & 6):
    journal  -- Journal model + json readers/writers  (#698, this arc)
    layout   -- BatchPaths: pure path computation + ensure_dirs  (#698)
    policy   -- LoadPolicy / CellSpec typed options  (#699)
    runner   -- load_cell / run -> BatchResult  (#700)
    ...
"""

from __future__ import annotations

from cellpy.batch.journal import (
    Journal,
    journal_from_custom_json,
    journal_from_frame,
    read_custom_json,
    read_journal,
    write_journal,
)
from cellpy.batch.layout import BatchPaths, ensure_dirs
from cellpy.batch.policy import (
    CellSpec,
    LoadPolicy,
    SourcePreference,
    parse_argument,
    resolve_specs,
)
from cellpy.batch.result import (
    BatchLoadError,
    BatchResult,
    CellOutcome,
    CellResult,
)
from cellpy.batch.runner import load_cell, run
from cellpy.batch.store import CellStore

__all__ = [
    "Journal",
    "read_journal",
    "write_journal",
    "journal_from_frame",
    "read_custom_json",
    "journal_from_custom_json",
    "BatchPaths",
    "ensure_dirs",
    "SourcePreference",
    "LoadPolicy",
    "CellSpec",
    "resolve_specs",
    "parse_argument",
    "CellResult",
    "BatchResult",
    "CellOutcome",
    "BatchLoadError",
    "load_cell",
    "run",
    "CellStore",
]
