"""Plotting backends (prepare → spec → render)."""

from __future__ import annotations

from typing import Any

from cellpy.plotting.backends.base import Backend
from cellpy.plotting.backends.mpl import MatplotlibBackend, require_matplotlib
from cellpy.plotting.backends.plotly import (
    PlotlyBackend,
    configure_formation_layout,
    configure_fullcell_standard_domains,
)

__all__ = [
    "Backend",
    "MatplotlibBackend",
    "require_matplotlib",
    "PlotlyBackend",
    "configure_formation_layout",
    "configure_fullcell_standard_domains",
    "get_backend",
]


def get_backend(name: str) -> Any:
    """Return a backend instance for *name* (``plotly`` or ``matplotlib``)."""
    key = (name or "").strip().lower()
    if key == "plotly":
        return PlotlyBackend()
    if key == "matplotlib":
        require_matplotlib("backend='matplotlib'")
        return MatplotlibBackend()
    raise ValueError(
        f"unknown plotting backend {name!r} (known: plotly, matplotlib)"
    )
