"""The single home for cellpy's plotting machinery (#567).

Four generations of plotting code grew up in three modules
(``utils/plotutils.py``, ``utils/collectors.py``,
``utils/batch_tools/batch_plotters.py``), and the same figure could be produced
by paths that shared no layout logic. This package is where the shared parts
live; the plan is `architecture-plan/cellpy2-plotting-redesign-plan.md`.

**Phase 1 (this)** consolidates the plumbing that was verifiably duplicated:

| module | owns |
|---|---|
| [`figures`][cellpy.plotting.figures] | loading and saving figures |
| [`labels`][cellpy.plotting.labels] | legend and marker post-processing |
| [`theme`][cellpy.plotting.theme] | plotly templates and colour/marker cycles |

The old locations re-export from here, so nothing that imported them breaks.
The drawing code itself — ``summary_plot`` and friends — has not moved yet;
that is Phase 2.
"""

from __future__ import annotations

from cellpy.plotting.figures import (
    load_figure,
    load_matplotlib_figure,
    load_plotly_figure,
    make_matplotlib_manager,
    save_matplotlib_figure,
)
from cellpy.plotting.labels import legend_replacer, remove_markers
from cellpy.plotting.theme import make_plotly_template

__all__ = [
    "legend_replacer",
    "load_figure",
    "load_matplotlib_figure",
    "load_plotly_figure",
    "make_matplotlib_manager",
    "make_plotly_template",
    "remove_markers",
    "save_matplotlib_figure",
]
