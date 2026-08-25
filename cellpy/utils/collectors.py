"""Deprecated shim: ``cellpy.utils.collectors`` -> `collect`.

The collector subsystem was redesigned and now lives in `collect`
(options / collection / summary / curves / ica / collector). The legacy
``BatchCollector`` family and the ``*_collector`` functions -- built on the
"elevated arguments" machinery (~20 parameters redeclared per subclass and
merged through three priority layers) -- are **removed in 2.1**: this module
keeps the import path alive but the old entry points raise, pointing at their
`collect` replacements.

The shared figure/label/drawing helpers (``load_figure`` & friends,
``legend_replacer``/``remove_markers``, ``collected_plot``/``_select_direction``)
are still re-exported from here -- they are canonical single copies owned by
`plotting`, unrelated to the collector classes.
"""

from __future__ import annotations

from typing import Any, NoReturn

from cellpy._deprecation import warn_once

# Canonical single copies (#567), owned by cellpy.plotting; kept importable
# from here. NOTE: no module-level plotly attribute access -- collectors must
# import without the ``batch`` extra (test_plotting_package guards this).
from cellpy.plotting.collected import _select_direction, collected_plot  # noqa: F401
from cellpy.plotting.figures import (  # noqa: F401
    load_figure,
    load_matplotlib_figure,
    load_plotly_figure,
    make_matplotlib_manager,
    save_matplotlib_figure,
)
from cellpy.plotting.labels import legend_replacer, remove_markers  # noqa: F401

__all__ = [
    # canonical re-exports (still supported)
    "load_figure",
    "load_plotly_figure",
    "load_matplotlib_figure",
    "save_matplotlib_figure",
    "make_matplotlib_manager",
    "legend_replacer",
    "remove_markers",
    "collected_plot",
    # removed collector entry points (raise with a pointer)
    "BatchCollector",
    "BatchSummaryCollector",
    "BatchCyclesCollector",
    "BatchICACollector",
    "summary_collector",
    "cycles_collector",
    "ica_collector",
    "standard_gravimetric_collector",
    "pick_named_cell",
]


def _moved(old: str, new: str) -> NoReturn:
    warn_once(f"cellpy.utils.collectors.{old}", new)
    raise NotImplementedError(
        f"cellpy.utils.collectors.{old} was removed in 2.1. "
        f"Use {new} instead (the collectors redesign, #708)."
    )


# --- removed collector functions -----------------------------------------


def summary_collector(*args: Any, **kwargs: Any) -> NoReturn:
    _moved("summary_collector", "cellpy.collect.collect_summaries")


def cycles_collector(*args: Any, **kwargs: Any) -> NoReturn:
    _moved("cycles_collector", "cellpy.collect.collect_cycles")


def ica_collector(*args: Any, **kwargs: Any) -> NoReturn:
    _moved("ica_collector", "cellpy.collect.collect_ica")


def standard_gravimetric_collector(*args: Any, **kwargs: Any) -> NoReturn:
    _moved("standard_gravimetric_collector", "cellpy.collect.standard_gravimetric")


def pick_named_cell(*args: Any, **kwargs: Any) -> NoReturn:
    _moved("pick_named_cell", "cellpy.collect.iter_cells")


# --- removed collector classes -------------------------------------------


class BatchCollector:
    """Removed in 2.1 -- use `BatchCollector`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _moved("BatchCollector", "cellpy.collect.BatchCollector")


class BatchSummaryCollector(BatchCollector):
    """Removed in 2.1 -- use `summary_collector`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _moved("BatchSummaryCollector", "cellpy.collect.summary_collector")


class BatchCyclesCollector(BatchCollector):
    """Removed in 2.1 -- use `cycles_collector`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _moved("BatchCyclesCollector", "cellpy.collect.cycles_collector")


class BatchICACollector(BatchCollector):
    """Removed in 2.1 -- use `ica_collector`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _moved("BatchICACollector", "cellpy.collect.ica_collector")
