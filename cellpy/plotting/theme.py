"""Plotly templates — one implementation (#567).

``_make_plotly_template`` existed in both ``utils/plotutils.py`` and
``utils/batch_tools/batch_plotters.py``. The bodies were identical; the only
difference was that plotutils' copy checked whether plotly was installed first,
which is the behaviour kept here.

Building a template *registers* it with plotly under ``name``, so the two
copies were also silently competing for the same registry key: whichever
module was imported last won. There is now one definition and one registration.
"""

from __future__ import annotations

import importlib.util
import logging

plotly_available = importlib.util.find_spec("plotly") is not None

#: Look of the default cellpy axis template.
TICK_LABEL_WIDTH = 6
TITLE_FONT_SIZE = 22
TITLE_FONT_FAMILY = "Arial"
AXIS_FONT_SIZE = 16
AXIS_STANDOFF = 15
LINE_COLOR = "rgb(36,36,36)"


def make_plotly_template(name: str = "axis"):
    """Build the cellpy axis template and register it with plotly.

    Args:
        name: the key to register under in ``plotly.io.templates``.

    Returns:
        The template, or ``None`` when plotly is not installed.
    """
    if not plotly_available:
        logging.warning("plotly is not available; no template registered")
        return None

    import plotly.graph_objects as go
    import plotly.io as pio

    template = go.layout.Template(
        layout=dict(
            font_family=TITLE_FONT_FAMILY,
            title=dict(
                font_size=TITLE_FONT_SIZE,
                x=0,
                xref="paper",
            ),
            xaxis=dict(
                linecolor=LINE_COLOR,
                mirror=True,
                showline=True,
                zeroline=False,
                title=dict(
                    standoff=AXIS_STANDOFF,
                    font_size=AXIS_FONT_SIZE,
                ),
            ),
            yaxis=dict(
                linecolor=LINE_COLOR,
                mirror=True,
                showline=True,
                zeroline=False,
                tickformat=f"{TICK_LABEL_WIDTH}",
                title=dict(
                    standoff=AXIS_STANDOFF,
                    font_size=AXIS_FONT_SIZE,
                ),
            ),
        )
    )
    pio.templates[name] = template
    return template


#: The collector template family. Four names, one look — collectors built four
#: separate `go.layout.Template` objects from the same layout dict and
#: registered them under these names.
COLLECTOR_TEMPLATE_NAMES = ("fig_pr_cell", "fig_pr_cycle", "film", "summary")

#: Axis styling shared by the collector templates: a full box, no zero line.
ALL_AXIS_SHOWN = dict(
    xaxis=dict(
        linecolor=LINE_COLOR,
        mirror=True,
        showline=True,
        zeroline=False,
        title={"standoff": AXIS_STANDOFF},
    ),
    yaxis=dict(
        linecolor=LINE_COLOR,
        mirror=True,
        showline=True,
        zeroline=False,
        title={"standoff": AXIS_STANDOFF},
    ),
)


def make_collector_templates(register: bool = True) -> dict | None:
    """Build (and by default register) the collector template family.

    Built lazily on purpose. These used to be four module-level
    ``go.layout.Template(...)`` calls in ``collectors.py``, which made
    ``import cellpy.utils.collectors`` raise ``NameError: name 'go' is not
    defined`` on any install without the ``batch`` extra — the module was
    simply unimportable without plotly.

    Args:
        register: also put them in ``plotly.io.templates``.

    Returns:
        ``{name: template}``, or ``None`` when plotly is not installed.
    """
    if not plotly_available:
        logging.warning("plotly is not available; no collector templates built")
        return None

    import plotly.graph_objects as go
    import plotly.io as pio

    templates = {
        name: go.layout.Template(layout=ALL_AXIS_SHOWN)
        for name in COLLECTOR_TEMPLATE_NAMES
    }
    if register:
        for name, template in templates.items():
            pio.templates[name] = template
    return templates
