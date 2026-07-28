"""cellpy.batch -- the batch v3 subsystem (#696).

A boring, standard architecture for batch processing, which replaced the
``utils/batch_tools`` "farm/barn" machinery (removed in 2.1, E4 #716);
``cellpy.utils.batch`` is a thin re-export/shim.

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
from cellpy.batch import aggregate, outputs, qc
from cellpy.batch.aggregate import combine_summaries, combine_tests
from cellpy.batch.db import journal_from_db
from cellpy.batch.facade import Batch, from_journal, load

__all__ = [
    "Batch",
    "load",
    "from_journal",
    "aggregate",
    "qc",
    "outputs",
    "combine_summaries",
    "combine_tests",
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
