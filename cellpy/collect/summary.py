"""Summary collection.

Assembles per-cell summaries into one tidy :class:`Collection`, carrying the
full rate-filtering / grouping / CV-partition feature set of the legacy
``helpers.concat_summaries`` on the :class:`SummaryOptions` model. Cycle-level
work (rate/CV/max-cycle) happens per cell in :mod:`._summary_ops`; combination,
column selection, group averaging and cleanup happen on the combined frame.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import polars as pl

from cellpy.batch.journal import FILENAME
from cellpy.collect import _summary_ops as ops
from cellpy.collect.collection import Collection, CollectionMeta
from cellpy.collect.options import SummaryOptions

_KEYS = ("cell", "group", "sub_group", "group_label", "label", ops.CYCLE)


def _pages_lookup(batch: Any) -> dict[str, dict[str, Any]]:
    """label -> row-dict of journal metadata (group/sub_group/group_label/selected)."""
    lookup: dict[str, dict[str, Any]] = {}
    pages = batch.journal.pages
    if FILENAME not in pages.columns:
        return lookup
    wanted = [
        c
        for c in ("group", "sub_group", "group_label", "label", "selected")
        if c in pages.columns
    ]
    for row in pages.iter_rows(named=True):
        lookup[row[FILENAME]] = {c: row.get(c) for c in wanted}
    return lookup


def collect_summaries(
    batch: Any, options: SummaryOptions | None = None, **overrides
) -> Collection:
    """Collect per-cell summaries into one tidy :class:`Collection`.

    With defaults this is a plain long-format concatenation (one row per
    cell/cycle). The options add rate filtering, CV partition, per-group
    averaging and inf/extreme cleanup -- see :class:`SummaryOptions`.
    """
    opts = options or SummaryOptions()
    if overrides:
        opts = opts.replace(**overrides)

    lookup = _pages_lookup(batch)

    frames: list[pl.DataFrame] = []
    included: list[str] = []
    for label, cell in batch.cells.items():
        meta = lookup.get(label, {})
        if opts.only_selected and "selected" in meta and meta.get("selected") != 1:
            continue

        frame = ops.extract_cell_summary(cell, opts)
        if frame is None or frame.height == 0:
            continue

        frames.append(
            frame.with_columns(
                pl.lit(label).alias("cell"),
                pl.lit(meta.get("group")).alias("group"),
                pl.lit(meta.get("sub_group")).alias("sub_group"),
                pl.lit(meta.get("group_label")).alias("group_label"),
                pl.lit(meta.get("label")).alias("label"),
            )
        )
        included.append(label)

    frame = (
        pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()
    )

    if opts.columns and frame.height:
        keep = [c for c in _KEYS if c in frame.columns]
        wanted = list(opts.columns)
        if opts.partition_by_cv:
            # keep the derived CV split alongside each requested metric
            wanted = [
                name
                for col in wanted
                for name in (col, f"{col}_non_cv", f"{col}_cv")
            ]
        keep += [c for c in wanted if c in frame.columns and c not in keep]
        frame = frame.select(keep)

    grouped = False
    if opts.group_it and frame.height:
        # legacy guard: std needs >= 2 cells per group; disable if any group is
        # short (a single-cell group -- or no group column -- keeps it wide).
        sizes = Counter(lookup.get(lbl, {}).get("group") for lbl in included)
        if sizes and min(sizes.values()) >= 2:
            group_labels = {
                m.get("group"): m.get("group_label")
                for m in lookup.values()
                if m.get("group_label") is not None
            }
            if opts.custom_group_labels:
                group_labels = {**group_labels, **dict(opts.custom_group_labels)}
            frame = ops.group_average(
                frame, opts, keys=_KEYS, group_labels=group_labels or None
            )
            grouped = True

    if frame.height and (opts.replace_inf_with_nan or opts.replace_extremes_with_nan):
        if grouped:
            clean_cols = [c for c in ("mean", "std") if c in frame.columns]
        else:
            clean_cols = ops._numeric_value_columns(frame, _KEYS)
        frame = ops.clean_extremes(
            frame,
            clean_cols,
            replace_inf=opts.replace_inf_with_nan,
            replace_extremes=opts.replace_extremes_with_nan,
            low=opts.low_limit,
            high=opts.high_limit,
        )

    for transform in opts.transforms:
        frame = transform(frame)

    meta = CollectionMeta(
        kind="summary",
        batch_name=batch.journal.name,
        options={
            "columns": list(opts.columns) if opts.columns else None,
            "group_it": opts.group_it,
            "rate": opts.rate,
            "partition_by_cv": opts.partition_by_cv,
            "max_cycle": opts.max_cycle,
        },
        cells_included=included,
    )
    return Collection(
        data=frame,
        kind="summary",
        name=f"{batch.journal.name or 'batch'}_summary",
        meta=meta,
    )
