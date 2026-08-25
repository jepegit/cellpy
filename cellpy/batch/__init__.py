"""Load and work with a set of cells.

Typical use::

    from cellpy import batch
    b = batch.load(name="exp", project="proj")
    b.summaries
    b.cells["cell_01"]
    b.plot()
    b.result.report()

``b`` is a `Batch`. ``cellpy.utils.batch`` re-exports the same entry
points.
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
from cellpy.batch.facade import Batch, from_cells, from_journal, load

__all__ = [
    "Batch",
    "load",
    "from_journal",
    "from_cells",
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
