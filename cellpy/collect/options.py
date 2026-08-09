"""Collection options.

One source of truth per option set: dataclasses shared by the pipeline
functions and the convenience class. This replaces the legacy "elevated
arguments" machinery -- ~20 parameters re-declared per collector subclass,
packed into dicts and merged through three priority layers, with the same
parameter documented in three places (collectors.py:995-1126, :306-316).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable

#: A transform is a pure frame -> frame step applied after collection.
Transform = Callable[["object"], "object"]


@dataclass(frozen=True)
class SummaryOptions:
    """Options for :func:`cellpy.collect.collect_summaries`.

    One source of truth for the whole summary pipeline, replacing the ~30
    keyword arguments of the legacy ``helpers.concat_summaries``. The three
    meaty feature families it carries:

    * **rate filtering** (``rate`` / ``rate_on`` / ``rate_std`` / ...): keep
      only cycles whose ``rate_on`` step ran at the requested C-rate.
    * **group averaging** (``group_it`` / ``average_method`` /
      ``custom_group_labels``): average per journal group, emitting a tidy
      long frame ``(group, cycle_num, variable, mean, std)``.
    * **CV partition** (``partition_by_cv``): split each capacity metric into
      ``*_non_cv`` / ``*_cv`` contributions.
    """

    # --- column selection -------------------------------------------------
    columns: tuple[str, ...] | None = None  # summary columns to keep (+ keys)

    # --- cycle selection --------------------------------------------------
    max_cycle: int | None = None  # drop cycles above this
    remove_last: bool = False  # drop the final cycle (often incomplete)
    only_selected: bool = False  # honour the journal ``selected`` column

    # --- rate filtering ---------------------------------------------------
    rate: float | None = None  # C-rate to keep (numeric, e.g. 0.05 for C/20)
    rate_on: str | tuple[str, ...] | None = None  # step type(s), default charge
    rate_std: float | None = None  # tolerance (default 10% of rate)
    rate_column: str | None = None  # C-rate column (default schema c_rate)
    rate_inverse: bool = False  # keep steps NOT at the rate
    rate_inverted: bool = False  # keep cycles NOT selected by the rate

    # --- CV partition -----------------------------------------------------
    partition_by_cv: bool = False  # add *_non_cv / *_cv columns

    # --- normalization ----------------------------------------------------
    normalize_cycles: bool = False  # expose normalized (equivalent) cycle index

    # --- grouping ---------------------------------------------------------
    group_it: bool = False  # average per group -> long (variable/mean/std)
    average_method: str = "mean"  # "mean" or "median" (column stays "mean")
    custom_group_labels: Mapping | None = None  # group -> display label

    # --- cleanup ----------------------------------------------------------
    replace_inf_with_nan: bool = True  # inf -> null (plot-friendly)
    replace_extremes_with_nan: bool = True  # out-of-range floats -> null
    low_limit: float = -1e6
    high_limit: float = 1e6

    # --- post hooks -------------------------------------------------------
    transforms: tuple[Transform, ...] = ()

    def replace(self, **changes) -> "SummaryOptions":
        return replace(self, **changes)


@dataclass(frozen=True)
class CurveOptions:
    """Options for cycle/capacity-curve collection."""

    cycles: tuple[int, ...] | None = None  # requested cycles (per cell, isolated)
    rate: float | None = None  # rate-based cycle selection
    rate_on: str | None = None
    rate_std: float | None = None
    inverse: bool = False
    # capacity mode/method, forwarded per cell to ``CellpyCell.get_cap`` for
    # parity with the single-cell call. ``None`` keeps ``get_cap``'s defaults
    # (mode="gravimetric", method="back-and-forth").
    mode: str | None = None  # "gravimetric" / "areal" / "absolute"
    method: str | None = None  # "forth-and-forth" / "back-and-forth" / "forth"
    transforms: tuple[Transform, ...] = ()

    def replace(self, **changes) -> "CurveOptions":
        return replace(self, **changes)


@dataclass(frozen=True)
class IcaOptions:
    """Options for dQ/dV (ICA) and dV/dQ (DVA) collection.

    Shared by :func:`cellpy.collect.collect_ica` and
    :func:`cellpy.collect.collect_dva` -- each forwards only the resolution
    knob its own transform actually uses: ``dqdv`` differentiates along
    voltage (needs ``voltage_resolution`` for the q(V) interpolation);
    ``dvdq`` differentiates along capacity (needs ``capacity_resolution`` for
    the V(q) interpolation).
    """

    cycles: tuple[int, ...] | None = None
    voltage_resolution: float | None = None
    capacity_resolution: float | None = None
    transforms: tuple[Transform, ...] = ()

    def replace(self, **changes) -> "IcaOptions":
        return replace(self, **changes)


@dataclass(frozen=True)
class SaveOptions:
    """Where/how a :class:`Collection` is saved (no cwd fallback)."""

    directory: Path | None = None
    formats: tuple[str, ...] = ("parquet", "csv")

    def replace(self, **changes) -> "SaveOptions":
        return replace(self, **changes)
