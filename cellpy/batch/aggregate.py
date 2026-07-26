"""Batch aggregation (batch v3, #701).

Turns a set of loaded cells into one tidy, long-format frame with ``cell`` /
``group`` / ``sub_group`` key columns -- replacing the legacy wide/multiindex
``join_summaries`` machinery. This is the frame the collectors redesign
(Epic B) builds on, so it lands here as ``batch.aggregate.combine_summaries``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl

from cellpy.batch.journal import FILENAME, Journal


def _group_lookup(journal: Journal | None) -> dict[str, tuple[Any, Any]]:
    """label -> (group, sub_group) from the journal pages."""
    lookup: dict[str, tuple[Any, Any]] = {}
    if journal is None:
        return lookup
    pages = journal.pages
    if FILENAME not in pages.columns:
        return lookup
    has_group = "group" in pages.columns
    has_sub = "sub_group" in pages.columns
    for row in pages.iter_rows(named=True):
        lookup[row[FILENAME]] = (
            row.get("group") if has_group else None,
            row.get("sub_group") if has_sub else None,
        )
    return lookup


def _summary_of(cell: Any) -> pl.DataFrame | None:
    summary = getattr(getattr(cell, "data", None), "summary", None)
    if summary is None:
        return None
    if isinstance(summary, pl.DataFrame):
        return summary
    try:
        return pl.from_pandas(summary)
    except (TypeError, ValueError):
        return None


def combine_summaries(
    cells: Mapping[str, Any], journal: Journal | None = None
) -> pl.DataFrame:
    """Concatenate per-cell summaries into one tidy long-format frame.

    Each row keeps its cell's summary columns plus ``cell``/``group``/
    ``sub_group`` keys. Cells without a summary are skipped. Returns an empty
    frame when nothing has a summary.
    """
    lookup = _group_lookup(journal)
    frames: list[pl.DataFrame] = []
    for label, cell in cells.items():
        summary = _summary_of(cell)
        if summary is None or summary.height == 0:
            continue
        group, sub_group = lookup.get(label, (None, None))
        frames.append(
            summary.with_columns(
                pl.lit(label).alias("cell"),
                pl.lit(group).alias("group"),
                pl.lit(sub_group).alias("sub_group"),
            )
        )
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="diagonal_relaxed")
