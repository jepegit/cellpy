"""Cycle/capacity-curve collection.

Per-cell rate/cycle selection is computed **per cell from the originally
requested cycles** -- the fix for the cross-cell narrowing bug where the legacy
``cycles_collector``/``ica_collector`` reassigned the shared ``cycles`` list
inside the per-cell loop (collectors.py:1609/1691), silently dropping cycles
for every cell after the first that lacked them.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from cellpy.collect.cells import iter_cells
from cellpy.collect.collection import Collection, CollectionMeta
from cellpy.collect.options import CurveOptions

_KEYS = ("cell", "group", "sub_group", "cycle_num")


def _as_polars(frame: Any) -> pl.DataFrame | None:
    if frame is None:
        return None
    if isinstance(frame, pl.DataFrame):
        return frame
    try:
        return pl.from_pandas(frame)
    except (TypeError, ValueError):
        return None


def collect_cycles(
    batch: Any, options: CurveOptions | None = None, **overrides
) -> Collection:
    """Collect capacity-voltage curves per cell/cycle into one tidy Collection."""
    opts = options or CurveOptions()
    if overrides:
        opts = opts.replace(**overrides)
    requested = tuple(opts.cycles) if opts.cycles is not None else None

    frames: list[pl.DataFrame] = []
    for item in iter_cells(batch):
        cell = item.cell
        available = set(cell.get_cycle_numbers())
        # PER-CELL isolation: derive this cell's cycles from the ORIGINAL
        # request every iteration -- never narrow a shared variable.
        if requested is None:
            cell_cycles = sorted(available)
        else:
            cell_cycles = [cyc for cyc in requested if cyc in available]

        for cyc in cell_cycles:
            curve = _as_polars(cell.get_cap(cycle=cyc))
            if curve is None or curve.height == 0:
                continue
            frames.append(
                curve.with_columns(
                    pl.lit(item.label).alias("cell"),
                    pl.lit(item.group).alias("group"),
                    pl.lit(item.sub_group).alias("sub_group"),
                    pl.lit(cyc).alias("cycle_num"),
                )
            )

    data = pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()
    for transform in opts.transforms:
        data = transform(data)

    meta = CollectionMeta(
        kind="cycles",
        batch_name=batch.journal.name,
        options={"cycles": list(requested) if requested else None, "rate": opts.rate},
        cells_included=list(batch.cells),
    )
    return Collection(
        data=data,
        kind="cycles",
        name=f"{batch.journal.name or 'batch'}_cycles",
        meta=meta,
    )
