"""Per-cell iteration for collection.

Successor of ``pick_named_cell`` with **per-cell isolation**: one cell's filter
results never leak into the next (fixes the cross-cell ``cycles`` narrowing bug
at collectors.py:1609/1691). Also carries the label-mapper idea (presentation
names != file names).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from cellpy.batch.journal import FILENAME


@dataclass
class CellItem:
    """One cell in a collection pass, with its group metadata."""

    label: str
    group: Any
    sub_group: Any
    cell: Any


def iter_cells(
    batch: Any, label_mapper: Mapping[str, str] | None = None
) -> Iterator[CellItem]:
    """Yield the batch's loaded cells with their journal group/sub_group."""
    lookup: dict[str, tuple[Any, Any]] = {}
    pages = batch.journal.pages
    if FILENAME in pages.columns:
        has_group = "group" in pages.columns
        has_sub = "sub_group" in pages.columns
        for row in pages.iter_rows(named=True):
            lookup[row[FILENAME]] = (
                row.get("group") if has_group else None,
                row.get("sub_group") if has_sub else None,
            )

    for label, cell in batch.cells.items():
        group, sub_group = lookup.get(label, (None, None))
        name = label_mapper.get(label, label) if label_mapper else label
        yield CellItem(label=name, group=group, sub_group=sub_group, cell=cell)
