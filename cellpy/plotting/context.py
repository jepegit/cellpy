"""Source adapters for prepare → spec → render (#638 / #657).

The only code in ``cellpy.plotting`` that should reach into ``CellpyCell`` /
``Batch`` objects — or wrap an already-collected tidy frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CellContext:
    """Thin wrapper around a single ``CellpyCell`` for summary prepare/render."""

    cell: Any

    @property
    def cell_name(self) -> str:
        return getattr(self.cell, "cell_name", None) or ""

    @property
    def summary(self) -> Any:
        return self.cell.data.summary

    @property
    def headers_summary(self) -> Any:
        return self.cell.headers_summary

    @property
    def schema(self) -> Any:
        return self.cell.schema

    @property
    def cellpy_units(self) -> Any:
        return self.cell.cellpy_units

    def make_summary(self, **kwargs: Any) -> Any:
        return self.cell.make_summary(**kwargs)


@dataclass
class FrameContext:
    """Already-collected tidy multi-cell frame for collected plotting (#657).

    Collectors own collection; plotting only needs the frame plus light metadata
    (units / journal / family kind).
    """

    frame: Any
    family_kind: str = "cycles"
    units: Any = None
    journal: Any = None


def from_frame(
    frame: Any,
    *,
    family_kind: str = "cycles",
    units: Any = None,
    journal: Any = None,
) -> FrameContext:
    """Wrap a collected tidy frame as a :class:`FrameContext`."""
    if isinstance(frame, FrameContext):
        return frame
    return FrameContext(
        frame=frame, family_kind=family_kind, units=units, journal=journal
    )


def from_source(source: Any) -> CellContext:
    """Adapt *source* to a plotting context.

    Single-cell inputs become :class:`CellContext`. Collected frames should use
    :func:`from_frame` / :func:`collected_plot` instead (#657).
    """
    if isinstance(source, CellContext):
        return source
    if isinstance(source, FrameContext):
        raise TypeError(
            "FrameContext is not a CellContext; use cellpy.plotting.collected_plot "
            "for collected multi-cell frames (#657)"
        )
    return CellContext(cell=source)
