"""Declarative figure specs for the prepare → spec → render pipeline (#636).

These dataclasses are the contract later Stage-1 issues (#637–#639) will render.
This PR only lands the types; today's builders do not consume them yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class AxisSpec:
    """One axis on a figure panel."""

    label: Optional[str] = None
    range: Optional[tuple[float, float]] = None
    unit_mode: Optional[str] = None


@dataclass(frozen=True)
class PanelSpec:
    """One panel (row) in a multi-panel figure."""

    columns: tuple[str, ...] = ()
    kind: str = "line"
    y_axis: AxisSpec = field(default_factory=AxisSpec)
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FigureSpec:
    """Backend-agnostic description of a figure."""

    panels: tuple[PanelSpec, ...] = ()
    x_axis: AxisSpec = field(default_factory=AxisSpec)
    title: Optional[str] = None
    supports_formation: bool = True
    extras: dict[str, Any] = field(default_factory=dict)
