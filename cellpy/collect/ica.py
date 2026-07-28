"""dQ/dV (ICA) collection.

Per-cell dQ/dV curves via :func:`cellpy.utils.ica.dqdv`, concatenated into one
tidy frame with ``cell`` / ``group`` / ``sub_group`` keys. Mirrors
:func:`cellpy.collect.curves.collect_cycles` -- including the per-cell cycle
isolation that fixes the legacy cross-cell narrowing bug (collectors.py:1691) --
but emits the specced ICA frame: ``cycle, direction, voltage, capacity,
dqdv`` (+ the deprecated ``dq`` duplicate until 2.1).
"""

from __future__ import annotations

from typing import Any

import polars as pl

from cellpy.collect.cells import iter_cells
from cellpy.collect.collection import Collection, CollectionMeta
from cellpy.collect.options import IcaOptions


def _as_polars(frame: Any) -> pl.DataFrame | None:
    if frame is None:
        return None
    if isinstance(frame, pl.DataFrame):
        return frame
    try:
        return pl.from_pandas(frame)
    except (TypeError, ValueError):
        return None


def collect_ica(
    batch: Any, options: IcaOptions | None = None, **overrides
) -> Collection:
    """Collect dQ/dV (incremental capacity) curves per cell into one Collection.

    Cycle selection is derived per cell from the *originally requested* cycles
    every iteration, so a cell missing a cycle never narrows the request for
    the cells after it.
    """
    from cellpy.utils import ica

    opts = options or IcaOptions()
    if overrides:
        opts = opts.replace(**overrides)
    requested = tuple(opts.cycles) if opts.cycles is not None else None

    dqdv_kwargs: dict[str, Any] = {}
    if opts.voltage_resolution is not None:
        dqdv_kwargs["voltage_resolution"] = opts.voltage_resolution

    frames: list[pl.DataFrame] = []
    for item in iter_cells(batch):
        cell = item.cell
        if requested is None:
            cycles = None
        else:
            available = set(cell.get_cycle_numbers())
            cycles = [c for c in requested if c in available]
            if not cycles:
                continue

        curve = _as_polars(ica.dqdv(cell, cycles=cycles, **dqdv_kwargs))
        if curve is None or curve.height == 0:
            continue
        frames.append(
            curve.with_columns(
                pl.lit(item.label).alias("cell"),
                pl.lit(item.group).alias("group"),
                pl.lit(item.sub_group).alias("sub_group"),
            )
        )

    data = pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()
    for transform in opts.transforms:
        data = transform(data)

    meta = CollectionMeta(
        kind="ica",
        batch_name=batch.journal.name,
        options={
            "cycles": list(requested) if requested else None,
            "voltage_resolution": opts.voltage_resolution,
        },
        cells_included=list(batch.cells),
    )
    return Collection(
        data=data,
        kind="ica",
        name=f"{batch.journal.name or 'batch'}_ica",
        meta=meta,
    )
