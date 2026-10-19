"""dQ/dV (ICA) collection.

Per-cell dQ/dV curves via `dqdv`, concatenated into one
tidy frame with ``cell`` / ``group`` / ``sub_group`` keys. Mirrors
`collect_cycles` -- including the per-cell cycle
isolation that fixes the legacy cross-cell narrowing bug (collectors.py:1691) --
but emits the specced ICA frame: ``cycle, direction, voltage, capacity, dqdv``.
"""

from __future__ import annotations

import warnings
from typing import Any

import polars as pl

from cellpy.collect.cells import iter_cells
from cellpy.collect.collection import Collection, CollectionMeta
from cellpy.collect.options import resolve_ica_collection

_MAX_LISTED_CELLS = 8
_EMPTY_CYCLE_FRAME = "cycle frame is empty"


def _as_polars(frame: Any) -> pl.DataFrame | None:
    if frame is None:
        return None
    if isinstance(frame, pl.DataFrame):
        return frame
    try:
        return pl.from_pandas(frame)
    except (TypeError, ValueError):
        return None


def _warn_left_out(kind: str, skipped: list[str]) -> None:
    """Name cells that contributed no derivative curve (#1152)."""
    listed = ", ".join(repr(label) for label in skipped[:_MAX_LISTED_CELLS])
    if len(skipped) > _MAX_LISTED_CELLS:
        listed += f", … ({len(skipped)} cells in total)"
    name = "collect_ica" if kind == "ica" else "collect_dva"
    warnings.warn(
        f"{name} left out cells with no cycle curve for this collection: {listed}. "
        "A cell drops out when the requested cycles are absent, when get_cap "
        "returns no rows, or when the derivative frame is empty.",
        UserWarning,
        stacklevel=4,
    )


def _empty_cycle_frame(exc: BaseException) -> bool:
    return isinstance(exc, ValueError) and _EMPTY_CYCLE_FRAME in str(exc)


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
    included: list[str] = []
    skipped: list[str] = []
    for item in iter_cells(batch):
        cell = item.cell
        if requested is None:
            cycles = None
        else:
            available = set(cell.get_cycle_numbers())
            cycles = [c for c in requested if c in available]
            if not cycles:
                skipped.append(item.label)
                continue

        try:
            raw = verb_fn(cell, cycles=cycles, options=recipe)
        except ValueError as exc:
            if not _empty_cycle_frame(exc):
                raise
            skipped.append(item.label)
            continue
        curve = _as_polars(raw)
        if curve is None or curve.height == 0:
            skipped.append(item.label)
            continue
        frames.append(
            curve.with_columns(
                pl.lit(item.label).alias("cell"),
                pl.lit(item.group).alias("group"),
                pl.lit(item.sub_group).alias("sub_group"),
            )
        )
        included.append(item.label)

    if skipped:
        _warn_left_out(kind, skipped)

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
        cells_included=included,
        cells_skipped=skipped,
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

    A cell with no usable curve is left out. The call warns (``UserWarning``)
    and names the cell. ``meta.cells_included`` lists cells that contributed
    rows; ``meta.cells_skipped`` lists the rest. A cell drops out when the
    requested cycles are absent, when ``get_cap`` returns no rows (the
    single-cell ``dqdv`` error ``"cycle frame is empty"``), or when the
    derivative frame is empty. A direct ``dqdv`` call on that cell still
    raises the ``ValueError``.

    Examples:
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
