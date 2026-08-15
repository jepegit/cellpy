"""Default batch progress UI (tqdm in the terminal, widget in Jupyter)."""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from cellpy.internals.progress import ProgressEvent, ProgressHook, get_hook, set_hook

def _noop(_event: ProgressEvent) -> None:
    return None


_NOOP: ProgressHook = _noop

_STEPS = {"copy": 1, "parse": 2, "save": 3}


def in_notebook() -> bool:
    """True when running under IPython/Jupyter (including JupyterLab)."""
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    shell = get_ipython()
    if shell is None:
        return False
    name = type(shell).__name__
    return name == "ZMQInteractiveShell" or "google.colab" in name


def should_show_default() -> bool:
    """TTY stderr or a notebook kernel — not a pytest/pipe capture."""
    if in_notebook():
        return True
    try:
        return bool(sys.stderr.isatty())
    except Exception:
        return False


class TqdmBatchProgress:
    """Overall cell bar plus per-cell step bars.

    Serial: one reusable child bar. Threads: one child bar per in-flight
    label (``position=``). ``processes`` should pass ``concurrent=False``;
    workers cannot drive these bars.
    """

    def __init__(
        self,
        n_cells: int,
        *,
        concurrent: bool = False,
        show_children: bool = True,
        disable: bool = False,
    ) -> None:
        from tqdm.auto import tqdm

        self._tqdm = tqdm
        self.concurrent = concurrent
        self.show_children = show_children
        self.disable = disable
        self._lock = threading.Lock()
        self.overall = tqdm(
            total=max(n_cells, 0),
            desc="batch",
            unit="cell",
            position=0,
            disable=disable,
            dynamic_ncols=True,
        )
        self._children: dict[str, Any] = {}
        self._serial: Any | None = None
        self._next_pos = 1
        self._free_pos: list[int] = []
        self.cells_done = 0

    def __call__(self, event: ProgressEvent) -> None:
        with self._lock:
            self._handle(event)

    def set_n_cells(self, n: int) -> None:
        with self._lock:
            self.overall.total = max(n, 0)
            self.overall.refresh()

    def close(self) -> None:
        with self._lock:
            for bar in self._children.values():
                bar.close()
            self._children.clear()
            if self._serial is not None:
                self._serial.close()
                self._serial = None
            self.overall.close()

    def _handle(self, event: ProgressEvent) -> None:
        if event.phase in {"journal", "search", "persist"}:
            self.overall.set_postfix_str(event.phase, refresh=True)
            return
        if not self.show_children:
            if event.phase == "cell_done":
                self.cells_done += 1
                self.overall.update(1)
                self.overall.set_postfix_str(event.label or "", refresh=True)
            return
        if event.phase == "cell_start" and event.label:
            self._child(event.label)
            return
        if event.phase in _STEPS and event.label:
            bar = self._child(event.label)
            if event.phase == "copy" and event.total_n:
                copied = event.n or 0
                bar.set_postfix_str(
                    f"copy {copied / 1e6:.1f}/{event.total_n / 1e6:.1f} MB",
                    refresh=True,
                )
                if copied < event.total_n:
                    return
            self._advance(bar, _STEPS[event.phase])
            bar.set_postfix_str(event.phase, refresh=True)
            return
        if event.phase == "cell_done":
            self.cells_done += 1
            self.overall.update(1)
            self.overall.set_postfix_str(event.label or "", refresh=True)
            self._close_child(event.label)

    def _child(self, label: str):
        if label in self._children:
            return self._children[label]
        if self.concurrent:
            pos = self._free_pos.pop() if self._free_pos else self._next_pos
            if pos == self._next_pos:
                self._next_pos += 1
            bar = self._tqdm(
                total=3,
                desc=label,
                position=pos,
                leave=False,
                disable=self.disable,
                unit="step",
                dynamic_ncols=True,
            )
            bar._cellpy_pos = pos
            self._children[label] = bar
            return bar
        if self._serial is None:
            self._serial = self._tqdm(
                total=3,
                desc=label,
                position=1,
                leave=False,
                disable=self.disable,
                unit="step",
                dynamic_ncols=True,
            )
        else:
            self._serial.reset(total=3)
            self._serial.set_description(label)
        self._children[label] = self._serial
        return self._serial

    def _advance(self, bar, step: int) -> None:
        if bar.n < step:
            bar.update(step - bar.n)

    def _close_child(self, label: str) -> None:
        bar = self._children.pop(label, None)
        if bar is None:
            return
        if self.concurrent:
            pos = getattr(bar, "_cellpy_pos", None)
            bar.close()
            if pos is not None:
                self._free_pos.append(pos)
        elif bar is self._serial:
            self._advance(bar, 3)


def attach_default(
    n_cells: int,
    *,
    concurrent: bool = False,
    show_children: bool = True,
) -> TqdmBatchProgress:
    """Install a tqdm display as the process hook. Caller must ``close()``."""
    display = TqdmBatchProgress(
        n_cells, concurrent=concurrent, show_children=show_children
    )
    set_hook(display)
    return display


@contextmanager
def progress_scope(
    progress: bool | ProgressHook | None,
    n_cells: int,
    executor: str,
) -> Iterator[TqdmBatchProgress | None]:
    """Install the ``progress=`` knob for a load. Restores the previous hook.

    ``None`` — auto (TTY or notebook) unless a hook is already installed.
    ``False`` — off (nested ``update()`` inherits the off state).
    ``True`` — force on. A callable is the raw event hook.
    """
    previous = get_hook()
    display: TqdmBatchProgress | None = None
    try:
        if progress is False:
            set_hook(_NOOP)
        elif callable(progress):
            set_hook(progress)
        elif progress is True or (
            progress is None and previous is None and should_show_default()
        ):
            display = attach_default(
                n_cells,
                concurrent=(executor == "threads"),
                show_children=(executor != "processes"),
            )
        yield display
    finally:
        if display is not None:
            display.close()
        set_hook(previous)
