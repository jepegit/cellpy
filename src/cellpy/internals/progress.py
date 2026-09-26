"""Process-wide progress emit bus.

Batch UI (tqdm / Jupyter) and loaders share one hook so copy/parse/save can
report without threading a callback through every signature. Threads in the
same process see the same hook; process-pool workers do not (parent updates
the overall bar on cell-done only).
"""

from __future__ import annotations

import threading
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable

_LOCK = threading.Lock()
_HOOK: Callable[["ProgressEvent"], None] | None = None
_CELL_LABEL: ContextVar[str] = ContextVar("cellpy_progress_cell", default="")


@dataclass(frozen=True)
class ProgressEvent:
    """One progress tick.

    ``phase`` is ``journal``, ``search``, ``cell_start``, ``copy``, ``parse``,
    ``save``, ``cell_done``, or ``persist``.
    """

    phase: str
    index: int = 0
    total: int = 0
    label: str = ""
    n: int | None = None
    total_n: int | None = None


ProgressHook = Callable[[ProgressEvent], None]


def set_hook(hook: ProgressHook | None) -> ProgressHook | None:
    """Install ``hook`` (or clear with ``None``). Returns the previous hook."""
    global _HOOK
    with _LOCK:
        previous = _HOOK
        _HOOK = hook
        return previous


def get_hook() -> ProgressHook | None:
    return _HOOK


def set_cell_label(label: str):
    """Bind copy/parse/save ticks to ``label`` for this task (thread-local)."""
    return _CELL_LABEL.set(label)


def reset_cell_label(token) -> None:
    _CELL_LABEL.reset(token)


def emit(
    phase: str,
    *,
    index: int = 0,
    total: int = 0,
    label: str = "",
    n: int | None = None,
    total_n: int | None = None,
) -> None:
    """Notify the current hook, if any. Never raises into the loader."""
    hook = _HOOK
    if hook is None:
        return
    try:
        hook(
            ProgressEvent(
                phase=phase,
                index=index,
                total=total,
                label=label or _CELL_LABEL.get(),
                n=n,
                total_n=total_n,
            )
        )
    except Exception:
        return
