"""Collection options (collectors redesign, #705).

One source of truth per option set: dataclasses shared by the pipeline
functions and the convenience class. This replaces the legacy "elevated
arguments" machinery -- ~20 parameters re-declared per collector subclass,
packed into dicts and merged through three priority layers, with the same
parameter documented in three places (collectors.py:995-1126, :306-316).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable

#: A transform is a pure frame -> frame step applied after collection.
Transform = Callable[["object"], "object"]


@dataclass(frozen=True)
class SummaryOptions:
    """Options for :func:`cellpy.collect.collect_summaries`."""

    columns: tuple[str, ...] | None = None  # summary columns to keep (+ keys)
    group_it: bool = False  # group-average with std
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
    transforms: tuple[Transform, ...] = ()

    def replace(self, **changes) -> "CurveOptions":
        return replace(self, **changes)


@dataclass(frozen=True)
class IcaOptions:
    """Options for dQ/dV (ICA) collection."""

    cycles: tuple[int, ...] | None = None
    voltage_resolution: float | None = None
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
