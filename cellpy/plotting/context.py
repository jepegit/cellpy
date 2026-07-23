"""Source adapters for prepare → spec → render (#638).

The only code in ``cellpy.plotting`` that should reach into ``CellpyCell`` /
``Batch`` objects. BatchContext arrives with the collectors rebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


def from_source(source: Any) -> CellContext:
    """Adapt *source* to a plotting context.

    Currently only single-cell inputs are supported (#638). Batch / frame
    adapters land with later epic stages.
    """
    if isinstance(source, CellContext):
        return source
    return CellContext(cell=source)
