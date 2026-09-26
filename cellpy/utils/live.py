"""Follow a running test: poll a cell's raw source and refresh it (#781).

The loop is a thin layer over ``CellpyCell.update()`` (#164): each tick asks the
cell to re-check its raw source and append what is new; ``on_update`` runs
after every tick that changed the frames. Nothing here talks to loaders or
cellpy-core directly.

Examples:
    ```python
    from cellpy.utils import live

    def show(c):
        print(c.data.summary.tail(1))

    c = live.poll("running_test.csv", interval=60, on_update=show, max_polls=10,
                  instrument="neware_txt", model="UIO")
    ```

    Stop on your own condition instead of a tick budget:

    ```python
    c = live.poll(c, interval=30, until=lambda cell: cell.get_cycle_numbers()[-1] >= 50)
    ```
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

import cellpy
from cellpy.readers.cellreader import CellpyCell

logging.captureWarnings(True)


class PollStatus:
    """Outcome of one ``poll`` run (also exposed as ``cell.poll_status``).

    Attributes:
        polls: ticks run (each tick is one ``update()`` call).
        updates: ticks where the frames changed.
        stopped_by: ``"complete"``, ``"until"``, ``"max_polls"``,
            ``"timeout"``, ``"interrupted"``, or ``"error"``.
        error: the exception when ``stopped_by == "error"``.
    """

    def __init__(self):
        self.polls = 0
        self.updates = 0
        self.stopped_by: Optional[str] = None
        self.error: Optional[BaseException] = None

    def __repr__(self):
        return f"PollStatus(polls={self.polls}, updates={self.updates}, stopped_by={self.stopped_by!r})"


def poll(
    cell_or_path,
    interval: float = 30.0,
    on_update: Optional[Callable] = None,
    stop_when_complete: bool = True,
    until: Optional[Callable] = None,
    max_polls: Optional[int] = None,
    timeout: Optional[float] = None,
    raise_errors: bool = False,
    sleep: Callable[[float], None] = time.sleep,
    **get_kwargs,
):
    """Refresh a cell from its raw source on an interval until a stop condition.

    Args:
        cell_or_path: a ``CellpyCell`` or a path handed to ``cellpy.get``
            (with ``**get_kwargs``, e.g. ``instrument=``, ``model=``,
            ``mass=``). When a path is given, the initial load counts as the
            first update and ``on_update`` fires for it.
        interval: seconds to wait between ticks.
        on_update: ``on_update(cell)``; called after every tick that changed
            the frames (and after the initial load from a path).
        stop_when_complete: stop when the loader reported the test has ended
            (``cell.source_complete``; only loaders that can tell set it).
        until: ``until(cell) -> bool``; checked after every tick, stops when
            true.
        max_polls: stop after this many ticks (``None`` = no limit).
        timeout: stop after this many seconds (``None`` = no limit).
        raise_errors: re-raise exceptions from ``update``/``on_update``
            instead of stopping the loop with ``stopped_by="error"``.
        sleep: the wait function (injectable for tests / event loops).
        **get_kwargs: forwarded to ``cellpy.get`` when a path is given, and
            (loader-related keys) to ``cell.update`` on every tick.

    Returns:
        The cell, with the run recorded on ``cell.poll_status``.

    ``KeyboardInterrupt`` stops the loop cleanly (``stopped_by="interrupted"``).
    With no stop condition at all the loop runs until interrupted.
    """
    status = PollStatus()
    update_kwargs = {k: v for k, v in get_kwargs.items() if k in _UPDATE_KWARGS}

    if isinstance(cell_or_path, CellpyCell):
        cell = cell_or_path
    else:
        cell = cellpy.get(cell_or_path, **get_kwargs)
        status.updates += 1
        _fire(on_update, cell, status, raise_errors)

    cell.poll_status = status
    started = time.monotonic()

    try:
        while status.stopped_by is None:
            if _should_stop(cell, status, stop_when_complete, until, max_polls, timeout, started):
                break
            sleep(interval)
            status.polls += 1
            try:
                changed = cell.update(**update_kwargs)
            except Exception as exc:  # noqa: BLE001 - reported on the status
                if raise_errors:
                    raise
                logging.error(f"poll: update failed ({exc})")
                status.stopped_by, status.error = "error", exc
                break
            if changed:
                status.updates += 1
                _fire(on_update, cell, status, raise_errors)
    except KeyboardInterrupt:
        status.stopped_by = "interrupted"
    logging.info(f"poll: finished {status}")
    return cell


#: ``cellpy.get`` kwargs that ``update()`` must see too (loader recreation).
_UPDATE_KWARGS = ("model",)


def _fire(on_update, cell, status, raise_errors):
    if on_update is None:
        return
    try:
        on_update(cell)
    except Exception as exc:  # noqa: BLE001 - reported on the status
        if raise_errors:
            raise
        logging.error(f"poll: on_update failed ({exc})")
        status.stopped_by, status.error = "error", exc


def _should_stop(cell, status, stop_when_complete, until, max_polls, timeout, started) -> bool:
    if stop_when_complete and getattr(cell, "source_complete", False):
        status.stopped_by = "complete"
    elif until is not None and until(cell):
        status.stopped_by = "until"
    elif max_polls is not None and status.polls >= max_polls:
        status.stopped_by = "max_polls"
    elif timeout is not None and time.monotonic() - started >= timeout:
        status.stopped_by = "timeout"
    return status.stopped_by is not None
