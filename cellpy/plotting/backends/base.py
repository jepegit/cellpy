"""Backend protocol for prepare → spec → render (#637)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cellpy.plotting.spec import FigureSpec


@runtime_checkable
class Backend(Protocol):
    """Render a tidy frame according to a :class:`~cellpy.plotting.spec.FigureSpec`."""

    def render(self, frame: Any, spec: FigureSpec) -> Any:
        """Return a backend-native figure object."""
        ...
