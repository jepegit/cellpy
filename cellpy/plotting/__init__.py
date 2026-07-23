"""The single home for cellpy's plotting machinery (#567).

Four generations of plotting code grew up in three modules
(``utils/plotutils.py``, ``utils/collectors.py``,
``utils/batch_tools/batch_plotters.py``), and the same figure could be produced
by paths that shared no layout logic. This package is where the shared parts
live; the plan is `architecture-plan/cellpy2-plotting-redesign-plan.md`.

| module | owns |
|---|---|
| [`figures`][cellpy.plotting.figures] | loading and saving figures |
| [`labels`][cellpy.plotting.labels] | legend and marker post-processing |
| [`theme`][cellpy.plotting.theme] | plotly templates and colour/marker cycles |
| [`cycle_legend`][cellpy.plotting.cycle_legend] | shared legend-vs-colorbar policy for cycle colouring |
| [`spec`][cellpy.plotting.spec] | ``FigureSpec`` / ``PanelSpec`` / ``AxisSpec`` |
| [`registry`][cellpy.plotting.registry] | named ``PlotFamily`` records for ``summary_plot`` |
| [`backends`][cellpy.plotting.backends] | render protocol + plotly formation layout (#637) |
| [`prepare`][cellpy.plotting.prepare] | summary tidy-frame + ``FigureSpec`` (#638) |
| [`context`][cellpy.plotting.context] | ``CellContext`` / ``FrameContext`` (#638 / #657) |
| [`collected`][cellpy.plotting.collected] | multi-cell ``collected_plot`` (``layout=`` / ``kind=``) (#657) |

The old locations re-export from here, so nothing that imported them breaks.
Public ``summary_plot`` still lives in ``plotutils`` but runs
prepare → spec → ``get_backend(...).render`` (#638 / #639).
"""

from __future__ import annotations

from cellpy.plotting.backends import (
    Backend,
    MatplotlibBackend,
    PlotlyBackend,
    get_backend,
)
from cellpy.plotting.collected import collected_plot
from cellpy.plotting.context import CellContext, FrameContext, from_frame, from_source
from cellpy.plotting.cycle_legend import (
    DEFAULT_LEGEND_CYCLE_LIMIT,
    resolve_cycle_legend_mode,
)
from cellpy.plotting.figures import (
    load_figure,
    load_matplotlib_figure,
    load_plotly_figure,
    make_matplotlib_manager,
    save_matplotlib_figure,
)
from cellpy.plotting.labels import (
    legend_replacer,
    quantity_label,
    remove_markers,
    units_quantity_label,
)
from cellpy.plotting.prepare import prepare_summary
from cellpy.plotting.registry import (
    PlotFamily,
    _register_family,
    families,
    get as get_family,
)
from cellpy.plotting.spec import AxisSpec, FigureSpec, PanelSpec
from cellpy.plotting.theme import make_plotly_template

__all__ = [
    "AxisSpec",
    "Backend",
    "CellContext",
    "DEFAULT_LEGEND_CYCLE_LIMIT",
    "FigureSpec",
    "FrameContext",
    "MatplotlibBackend",
    "PanelSpec",
    "PlotFamily",
    "PlotlyBackend",
    "_register_family",
    "collected_plot",
    "families",
    "from_frame",
    "from_source",
    "get_backend",
    "get_family",
    "legend_replacer",
    "load_figure",
    "load_matplotlib_figure",
    "load_plotly_figure",
    "make_matplotlib_manager",
    "make_plotly_template",
    "prepare_summary",
    "quantity_label",
    "remove_markers",
    "resolve_cycle_legend_mode",
    "save_matplotlib_figure",
    "units_quantity_label",
]
