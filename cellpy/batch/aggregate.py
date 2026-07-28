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


#: Scalar TestMeta fields surfaced by :func:`combine_tests` (skips nested/object
#: fields like ``cell``; ``raw_file_names`` is joined to a string).
_TEST_FIELDS = (
    "test_id",
    "cell_name",
    "cycle_mode",
    "test_family",
    "test_type",
    "source_type",
    "source_uri",
    "channel",
    "creator",
    "start_datetime",
    "loaded_datetime",
    "voltage_lim_low",
    "voltage_lim_high",
    "comment",
)


def _tests_of(cell: Any) -> list[dict[str, Any]]:
    """Per-test metadata records of a cell as plain dicts (native fields only)."""
    data = getattr(cell, "data", None)
    collection = getattr(data, "tests", None)
    if collection is None:
        return []
    rows: list[dict[str, Any]] = []
    for record in collection:
        row = {f: getattr(record, f, None) for f in _TEST_FIELDS}
        raw_files = getattr(record, "raw_file_names", None)
        if raw_files:
            row["raw_file_names"] = "; ".join(str(p) for p in raw_files)
        rows.append(row)
    return rows


def combine_tests(
    cells: Mapping[str, Any], journal: Journal | None = None
) -> pl.DataFrame:
    """Per-test metadata across the batch as one tidy long-format frame.

    One row per (cell, ``test_id``) carrying the native ``TestMeta`` fields plus
    ``cell``/``group``/``sub_group`` keys. Surfaces the per-test records that a
    merged (campaign) cell holds in ``Data.tests`` (#506) at the batch level.
    Returns an empty frame when no cell exposes test metadata.
    """
    lookup = _group_lookup(journal)
    rows: list[dict[str, Any]] = []
    for label, cell in cells.items():
        group, sub_group = lookup.get(label, (None, None))
        for row in _tests_of(cell):
            rows.append(
                {"cell": label, "group": group, "sub_group": sub_group, **row}
            )
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows)


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
