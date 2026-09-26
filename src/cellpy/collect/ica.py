"""dQ/dV (ICA) collection.

Per-cell dQ/dV curves via `dqdv`, concatenated into one
tidy frame with ``cell`` / ``group`` / ``sub_group`` keys. Mirrors
`collect_cycles` -- including the per-cell cycle
isolation that fixes the legacy cross-cell narrowing bug (collectors.py:1691) --
but emits the specced ICA frame: ``cycle, direction, voltage, capacity, dqdv``.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from cellpy.collect.cells import iter_cells
from cellpy.collect.collection import Collection, CollectionMeta
from cellpy.collect.options import resolve_ica_collection


def _as_polars(frame: Any) -> pl.DataFrame | None:
    if frame is None:
        return None
    if isinstance(frame, pl.DataFrame):
        return frame
    try:
        return pl.from_pandas(frame)
    except (TypeError, ValueError):
        return None


def _collect_derivative(
    batch: Any,
    options: Any,
    overrides: dict[str, Any],
    *,
    kind: str,
    verb: str,
    default_recipe: Any,
    resolution_key: str,
) -> Collection:
    """Per-cell ICA/DVA collection with a shared recipe + cycle isolation."""
    from cellpy.utils import ica as ica_mod

    recipe, requested, transforms = resolve_ica_collection(
        options, overrides, default_recipe=default_recipe
    )
    verb_fn = getattr(ica_mod, verb)

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

        curve = _as_polars(verb_fn(cell, cycles=cycles, options=recipe))
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
    for transform in transforms:
        data = transform(data)

    meta = CollectionMeta(
        kind=kind,
        batch_name=batch.journal.name,
        options={
            "cycles": list(requested) if requested else None,
            resolution_key: getattr(recipe, resolution_key),
        },
        cells_included=list(batch.cells),
    )
    return Collection(
        data=data,
        kind=kind,
        name=f"{batch.journal.name or 'batch'}_{kind}",
        meta=meta,
    )


def collect_ica(batch: Any, options: Any = None, **overrides) -> Collection:
    """Collect dQ/dV (incremental capacity) curves per cell into one Collection.

    ``options`` is a [`cellpy.ica.IcaOptions`][cellpy.ica.IcaOptions] recipe,
    forwarded whole to [`dqdv`][cellpy.ica.dqdv]. ``cycles`` and ``transforms``
    are collect-level knobs (keyword arguments, not recipe fields).

    Cycle selection is derived per cell from the *originally requested* cycles
    every iteration, so a cell missing a cycle never narrows the request for
    the cells after it.

    Example:
        >>> from cellpy import ica
        >>> from cellpy.collect import collect_ica
        >>> opts = ica.IcaOptions(voltage_resolution=0.005, voltage_fwhm=0.015)
        >>> collect_ica(batch, options=opts, cycles=(2, 3))
    """
    from cellpy.ica import IcaOptions as IcaRecipe

    return _collect_derivative(
        batch,
        options,
        overrides,
        kind="ica",
        verb="dqdv",
        default_recipe=IcaRecipe(),
        resolution_key="voltage_resolution",
    )
