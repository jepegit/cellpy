# -*- coding: utf-8 -*-
"""
Utilities for helping to plot cellpy-data.
"""

import collections
import dataclasses
import importlib
import itertools
import logging
from multiprocessing import Process
import pickle as pkl
import pprint
from typing import Any, Callable, Optional, Union
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from cellpycore.config import CurveCols
from cellpycore.legacy import mapping

from cellpy._deprecation import warn_once

from cellpy.parameters.internal_settings import (
    get_headers_journal,
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
)
from cellpy.exceptions import UnitsError
from cellpy.units import units_label, with_cellpy_unit
from cellpy.utils import helpers

# Single copies of the plotting plumbing that used to be duplicated across
# plotutils / collectors / batch_plotters (#567). Re-exported here so the
# `from cellpy.utils.plotutils import load_figure` spelling keeps working.
from cellpy.plotting.figures import (  # noqa: F401
    load_figure,
    load_matplotlib_figure,
    load_plotly_figure,
    make_matplotlib_manager,
    save_matplotlib_figure,
)
from cellpy.plotting.labels import legend_replacer as _plotly_legend_replacer
from cellpy.plotting.labels import remove_markers as _plotly_remove_markers
from cellpy.plotting import registry as plot_registry
from cellpy.plotting.theme import make_plotly_template as _make_plotly_template

# get_cap curve frames use native CurveCols names (#540): potential/cycle_num
# replace the legacy voltage/cycle (used by cycles_plot below).
_CCOLS = CurveCols()

plotly_available = importlib.util.find_spec("plotly") is not None
seaborn_available = importlib.util.find_spec("seaborn") is not None

# Refactoring work in progress:
# - homogenize plotting tools (plotutils, batchutils and collectors) to
#   remove the need to change code in many files when changing plotting settings and tools
# - utilize the prms system to set plotting settings
# - make standardized plot templates and looks

# including this to mimic the behaviour of collectors:
supported_backends = []
if plotly_available:
    supported_backends.append("plotly")
if seaborn_available:
    supported_backends.append("seaborn")

# logger = logging.getLogger(__name__)
logging.captureWarnings(True)

# from collectors - template:

PLOTLY_BASE_TEMPLATE = "plotly"
IMAGE_TO_FILE_TIMEOUT = 30


def notebook_docstring_printer(func, default_show_docstring=False):
    """
    Decorator that prints the function's docstring when called from a notebook environment.

    This decorator checks if the function is being called from a Jupyter notebook
    or IPython environment and prints the function's docstring if it is.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """

    def wrapper(*args, **kwargs):
        # Check if we're in a notebook environment
        show_docstring = kwargs.pop("show_docstring", default_show_docstring)
        if show_docstring:
            try:
                # Check for IPython/Jupyter environment
                import IPython

                ipython = IPython.get_ipython()
                if ipython is not None and hasattr(ipython, "kernel"):
                    # We're in a notebook environment
                    if func.__doc__:
                        print(f"{func.__name__} docstring:")
                        print("-" * (len(func.__name__) + 12))
                        print(func.__doc__)
                        print("-" * (len(func.__name__) + 12))
                    else:
                        print(f"No docstring found for {func.__name__}")
            except (ImportError, AttributeError):
                # Not in a notebook environment, continue silently
                pass

        # Call the original function
        return func(*args, **kwargs)

    # Preserve the original function's metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__

    return wrapper


# from collectors - tools for loading and saving plots:










def _image_exporter_plotly(figure, filename, timeout=IMAGE_TO_FILE_TIMEOUT, **kwargs):
    p = Process(
        target=figure.write_image,
        args=(filename,),
        name="save_plotly_image_to_file",
        kwargs=kwargs,
    )
    p.start()
    p.join(timeout=timeout)
    p.terminate()
    if p.exitcode is None:
        print(f"Oops, {p} timeouts! Could not save {filename}")
    if p.exitcode == 0:
        print(f" - saved image file: {filename}")


@notebook_docstring_printer
def save_image_files(
    figure: Any,
    name: str = "my_figure",
    scale: float = 3.0,
    dpi: int = 300,
    backend: str = "plotly",
    formats: Optional[list] = None,
):
    """Save to image files (png, svg, json/pickle).

    Notes:
        This method requires ``kaleido`` for the plotly backend.

    Notes:
        Exporting to json is only applicable for the plotly backend.

    Args:
        figure (fig-object): The figure to save.
        name (pathlib.Path or str): The path of the file (without extension).
        scale (float): The scale of the image.
        dpi (int): The dpi of the image.
        backend (str): The backend to use (plotly or seaborn/matplotlib).
        formats (list): The formats to save (default: ["png", "svg", "json", "pickle"]).

    """
    filename = Path(name)
    filename_png = filename.with_suffix(".png")
    filename_svg = filename.with_suffix(".svg")
    filename_json = filename.with_suffix(".json")
    filename_pickle = filename.with_suffix(".pickle")

    if formats is None:
        formats = ["png", "svg", "json", "pickle"]

    if backend == "plotly":
        if "png" in formats:
            _image_exporter_plotly(figure, filename_png, scale=scale)
        if "svg" in formats:
            _image_exporter_plotly(figure, filename_svg)
        if "json" in formats:
            figure.write_json(filename_json)
            print(f" - saved plotly json file: {filename_json}")

    elif backend in ["seaborn", "matplotlib"]:
        if "png" in formats:
            figure.savefig(filename_png, dpi=dpi)
            print(f" - saved png file: {filename_png}")
        if "svg" in formats:
            figure.savefig(filename_svg)
            print(f" - saved svg file: {filename_svg}")
        if "pickle" in formats:
            save_matplotlib_figure(figure, filename_pickle)
            print(f" - pickled to file: {filename_pickle}")

    else:
        print(f"TODO: implement saving {filename_png}")
        print(f"TODO: implement saving {filename_svg}")
        print(f"TODO: implement saving {filename_json}")




# from batch_plotters:





# original:
SYMBOL_DICT = {
    "all": [
        "s",
        "o",
        "v",
        "^",
        "<",
        ">",
        "D",
        "p",
        "*",
        "1",
        "2",
        ".",
        ",",
        "3",
        "4",
        "8",
        "p",
        "d",
        "h",
        "H",
        "+",
        "x",
        "X",
        "|",
        "_",
    ],
    "simple": ["s", "o", "v", "^", "<", ">", "*", "d"],
}

COLOR_DICT = {
    "classic": ["b", "g", "r", "c", "m", "y", "k"],
    "grayscale": ["0.00", "0.40", "0.60", "0.70"],
    "bmh": [
        "#348ABD",
        "#A60628",
        "#7A68A6",
        "#467821",
        "#D55E00",
        "#CC79A7",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
    ],
    "dark_background": [
        "#8dd3c7",
        "#feffb3",
        "#bfbbd9",
        "#fa8174",
        "#81b1d2",
        "#fdb462",
        "#b3de69",
        "#bc82bd",
        "#ccebc4",
        "#ffed6f",
    ],
    "ggplot": [
        "#E24A33",
        "#348ABD",
        "#988ED5",
        "#777777",
        "#FBC15E",
        "#8EBA42",
        "#FFB5B8",
    ],
    "fivethirtyeight": ["#30a2da", "#fc4f30", "#e5ae38", "#6d904f", "#8b8b8b"],
    "seaborn-colorblind": [
        "#0072B2",
        "#009E73",
        "#D55E00",
        "#CC79A7",
        "#F0E442",
        "#56B4E9",
    ],
    "seaborn-deep": ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD"],
    "seaborn-bright": [
        "#003FFF",
        "#03ED3A",
        "#E8000B",
        "#8A2BE2",
        "#FFC400",
        "#00D7FF",
    ],
    "seaborn-muted": ["#4878CF", "#6ACC65", "#D65F5F", "#B47CC7", "#C4AD66", "#77BEDB"],
    "seaborn-pastel": [
        "#92C6FF",
        "#97F0AA",
        "#FF9F9A",
        "#D0BBFF",
        "#FFFEA3",
        "#B0E0E6",
    ],
    "seaborn-dark-palette": [
        "#001C7F",
        "#017517",
        "#8C0900",
        "#7600A1",
        "#B8860B",
        "#006374",
    ],
}

PLOTLY_BLANK_LABEL = {
    "font": {},
    "showarrow": False,
    "text": "",
    "x": 1.1,
    "xanchor": "center",
    "xref": "paper",
    "y": 1.0,
    "yanchor": "bottom",
    "yref": "paper",
}


def _plotly_label_dict(text, x, y):
    d = PLOTLY_BLANK_LABEL.copy()
    d["text"] = text
    d["x"] = x
    d["y"] = y
    return d


#: ``normalized_cycle_index`` is spelled the same in both dialects (asserted in
#: tests/test_plotutils_headers.py), so comparing against it needs no schema.
#: The other three module-level header singletons that used to live here were
#: removed in #567: they answered with *legacy* names regardless of the cell,
#: which silently broke every raw-frame lookup after the native-headers flip.
#: Use ``_LiveHeaders(cell, frame)`` instead.
_NORMALIZED_CYCLE_INDEX = "normalized_cycle_index"
_hdr_journal = get_headers_journal()


def set_plotly_template(template_name=None, **kwargs):
    """Set the default plotly template."""
    if not plotly_available:
        return None
    import plotly.io as pio

    try:
        if template_name is None:
            name = create_plotly_default_template(**kwargs)
            pio.templates.default = f"{PLOTLY_BASE_TEMPLATE}+{name}"
        else:
            pio.templates.default = template_name
    except Exception as e:
        logging.debug(f"Could not set plotly template: {e}")
        pio.templates.default = PLOTLY_BASE_TEMPLATE


def create_plotly_default_template(
    name="all_axis",
    font_color="#455A64",
    marker_edge_on=False,
    marker_size=12,
    marker_edge_color="white",
    marker_width=None,
    opacity=0.8,
):
    # ValueError: Invalid property specified for object of type plotly.graph_objs.layout.XAxis: 'titlefont'
    if not plotly_available:
        return None
    import plotly.graph_objects as go
    import plotly.io as pio

    axis_color = "rgb(36,36,36)"
    grid_color = "white"
    axis_font = "Arial Black"
    axis_font_size = 16
    # axis_standoff = 15
    axis_standoff = None
    tick_label_width = 6

    title_font_size = 22
    title_font_family = "Arial Black, Helvetica, Sans-serif"
    title_font_color = font_color

    marker = dict(
        size=marker_size,
    )
    line = dict()

    if marker_edge_on:
        if marker_width is None:
            if marker_size is not None:
                marker_width = marker_size / 6
            else:
                marker_width = 0.5

        marker["line"] = dict(
            width=marker_width,
            color=marker_edge_color,
        )
    axis = dict(
        linecolor=axis_color,
        mirror=True,
        showline=True,
        gridcolor=grid_color,
        zeroline=False,
        tickformat=f"{tick_label_width}",
        title_font_family=axis_font,
        title=dict(
            standoff=axis_standoff,
            font_size=axis_font_size,
            font_color=font_color,
        ),
    )
    title = dict(
        font_family=title_font_family,
        font_size=title_font_size,
        font_color=title_font_color,
        x=0,
        xref="paper",
    )
    data = dict(
        scatter=[go.Scatter(marker=marker, line=line, opacity=opacity)],
    )
    pio.templates[name] = go.layout.Template(
        layout=dict(title=title, xaxis=axis, yaxis=axis), data=data
    )
    return name


def create_colormarkerlist_for_journal(
    journal, symbol_label="all", color_style_label="seaborn-colorblind"
):
    """Fetch lists with color names and marker types of correct length for a journal.

    Args:
        journal: cellpy journal
        symbol_label: sub-set of markers to use
        color_style_label: cmap to use for colors

    Returns:
        colors (list), markers (list)
    """
    logging.debug("symbol_label: " + symbol_label)
    logging.debug("color_style_label: " + color_style_label)
    groups = journal.pages[_hdr_journal.group].unique()
    sub_groups = journal.pages[_hdr_journal.subgroup].unique()
    return create_colormarkerlist(groups, sub_groups, symbol_label, color_style_label)


def create_colormarkerlist(
    groups, sub_groups, symbol_label="all", color_style_label="seaborn-colorblind"
):
    """Fetch lists with color names and marker types of correct length.

    Args:
        groups: list of group numbers (used to generate the list of colors)
        sub_groups: list of sub-group numbers (used to generate the list of markers).
        symbol_label: sub-set of markers to use
        color_style_label: cmap to use for colors

    Returns:
        colors (list), markers (list)
    """
    symbol_list = SYMBOL_DICT[symbol_label]
    color_list = COLOR_DICT[color_style_label]

    # checking that we have enough colors and symbols (if not, then use cycler (e.g. reset))
    color_cycler = itertools.cycle(color_list)
    symbol_cycler = itertools.cycle(symbol_list)
    _color_list = []
    _symbol_list = []
    for i in groups:
        _color_list.append(next(color_cycler))
    for i in sub_groups:
        _symbol_list.append(next(symbol_cycler))
    return _color_list, _symbol_list


def _get_capacity_unit(c, mode="gravimetric"):
    # Callers derive the mode from a y-spec suffix (``y.split("_")[-1]``), so
    # it is routinely something that is not a mode at all; keep returning the
    # "-" placeholder for those rather than letting units_label raise.
    try:
        return units_label("charge", mode, units=c.cellpy_units)
    except UnitsError:
        return "-"


def _resolve_summary_column(c, name):
    """Accept the legacy spelling of a summary column and return the live one.

    The native-headers flip renamed summary columns, so ``summary_plot(c,
    x="cycle_index")`` — the spelling in this module's own docstrings and in
    every 1.x script — stopped indexing the frame and raised ``KeyError`` deep
    inside a ``melt``. The default path was unaffected (it reads the name off
    the schema), which is why nothing caught it.

    Resolution is checked against the *frame*, so this works on both runtimes:
    on the legacy runtime the frame still carries ``cycle_index`` and the name
    is returned untouched.
    """
    if not isinstance(name, str):
        return name

    summary = getattr(getattr(c, "data", None), "summary", None)
    columns = set(summary.columns) if summary is not None else set()

    if not columns or name in columns:
        return name

    native = mapping.legacy_to_native_summary().get(name)
    if native is None or native not in columns:
        # Not a legacy spelling we know: leave it alone and let the caller
        # raise its own error, which will name the column the user asked for.
        return name

    warn_once(
        f"legacy summary column name {name!r} in a plot argument",
        f"the native name {native!r} (see c.schema.summary)",
        removal="2.1",
    )
    return native


def _resolve_summary_columns(c, names):
    """``_resolve_summary_column`` over a list, preserving order and Nones."""
    if not names:
        return names
    return [_resolve_summary_column(c, name) for name in names]


#: cellpy-core mapping key per frame, for ``_LiveHeaders``.
_MAPPING_FRAME = {"raw": "raw", "steps": "step", "summary": "cycle"}


class _LiveHeaders:
    """Column names for *this cell's* frames, keyed by the 1.x attribute names.

    Replaces the module-level ``_hdr_raw = get_headers_normal()`` /
    ``_hdr_steps`` / ``_hdr_summary`` singletons. Those were built once at
    import time and always answered with the **legacy** names, so after the
    native-headers flip every lookup through them produced a key the frame no
    longer had. That is why ``raw_plot`` and ``cycle_info_plot`` raised
    ``KeyError: 'voltage'`` on any cellpy 2 cell — a module-level binding that
    could not see the runtime, which is the same trap that bit the schema
    migration in #558.

    Resolution goes through the cell's own schema, so this is correct on both
    runtimes: on the legacy runtime ``schema.raw.potential`` still answers
    ``"voltage"``.

    Both spellings the old singletons supported are kept, because call sites
    use both: ``hdr["voltage_txt"]`` and ``hdr.voltage_txt``.
    """

    __slots__ = ("_schema", "_frame", "_attrs")

    def __init__(self, c, frame: str):
        self._frame = frame
        self._schema = getattr(c.schema, frame)
        self._attrs = mapping.LEGACY_ATTR_TO_SCHEMA[_MAPPING_FRAME[frame]]

    def _resolve(self, legacy_attr: str) -> str:
        native = self._attrs.get(legacy_attr)
        if native is None:
            # Either unknown, or a legacy-only column with no native
            # counterpart. Fall back to the schema's own attribute so native
            # spellings work too, and let it raise if that fails as well.
            try:
                return getattr(self._schema, legacy_attr)
            except AttributeError:
                raise KeyError(
                    f"no {self._frame} column named {legacy_attr!r} on this cell"
                ) from None
        return getattr(self._schema, native)

    def base(self, legacy_attr: str) -> str:
        """The native *stem* of a step-table statistic family.

        Step-table columns are ``<stem>_<statistic>`` (``potential_delta``,
        ``current_min``). The schema exposes the composed columns, not the
        stem, so this reads the stem straight off the mapping — and falls back
        to the legacy spelling on the legacy runtime, where the stem is what
        the frame already uses.
        """
        native = self._attrs.get(legacy_attr)
        if native is None:
            return legacy_attr
        # On the legacy runtime the schema resolves the native name back to the
        # legacy one; when it cannot (a stem is not a column) keep the native
        # stem, which is what a native frame is built from.
        try:
            return getattr(self._schema, native)
        except AttributeError:
            return native

    def stat(self, legacy_attr: str, statistic: str) -> str:
        """``stat("voltage", "delta")`` -> ``"potential_delta"`` (native)."""
        return f"{self.base(legacy_attr)}_{statistic}"

    def __getitem__(self, legacy_attr: str) -> str:
        return self._resolve(legacy_attr)

    def __getattr__(self, legacy_attr: str) -> str:
        return self._resolve(legacy_attr)


# Per-row y-axis labels for predefined ``y`` sets that route a different
# quantity onto row 0 (efficiency plots, *_with_rate plots). The "_plotly"
# and "_seaborn" variants differ only in the line-break character (HTML
# ``<br>`` vs ``\n``) so each builder gets a string it can render natively.
def _plotly_top_row_label(y: str) -> Optional[str]:
    if y.endswith("_efficiency"):
        return "Coulombic Efficiency"
    if y.endswith("_with_rate"):
        return "C-rate (1/h)"
    return None


def _seaborn_top_row_label(y: str) -> Optional[str]:
    if y.endswith("_efficiency"):
        return "Coulombic\nEfficiency (%)"
    if y.endswith("_with_rate"):
        return "C-rate\n(1/h)"
    return None


def _has_special_top_row(y: str) -> bool:
    """True for y-sets whose row 0 holds a different quantity than the
    other rows (so plotters should disable shared y-axis and pick a
    per-row y-label)."""
    return y.endswith("_efficiency") or y.endswith("_with_rate")


# TODO: consistent parameter names (e.g. y_range vs ylim) between summary_plot, plot_cycles, raw_plot, cycle_info_plot and batchutils
# TODO: consistent function names (raw_plot vs plot_raw etc)


@dataclasses.dataclass
class SummaryPlotConfig:
    """Configuration dataclass for summary_plot parameters.

    Encapsulates all parameters for summary_plot to improve maintainability
    and enable easier refactoring.
    """

    # Core parameters
    x: Optional[str] = None
    y: str = "capacities_gravimetric_coulombic_efficiency"

    # Plot dimensions
    height: Optional[int] = None
    width: int = 900

    # Plot styling
    markers: bool = True
    title: Optional[str] = None

    # Axis ranges
    x_range: Optional[list] = None
    y_range: Optional[list] = None
    ce_range: Optional[list] = None
    norm_range: Optional[list] = None
    cv_share_range: Optional[list] = None

    # Plot layout
    split: bool = True
    hover_columns: Optional[list] = None
    auto_convert_legend_labels: bool = True
    backend: Optional[str] = None
    interactive: Optional[bool] = None
    share_y: bool = False
    rangeslider: bool = False

    # Return options
    return_data: bool = False
    verbose: bool = False

    # Backend-specific
    plotly_template: Optional[str] = None
    seaborn_palette: str = "deep"
    seaborn_style: str = "dark"

    # Formation cycles
    formation_cycles: int = 3
    show_formation: bool = True
    show_legend: bool = True
    x_axis_domain_formation_fraction: float = 0.2
    column_separator: float = 0.01

    # Fullcell standard specific
    reset_losses: bool = True
    link_capacity_scales: bool = False
    fullcell_standard_normalization_type: str = "max"
    fullcell_standard_normalization_factor: Optional[float] = None
    fullcell_standard_normalization_scaler: float = 1.0
    fullcell_standard_normalization_cycle_numbers: Optional[list[int]] = None

    # Seaborn hooks
    seaborn_line_hooks: Optional[list[tuple[str, list, dict]]] = None

    # Summary filtering / rate handling (issue #363)
    filters: Optional[dict] = None
    nominal_capacity: Optional[float] = None
    rate_filter_columns: Optional[Union[str, tuple, list]] = None

    # Additional kwargs (stored as dict)
    additional_kwargs: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        # Mirror the legacy normalisation: a non-positive ``formation_cycles``
        # (including ``False`` / ``0`` / ``None``) means there is no formation
        # block to draw, so ``show_formation`` must be False regardless of
        # how the caller set it. Without this, ``_mark_formation_cycles``
        # returns the ``slice(None, None)`` sentinel while ``show_formation``
        # stays True, and formation layout then evaluates ``~slice(...)``
        # which raises ``TypeError``. See issue #366.
        if self.formation_cycles is None:
            self.formation_cycles = 0
        self.formation_cycles = int(self.formation_cycles)
        if self.formation_cycles < 1:
            self.show_formation = False

    def __str__(self) -> str:
        variables = vars(self)
        outputs = ["SummaryPlotConfig:"]
        outputs.extend([f"{k}: {pprint.pformat(v)}" for k, v in variables.items()])
        return "\n".join(outputs)

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_kwargs(cls, **kwargs) -> "SummaryPlotConfig":
        """Create SummaryPlotConfig from keyword arguments.

        Extracts known parameters and stores remaining kwargs in additional_kwargs.
        """
        # Get known parameter names from dataclass fields (excluding additional_kwargs)
        known_params = {
            f.name for f in dataclasses.fields(cls) if f.name != "additional_kwargs"
        }

        # Separate known params from additional kwargs
        config_params = {k: v for k, v in kwargs.items() if k in known_params}
        additional_kwargs = {k: v for k, v in kwargs.items() if k not in known_params}

        # Create config with known params
        config_params["additional_kwargs"] = additional_kwargs
        return cls(**config_params)

    def to_kwargs(self) -> dict:
        """Convert config back to kwargs dict for passing to legacy function."""
        kwargs = dataclasses.asdict(self)
        # Extract additional_kwargs and merge them
        additional = kwargs.pop("additional_kwargs", {})
        # Remove None values to match legacy function behavior
        kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None
            or k
            in [
                "x",
                "height",
                "title",
                "plotly_template",
                "fullcell_standard_normalization_factor",
            ]
        }
        kwargs.update(additional)
        return kwargs


class SummaryPlotInfo:
    x_cols: Optional[tuple] = None
    y_cols: Optional[dict] = None
    x_trans: Optional[dict] = None
    y_trans: Optional[dict] = None
    x_axis_labels: Optional[dict] = None
    y_axis_label: Optional[dict] = None

    def __init__(self, c: Any):
        """Initialize SummaryPlotInfo.

        This class contains information about the summary plot.
        It is used to store the information about the columns and labels.

        Args:
            c: cellpy object
        """
        self._create_col_info(c)
        self._create_label_dict(c)

    def __str__(self) -> str:
        variables = vars(self)
        outputs = ["SummaryPlotInfo:"]
        outputs.extend([f"{k}: {pprint.pformat(v)}" for k, v in variables.items()])
        return "\n".join(outputs)

    def __repr__(self) -> str:
        return self.__str__()

    def _create_label_dict(self, c: Any) -> tuple[dict, dict]:
        """Create label dictionary for summary plots.

        Args:
            c: cellpy object

        Returns:
            x_axis_labels (dict), y_axis_label (dict)

        """

        hdr = c.headers_summary
        x_axis_labels = {
            hdr.cycle_index: "Cycle Number",
            hdr.data_point: "Point",
            hdr.test_time: with_cellpy_unit("Test Time", "time", units=c.cellpy_units),
            hdr.datetime: "Date",
            hdr.normalized_cycle_index: "Equivalent Full Cycle",  # hdr.normalized_cycle_index: "Normalized Cycle Number",
        }

        _units = c.cellpy_units
        _cap_gravimetric_label = with_cellpy_unit(
            "Capacity", "charge", "gravimetric", units=_units
        )
        _cap_areal_label = with_cellpy_unit("Capacity", "charge", "areal", units=_units)
        _cap_absolute_label = with_cellpy_unit("Capacity", "charge", units=_units)
        # the raw frame's own units, not the session's
        _cap_label = with_cellpy_unit("Capacity", "charge", units=c.data.raw_units)

        y_axis_label = {
            "voltages": with_cellpy_unit("Voltage", "voltage", units=_units),
            "capacities_gravimetric": _cap_gravimetric_label,
            "capacities_areal": _cap_areal_label,
            "capacities_absolute": _cap_absolute_label,
            "capacities": _cap_label,
            "capacities_gravimetric_split_constant_voltage": _cap_gravimetric_label,
            "capacities_areal_split_constant_voltage": _cap_areal_label,
            "capacities_absolute_split_constant_voltage": _cap_absolute_label,
            "capacities_gravimetric_coulombic_efficiency": _cap_gravimetric_label,
            "capacities_areal_coulombic_efficiency": _cap_areal_label,
            "capacities_absolute_coulombic_efficiency": _cap_absolute_label,
            "capacities_gravimetric_with_rate": _cap_gravimetric_label,
            "capacities_areal_with_rate": _cap_areal_label,
            "capacities_absolute_with_rate": _cap_absolute_label,
            "fullcell_standard_gravimetric": _cap_gravimetric_label,
            "fullcell_standard_areal": _cap_areal_label,
            "fullcell_standard_absolute": _cap_absolute_label,
        }

        self.x_axis_labels = x_axis_labels
        self.y_axis_label = y_axis_label

    @staticmethod
    def normalize_col(
        x: np.ndarray,
        normalization_factor: Optional[float] = None,
        normalization_type: str = "max",
        normalization_scaler: float = 1.0,
        normalization_indexes: list[int] = [1],
    ) -> np.ndarray:
        """Normalize a column.

        Args:
            x: column to normalize
            normalization_factor: normalization factor
            normalization_type: normalization type
            normalization_scaler: normalization scaler
            normalization_indexes: indexes to use for normalization

        Normalization types:
            - divide: divide by normalization factor and then multiply by normalization scaler
            - shift-divide: shift by normalization factor and then
                divide by normalization factor and then multiply by normalization scaler
            - multiply: multiply by normalization factor and normalization scaler
            - area: divide by area (integrated using trapezoid rule) and then multiply by normalization scaler
            - max: divide by maximum value and then multiply by normalization scaler
            - on-max: divide by maximum value over normalization factor and then multiply by normalization scaler
            - on-cycles: divide by mean value of the cycles in normalization_indexes and then multiply by normalization scaler
            - false: no normalization is done

        Returns:
            normalized column
        """
        # These normalization types do NOT require a normalization factor:
        if normalization_type == "area":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                area = np.trapzoid(x, dx=1)
            return (x / area) * normalization_scaler

        elif normalization_type == "max":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                x_max = x.max()
            return (x / x_max) * normalization_scaler

        elif normalization_type == "on-cycles":
            x_on_cycles = []
            for cycle in normalization_indexes:
                try:
                    x_on_cycles.append(x[cycle])
                except KeyError:
                    logging.warning(f"Cycle number {cycle} not found in data")
            if len(x_on_cycles) == 0:
                raise ValueError(
                    f"No cycle numbers found in data: {normalization_indexes}"
                )
            x_on_cycles_mean = np.mean(x_on_cycles)
            return (x / x_on_cycles_mean) * normalization_scaler

        elif normalization_type == "false":
            return x

        # These normalization types require a normalization factor:
        if normalization_factor is None:
            raise ValueError(
                f"Normalization factor is required for this normalization type: {normalization_type}"
            )

        elif normalization_type == "divide":
            return (x / normalization_factor) * normalization_scaler

        elif normalization_type == "shift-divide":
            return (
                (normalization_factor - x) / normalization_factor
            ) * normalization_scaler

        elif normalization_type == "multiply":
            return (x * normalization_factor) * normalization_scaler

        elif normalization_type == "on-max":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                x_max = x.max()
            return (x / x_max / normalization_factor) * normalization_scaler

        else:
            raise ValueError(f"Invalid normalization type: {normalization_type}")

    def _create_col_info(self, c: Any) -> tuple[tuple, dict, dict, dict]:
        """Create column information for summary plots.

        Thin adapter over :mod:`cellpy.plotting.registry` (#636). Column-set
        selection for named ``y`` values lives in ``PlotFamily`` records; this
        method only materialises them against ``c.headers_summary``. Keep in
        sync with :meth:`_create_label_dict`.

        Args:
            c: cellpy object

        Returns:
            x_columns (tuple), y_cols (dict), x_transformations (dict), y_transformations (dict)

        """

        hdr = c.headers_summary
        x_columns = (
            [
                hdr.cycle_index,
                hdr.data_point,
                hdr.test_time,
                hdr.datetime,
                hdr.normalized_cycle_index,
            ],
        )
        y_cols: dict[str, list[str]] = {}
        y_transformations: dict[str, dict] = {}
        for family in plot_registry.iter_families():
            y_cols[family.name] = family.columns(hdr)
            transforms = family.transforms(hdr, self.normalize_col)
            if transforms:
                y_transformations[family.name] = transforms

        self.x_cols = x_columns
        self.y_cols = y_cols
        self.x_trans = dict()
        self.y_trans = y_transformations



def summary_plot_legacy(
    c,
    x: Optional[str] = None,
    y: str = "capacities_gravimetric_coulombic_efficiency",
    height: Optional[int] = None,
    width: int = 900,
    markers: bool = True,
    title: Optional[str] = None,
    x_range: Optional[list] = None,
    y_range: Optional[list] = None,
    ce_range: Optional[list] = None,
    norm_range: Optional[list] = None,
    cv_share_range: Optional[list] = None,
    split: bool = True,
    auto_convert_legend_labels: bool = True,
    interactive: bool = True,
    share_y: bool = False,
    rangeslider: bool = False,
    return_data: bool = False,
    verbose: bool = False,
    plotly_template: Optional[str] = None,
    seaborn_palette: str = "deep",
    seaborn_style: str = "dark",
    formation_cycles: int = 3,
    show_formation: bool = True,
    show_legend: bool = True,
    x_axis_domain_formation_fraction: float = 0.2,
    column_separator: float = 0.01,
    reset_losses: bool = True,
    link_capacity_scales: bool = False,
    fullcell_standard_normalization_type: str = "on-max",
    fullcell_standard_normalization_factor: Optional[float] = None,
    fullcell_standard_normalization_scaler: float = 1.0,
    seaborn_line_hooks: Optional[list[tuple[str, list, dict]]] = None,
    **kwargs,
) -> Any:
    """Deprecated. Use [`summary_plot`][cellpy.utils.plotutils.summary_plot].

    The 1 400-line implementation that used to live here was **broken, not
    merely redundant**: its first statement unpacked the return value of
    ``SummaryPlotInfo._create_col_info``, which stores its results as
    attributes and returns ``None`` — so every call raised ``TypeError``
    regardless of the cell or the runtime (#567). Nothing in the repo called
    it, and nothing outside it could have called it successfully either.

    Delegates to ``summary_plot``, which draws the same figures through the
    builder pipeline. Removal in 2.1.
    """
    warn_once(
        "plotutils.summary_plot_legacy",
        "cellpy.utils.plotutils.summary_plot (same figures, same options)",
        removal="2.1",
    )
    return summary_plot(
        c,
        x=x,
        y=y,
        height=height,
        width=width,
        markers=markers,
        title=title,
        x_range=x_range,
        y_range=y_range,
        ce_range=ce_range,
        norm_range=norm_range,
        cv_share_range=cv_share_range,
        split=split,
        auto_convert_legend_labels=auto_convert_legend_labels,
        interactive=interactive,
        share_y=share_y,
        rangeslider=rangeslider,
        return_data=return_data,
        verbose=verbose,
        plotly_template=plotly_template,
        seaborn_palette=seaborn_palette,
        seaborn_style=seaborn_style,
        formation_cycles=formation_cycles,
        show_formation=show_formation,
        show_legend=show_legend,
        x_axis_domain_formation_fraction=x_axis_domain_formation_fraction,
        column_separator=column_separator,
        reset_losses=reset_losses,
        link_capacity_scales=link_capacity_scales,
        fullcell_standard_normalization_type=fullcell_standard_normalization_type,
        fullcell_standard_normalization_factor=fullcell_standard_normalization_factor,
        fullcell_standard_normalization_scaler=fullcell_standard_normalization_scaler,
        seaborn_line_hooks=seaborn_line_hooks,
        **kwargs,
    )


@notebook_docstring_printer
def summary_plot(
    c,
    x: Optional[str] = None,
    y: str = "capacities_gravimetric_coulombic_efficiency",
    height: Optional[int] = None,
    width: int = 900,
    markers: bool = True,
    title: Optional[str] = None,
    x_range: Optional[list] = None,
    y_range: Optional[list] = None,
    ce_range: Optional[list] = None,
    norm_range: Optional[list] = None,
    cv_share_range: Optional[list] = None,
    split: bool = True,
    hover_columns: Optional[list] = None,
    auto_convert_legend_labels: bool = True,
    backend: Optional[str] = None,
    interactive: Optional[bool] = None,
    share_y: bool = False,
    rangeslider: bool = False,
    return_data: bool = False,
    verbose: bool = False,
    plotly_template: Optional[str] = None,
    seaborn_palette: str = "deep",
    seaborn_style: str = "dark",
    formation_cycles: int = 3,
    show_formation: bool = True,
    show_legend: bool = True,
    x_axis_domain_formation_fraction: float = 0.2,
    column_separator: float = 0.01,
    reset_losses: bool = True,
    link_capacity_scales: bool = False,
    fullcell_standard_normalization_type: str = "max",
    fullcell_standard_normalization_factor: Optional[float] = None,
    fullcell_standard_normalization_scaler: float = 1.0,
    fullcell_standard_normalization_cycle_numbers: Optional[list[int]] = None,
    seaborn_line_hooks: Optional[list[tuple[str, list, dict]]] = None,
    filters: Optional[dict] = None,
    nominal_capacity: Optional[float] = None,
    rate_filter_columns: Optional[Union[str, tuple, list]] = None,
    **kwargs,
) -> Any:
    """Create a summary plot.

    Args:
        c: cellpy object
        x: x-axis column (default: 'cycle_index')
        y: y-axis column or column set. Currently, the following predefined sets exists:
            "voltages", "capacities_gravimetric", "capacities_areal", "capacities_absolute",
            "capacities_gravimetric_split_constant_voltage", "capacities_areal_split_constant_voltage",
            "capacities_gravimetric_coulombic_efficiency", "capacities_areal_coulombic_efficiency",
            "capacities_absolute_coulombic_efficiency",
            "capacities_gravimetric_with_rate", "capacities_areal_with_rate",
            "capacities_absolute_with_rate",
            "fullcell_standard_gravimetric", "fullcell_standard_areal", "fullcell_standard_absolute",
        height: height of the plot (for plotly)
        width: width of the plot (for plotly)
        markers: use markers
        title: title of the plot
        x_range: limits for x-axis
        y_range: limits for y-axis
        ce_range: limits for coulombic efficiency (if present)
        norm_range: limits for normalized capacity (if present)
        cv_share_range: limits for cv share (if present)
        split: split the plot
        hover_columns: columns to show in the hover tooltip (only for plotly)
        auto_convert_legend_labels: convert the legend labels to a nicer format.
        backend: plotting backend (``"plotly"`` or ``"matplotlib"``; default
            ``"plotly"``)
        interactive: deprecated alias for backend selection
            (``True`` → ``"plotly"``, ``False`` → ``"matplotlib"``); removal 2.1
        rangeslider: add a range slider to the x-axis (only for plotly)
        share_y: share y-axis (only for plotly)
        return_data: return the data used for plotting
        verbose: print out some extra information to make it easier to find out what to plot next time
        plotly_template: name of the plotly template to use
        seaborn_palette: name of the seaborn palette to use (matplotlib backend)
        seaborn_style: name of the seaborn style to use (matplotlib backend)
        formation_cycles: number of formation cycles to show
        show_formation: show formation cycles
        show_legend: show the legend
        x_axis_domain_formation_fraction: fraction of the x-axis domain for the formation cycles (default: 0.2)
        column_separator: separation between columns when splitting the plot (only for plotly)
        reset_losses: reset the losses to the first cycle (only for fullcell_standard plots)
        link_capacity_scales: link the capacity scales (only for fullcell_standard plots)
        fullcell_standard_normalization_type: normalization type for the fullcell standard plots (capacity retention)
            (divide, multiply, area, max, on-max, False)
        fullcell_standard_normalization_factor: normalization factor for the fullcell standard plots
        fullcell_standard_normalization_scaler: scaler for the fullcell standard plots
        fullcell_standard_normalization_cycle_numbers: cycle numbers to use for normalization (only for fullcell_standard plots)
        seaborn_line_hooks: list of functions to hook into the seaborn lines (e.g. to update the marker_size)
        filters: optional dict forwarded to
            :func:`cellpy.filters.filter_summary` to drop rows from the
            summary before plotting (e.g. ``filters={"rate": (0, 0.5)}``
            drops slow-rate characterisation cycles). See
            :func:`cellpy.filters.filter_summary` for range semantics.
        nominal_capacity: optional plain float in
            ``c.cellpy_units.nominal_capacity`` units. When given, the
            ``charge_c_rate`` / ``discharge_c_rate`` columns are
            rescaled to use this nominal capacity instead of
            ``c.data.nom_cap`` (multiplies rates by
            ``c.data.nom_cap / nominal_capacity``).
        rate_filter_columns: optional override for which rate column(s)
            the ``rate`` filter targets. Defaults to both
            ``(charge_c_rate, discharge_c_rate)``; pass a single string
            (e.g. ``"discharge_c_rate"``) to filter only one side.
        **kwargs: includes additional parameters for the plotting backend (not properly documented yet).

    Returns:
        if ``return_data`` is True, returns a tuple with the figure and the data used for plotting.
        Otherwise, it returns only the figure. With ``backend="plotly"`` the figure is a
        plotly figure; with ``backend="matplotlib"`` it is a matplotlib figure.

    Examples:
        Default plot (capacity and Coulombic efficiency vs cycle number)::

            >>> from cellpy.utils.plotutils import summary_plot
            >>> fig = summary_plot(c)
            >>> fig.show()

        Plot gravimetric capacity alone, with formation cycles disabled::

            >>> fig = summary_plot(c, y="capacities_gravimetric", show_formation=False)

        Use the matplotlib backend (seaborn styling), e.g. for an
        SVG export from a script::

            >>> fig = summary_plot(c, y="capacities_gravimetric", backend="matplotlib")
            >>> fig.savefig("summary.svg")

        Get the prepared DataFrame back together with the figure (useful
        for custom annotations or follow-up analysis)::

            >>> fig, data = summary_plot(c, y="capacities_gravimetric", return_data=True)
            >>> data.head()

        New ``*_with_rate`` y-set adds a C-rate subplot on row 0::

            >>> fig = summary_plot(c, y="capacities_gravimetric_with_rate")

        Drop slow-rate characterisation cycles (e.g. keep only rows where
        both ``charge_c_rate`` and ``discharge_c_rate`` are above 0.1)::

            >>> fig = summary_plot(
            ...     c,
            ...     y="capacities_gravimetric",
            ...     filters={"rate": (0.1, 10.0)},
            ... )

        Same idea using the symmetric ``{value, delta}`` form to keep
        rows close to a target C/2 rate::

            >>> fig = summary_plot(
            ...     c,
            ...     y="capacities_gravimetric_with_rate",
            ...     filters={"rate": {"value": 0.5, "delta": 0.05}},
            ... )

        Filter on the discharge rate only (charge rate is ignored)::

            >>> fig = summary_plot(
            ...     c,
            ...     y="capacities_gravimetric",
            ...     filters={"rate": (0.1, 1.0)},
            ...     rate_filter_columns="discharge_c_rate",
            ... )

        Override the nominal capacity used for the C-rate axis without
        re-running ``make_summary``. The rate columns are rescaled by
        ``c.data.nom_cap / nominal_capacity``; here we both rescale and
        filter in the new units::

            >>> fig = summary_plot(
            ...     c,
            ...     y="capacities_gravimetric_with_rate",
            ...     nominal_capacity=200.0,
            ...     filters={"rate": (0.1, 5.0)},
            ... )

        The same filter is available without plotting via
        :meth:`CellpyCell.filtered_summary` (returns a DataFrame copy)::

            >>> trimmed = c.filtered_summary(rate=(0.1, 10.0))

        Or as a free function on any summary-shaped DataFrame::

            >>> from cellpy.filters import filter_summary
            >>> trimmed = filter_summary(c.data.summary.reset_index(),
            ...                          rate=(0.1, 10.0))
    """
    # Create config from parameters
    config = SummaryPlotConfig.from_kwargs(
        x=x,
        y=y,
        height=height,
        width=width,
        markers=markers,
        title=title,
        x_range=x_range,
        y_range=y_range,
        ce_range=ce_range,
        norm_range=norm_range,
        cv_share_range=cv_share_range,
        split=split,
        hover_columns=hover_columns,
        auto_convert_legend_labels=auto_convert_legend_labels,
        backend=backend,
        interactive=interactive,
        share_y=share_y,
        rangeslider=rangeslider,
        return_data=return_data,
        verbose=verbose,
        plotly_template=plotly_template,
        seaborn_palette=seaborn_palette,
        seaborn_style=seaborn_style,
        formation_cycles=formation_cycles,
        show_formation=show_formation,
        show_legend=show_legend,
        x_axis_domain_formation_fraction=x_axis_domain_formation_fraction,
        column_separator=column_separator,
        reset_losses=reset_losses,
        link_capacity_scales=link_capacity_scales,
        fullcell_standard_normalization_type=fullcell_standard_normalization_type,
        fullcell_standard_normalization_factor=fullcell_standard_normalization_factor,
        fullcell_standard_normalization_scaler=fullcell_standard_normalization_scaler,
        fullcell_standard_normalization_cycle_numbers=fullcell_standard_normalization_cycle_numbers,
        seaborn_line_hooks=seaborn_line_hooks,
        filters=filters,
        nominal_capacity=nominal_capacity,
        rate_filter_columns=rate_filter_columns,
        **kwargs,
    )

    # Column names the caller spelled out are resolved against the frame, so
    # 1.x spellings ("cycle_index") keep working after the native-headers flip.
    config.x = _resolve_summary_column(c, config.x)
    config.hover_columns = _resolve_summary_columns(c, config.hover_columns)

    # Resolve backend= vs deprecated interactive= (#639).
    resolved_backend = config.backend
    if config.interactive is not None:
        warn_once(
            "summary_plot(interactive=...)",
            'backend="plotly"|"matplotlib"',
            removal="2.1",
        )
        if resolved_backend is None:
            resolved_backend = "plotly" if config.interactive else "matplotlib"
    if resolved_backend is None:
        resolved_backend = "plotly"
    config.backend = resolved_backend

    if resolved_backend == "plotly" and not plotly_available:
        warnings.warn(
            "plotly not available, and it is currently the only supported plotly backend"
        )
        return None

    # prepare → spec → render (#638 / #639)
    from cellpy.plotting.backends import get_backend
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.summary import prepare as prepare_summary

    plot_info = SummaryPlotInfo(c)
    family = plot_registry.get(config.y)
    ctx = from_source(c)
    frame, spec = prepare_summary(ctx, family, config, plot_info=plot_info)

    # MatplotlibBackend still needs the live config/cell for seaborn styling knobs.
    spec.extras["config"] = config
    spec.extras["cell"] = c

    fig = get_backend(resolved_backend).render(frame, spec)

    if config.return_data:
        return fig, frame
    return fig




def partition_summary_cv_steps(
    c,
    x: str,
    column_set: list,
    split: bool = False,
    var_name: str = "variable",
    value_name: str = "value",
):
    """Partition the summary data into CV and non-CV steps.

    Args:
        c: cellpy object
        x: x-axis column name
        column_set: names of columns to include
        split: add additional column that can be used to split the data when plotting.
        var_name: name of the variable column after melting
        value_name: name of the value column after melting

    Returns:
        ``pandas.DataFrame`` (melted with columns x, var_name, value_name, and optionally "row" if split is True)
    """
    import pandas as pd

    # A copy, because `set_index(..., inplace=True)` below would otherwise move
    # the x column out of the *cell's own* summary frame and leave it there:
    # one CV-split plot and `c.data.summary` has permanently lost `cycle_num`,
    # breaking every later plot and any user code reading that column (#567).
    summary = c.data.summary.copy()

    summary_no_cv = c.make_summary(
        selector_type="non-cv", create_copy=True
    ).data.summary
    summary_only_cv = c.make_summary(
        selector_type="only-cv", create_copy=True
    ).data.summary
    if x != summary.index.name:
        summary.set_index(x, inplace=True)
        summary_no_cv.set_index(x, inplace=True)
        summary_only_cv.set_index(x, inplace=True)

    summary = summary[column_set]

    summary_no_cv = summary_no_cv[column_set]
    summary_no_cv.columns = [col + "_non_cv" for col in summary_no_cv.columns]

    summary_only_cv = summary_only_cv[column_set]
    summary_only_cv.columns = [col + "_cv" for col in summary_only_cv.columns]

    if split:
        id_vars = [x, "row"]
        summary_no_cv["row"] = "without CV"
        summary_only_cv["row"] = "with CV"
        summary["row"] = "all"
    else:
        id_vars = x

    summary_no_cv = summary_no_cv.reset_index()
    summary_only_cv = summary_only_cv.reset_index()
    summary = summary.reset_index()
    summary_no_cv = summary_no_cv.melt(
        id_vars, var_name=var_name, value_name=value_name
    )
    summary_only_cv = summary_only_cv.melt(
        id_vars, var_name=var_name, value_name=value_name
    )
    summary = summary.melt(id_vars, var_name=var_name, value_name=value_name)

    s = pd.concat([summary, summary_no_cv, summary_only_cv], axis=0)
    s = s.reset_index(drop=True)

    return s


def raw_plot(
    cell,
    y=None,
    y_label=None,
    x=None,
    x_label=None,
    title=None,
    interactive=True,
    plot_type="voltage-current",
    double_y=True,
    **kwargs,
):
    """Plot raw data.

    Args:
        cell: cellpy object
        y (str or list): y-axis column
        y_label (str or list): label for y-axis
        x (str): x-axis column
        x_label (str): label for x-axis
        title (str): title of the plot
        interactive (bool): use interactive plotting
        plot_type (str): type of plot (defaults to "voltage-current") (overrides given y if y is not None),
          currently only "voltage-current", "raw", "capacity", "capacity-current", and "full" is supported.
        double_y (bool): use double y-axis (only for matplotlib and when plot_type with 2 rows is used)
        **kwargs: additional parameters for the plotting backend

    Returns:
        ``matplotlib`` figure or ``plotly`` figure

    """
    from cellpy.readers.data_structures import Q

    _set_individual_y_labels = False
    _special_height = None

    # Per-cell, not the module-level legacy singleton (#567).
    hdr_raw = _LiveHeaders(cell, "raw")
    raw = cell.data.raw.copy()
    if y is not None:
        if y_label is None:
            y_label = y
        y = [y]
        y_label = [y_label]

    elif plot_type is not None:
        # special pre-defined plot types
        if plot_type == "voltage-current":
            y1 = hdr_raw["voltage_txt"]
            y1_label = f"Voltage ({cell.data.raw_units.voltage})"
            y2 = hdr_raw["current_txt"]
            y2_label = f"Current ({cell.data.raw_units.current})"
            y = [y1, y2]
            y_label = [y1_label, y2_label]

        elif plot_type == "capacity":
            _y = [
                (
                    hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
            ]
            y, y_label = zip(*_y)

        elif plot_type == "raw":
            _y = [
                (
                    hdr_raw["cycle_index_txt"],
                    f"Cycle index (#)",
                ),
                (
                    hdr_raw["step_index_txt"],
                    f"Step index (#)",
                ),
                (hdr_raw["voltage_txt"], f"Voltage ({cell.data.raw_units.voltage})"),
                (hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
            ]
            y, y_label = zip(*_y)
            _special_height = 600

        elif plot_type == "capacity-current":
            _y = [
                (
                    hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
                (hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
            ]
            y, y_label = zip(*_y)
            _special_height = 500

        elif plot_type == "full":
            _y = [
                (hdr_raw["voltage_txt"], f"Voltage ({cell.data.raw_units.voltage})"),
                (hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
                (
                    hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    hdr_raw["cycle_index_txt"],
                    f"Cycle index (#)",
                ),
                (
                    hdr_raw["step_index_txt"],
                    f"Step index (#)",
                ),
            ]
            y, y_label = zip(*_y)
            _special_height = 800

        else:
            warnings.warn(f"Plot type {plot_type} not supported")
            return None
    else:
        # default to voltage if y is not given
        y = [hdr_raw["voltage_txt"]]
        y_label = [f"Voltage ({cell.data.raw_units.voltage})"]

    if x is None:
        x = "test_time_hrs"

    if x in ["test_time_hrs", "test_time_hours"]:
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("hours").magnitude
        raw[x] = raw[hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (hours)"
    elif x == "test_time_days":
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("days").magnitude
        raw[x] = raw[hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (days)"
    elif x == "test_time_years":
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("years").magnitude
        raw[x] = raw[hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (years)"

    if title is None:
        title = f"{cell.cell_name}"

    number_of_rows = len(y)

    if plotly_available and interactive:
        title = f"<b>{title}</b>"
        if number_of_rows == 1:
            # single plot
            import plotly.express as px

            if x_label or y_label:
                labels = {}
                if x_label:
                    labels[x] = x_label
                if y_label:
                    labels[y[0]] = y_label[0]
            else:
                labels = None
            fig = px.line(raw, x=x, y=y[0], title=title, labels=labels, **kwargs)

        else:
            from plotly.subplots import make_subplots
            import plotly.graph_objects as go

            width = kwargs.pop("width", 1000)
            height = kwargs.pop("height", None)
            if height is None:
                if _special_height is not None:
                    height = _special_height
                else:
                    height = number_of_rows * 300

            vertical_spacing = kwargs.pop("vertical_spacing", 0.02)

            fig = make_subplots(
                rows=number_of_rows,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=vertical_spacing,
                x_title=x_label,
                # hoversubplots="axis",  # only available in plotly 5.21
            )
            x_values = raw[x]

            rows = range(1, number_of_rows + 1)
            for i in range(number_of_rows):
                fig.add_trace(
                    go.Scatter(x=x_values, y=raw[y[i]], name=y_label[i]),
                    row=rows[i],
                    col=1,
                    **kwargs,
                )

            fig.update_layout(height=height, width=width, title_text=title)
            if _set_individual_y_labels:
                for i in range(number_of_rows):
                    fig.update_yaxes(title_text=y_label[i], row=rows[i], col=1)

        return fig

    # default to a simple matplotlib figure
    xlim = kwargs.get("xlim")
    figsize = kwargs.pop("figsize", (10, 2 * number_of_rows))
    if seaborn_available:
        import seaborn as sns

        if double_y:
            sns.set_style(kwargs.pop("style", "dark"))
        else:
            sns.set_style(kwargs.pop("style", "darkgrid"))

    if len(y) == 1:
        y = y[0]
        y_label = y_label[0]
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(raw[x], raw[y])
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.set_xlim(xlim)
        plt.close(fig)
        return fig

    elif len(y) == 2 and double_y:
        fig, ax_v = plt.subplots(figsize=figsize)

        color = "tab:red"
        ax_v.set_xlabel(x_label)
        ax_v.set_ylabel(y_label[0], color=color)
        ax_v.plot(raw[x], raw[y[0]], label=y_label[0], color=color)
        ax_v.tick_params(axis="y", labelcolor=color)

        ax_c = ax_v.twinx()

        color = "tab:blue"
        ax_c.set_ylabel(y_label[1], color=color)
        ax_c.plot(raw[x], raw[y[1]], label=y_label[1], color=color)
        ax_c.tick_params(axis="y", labelcolor=color)
        ax_v.set_xlim(xlim)
    else:
        fig, axes = plt.subplots(
            nrows=number_of_rows, ncols=1, figsize=figsize, sharex=True
        )

        for i in range(number_of_rows):
            axes[i].plot(raw[x], raw[y[i]])
            axes[i].set_ylabel(y_label[i])

        axes[0].set_title(title)
        axes[0].set_xlim(xlim)
        axes[-1].set_xlabel(x_label)

        fig.align_ylabels()

    fig.tight_layout()
    plt.close(fig)
    return fig


def cycle_info_plot(
    cell,
    cycle=None,
    get_axes=False,
    interactive=True,
    t_unit="hours",
    v_unit="V",
    i_unit="mA",
    **kwargs,
):
    """Show raw data together with step and cycle information.

    Args:
        cell: cellpy object
        cycle (int or list or tuple): cycle(s) to select (must be int for matplotlib)
        get_axes (bool): return axes (for matplotlib) or figure (for plotly)
        interactive (bool): use interactive plotting (if available)
        t_unit (str): unit for x-axis (default: "hours")
        v_unit (str): unit for y-axis (default: "V")
        i_unit (str): unit for current (default: "mA")
        **kwargs: parameters specific to plotting backend.

    Returns:
        ``matplotlib.axes`` or None
    """
    t_scaler = cell.unit_scaler_from_raw(t_unit, "time")
    v_scaler = cell.unit_scaler_from_raw(v_unit, "voltage")
    i_scaler = cell.unit_scaler_from_raw(i_unit, "current")

    if plotly_available and interactive:
        fig = _cycle_info_plot_plotly(
            cell,
            cycle,
            get_axes,
            t_scaler,
            t_unit,
            v_scaler,
            v_unit,
            i_scaler,
            i_unit,
            **kwargs,
        )
        if get_axes:
            return fig
        return fig

    axes = _cycle_info_plot_matplotlib(
        cell,
        cycle,
        get_axes,
        t_scaler,
        t_unit,
        v_scaler,
        v_unit,
        i_scaler,
        i_unit,
        **kwargs,
    )

    if get_axes:
        return axes


def _cycle_info_plot_plotly(
    cell,
    cycle,
    get_axes,
    t_scaler,
    t_unit,
    v_scaler,
    v_unit,
    i_scaler,
    i_unit,
    **kwargs,
):
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np

    if kwargs.get("xlim"):
        logging.info("xlim is not supported for plotly yet")

    # Per-cell, not the module-level legacy singletons (#567).
    raw_hdr = _LiveHeaders(cell, "raw")
    step_hdr = _LiveHeaders(cell, "steps")

    data = cell.data.raw.copy()
    table = cell.data.steps.copy()

    if cycle is None:
        cycle = list(data[raw_hdr.cycle_index_txt].unique())

    if not isinstance(cycle, (list, tuple)):
        cycle = [cycle]

    delta = "_delta"
    v_delta = step_hdr.stat("voltage", "delta")
    i_delta = step_hdr.stat("current", "delta")
    c_delta = step_hdr.stat("charge", "delta")
    dc_delta = step_hdr.stat("discharge", "delta")
    cycle_ = step_hdr.cycle
    step_ = step_hdr.step
    type_ = step_hdr.type

    time_hdr = raw_hdr.test_time_txt
    cycle_hdr = raw_hdr.cycle_index_txt
    step_number_hdr = raw_hdr.step_index_txt
    current_hdr = raw_hdr.current_txt
    voltage_hdr = raw_hdr.voltage_txt

    data = data[
        [
            time_hdr,
            cycle_hdr,
            step_number_hdr,
            current_hdr,
            voltage_hdr,
        ]
    ]

    table = table[
        [
            cycle_,
            step_,
            type_,
            v_delta,
            i_delta,
            c_delta,
            dc_delta,
        ]
    ]
    m_cycle_data = data[cycle_hdr].isin(cycle)
    data = data.loc[m_cycle_data, :]

    data[time_hdr] = data[time_hdr] * t_scaler
    data[voltage_hdr] = data[voltage_hdr] * v_scaler
    data[current_hdr] = data[current_hdr] * i_scaler
    data = data.merge(
        table,
        left_on=(cycle_hdr, step_number_hdr),
        right_on=(cycle_, step_),
    ).sort_values(by=[time_hdr])

    fig = go.Figure()

    grouped_data = data.groupby(cycle_hdr)
    for cycle_number, group in grouped_data:
        x = group[time_hdr]
        y = group[voltage_hdr]
        s = group[step_number_hdr]
        i = group[current_hdr]

        st = group[type_]
        dV = group[v_delta]
        dI = group[i_delta]
        dC = group[c_delta]
        dDC = group[dc_delta]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=f"cycle {cycle_number}",
                customdata=np.stack((i, s, st, dV, dI, dC, dDC), axis=-1),
                hovertemplate="<br>".join(
                    [
                        "<b>Time: %{x:.2f}" + f" {t_unit}" + "</b>",
                        "  <b>Voltage:</b> %{y:.4f}" + f" {v_unit}",
                        "  <b>Current:</b> %{customdata[0]:.4f}" + f" {i_unit}",
                        "<b>Step: %{customdata[1]} (%{customdata[2]})</b>",
                        "  <b>ΔV:</b> %{customdata[3]:.2f}",
                        "  <b>ΔI:</b> %{customdata[4]:.2f}",
                        "  <b>ΔCh:</b> %{customdata[5]:.2f}",
                        "  <b>ΔDCh:</b> %{customdata[6]:.2f}",
                    ]
                ),
            ),
        )

    cell_name = kwargs.get("title", cell.cell_name)
    height = kwargs.get("height", 600)
    width = kwargs.get("width", 1000)
    title_start = f"<b>{cell_name}</b> Cycle"
    if len(cycle) > 2:
        if cycle[-1] - cycle[0] == len(cycle) - 1:
            title = f"{title_start}s {cycle[0]} - {cycle[-1]}"
        else:
            title = f"{title_start}s {cycle}"
    elif len(cycle) == 2:
        title = f"{title_start}s {cycle[0]} and {cycle[1]}"
    else:
        title = f"{title_start} {cycle[0]}"

    fig.update_layout(
        title=title,
        xaxis_title=f"Time ({t_unit})",
        yaxis_title=f"Voltage ({v_unit})",
        width=width,
        height=height,
    )

    if get_axes:
        return fig
    fig.show()


def _plot_step(ax, x, y, color):
    ax.plot(x, y, color=color, linewidth=3)


def _get_info(table, cycle, step, step_hdr):
    """``step_hdr`` is passed in: this helper never sees the cell, and the
    module-level singleton it used to read answered with legacy names (#567)."""
    m_table = (table[step_hdr.cycle] == cycle) & (table[step_hdr.step] == step)
    # Step-table statistic columns, composed from the live stems rather than
    # hard-coded legacy spellings ("voltage_delta" is "potential_delta" on a
    # native frame).
    p1, p2 = table.loc[
        m_table, [step_hdr.stat("point", "min"), step_hdr.stat("point", "max")]
    ].values[0]
    c1, c2 = (
        table.loc[
            m_table,
            [step_hdr.stat("current", "min"), step_hdr.stat("current", "max")],
        ]
        .abs()
        .values[0]
    )
    d_voltage, d_current = table.loc[
        m_table, [step_hdr.stat("voltage", "delta"), step_hdr.stat("current", "delta")]
    ].values[0]
    d_discharge, d_charge = table.loc[
        m_table,
        [step_hdr.stat("discharge", "delta"), step_hdr.stat("charge", "delta")],
    ].values[0]
    current_max = (c1 + c2) / 2
    rate = table.loc[m_table, step_hdr.rate_avr].values[0]
    step_type = table.loc[m_table, step_hdr.type].values[0]
    return [step_type, rate, current_max, d_voltage, d_current, d_discharge, d_charge]


def _cycle_info_plot_matplotlib(
    cell,
    cycle,
    get_axes,
    t_scaler,
    t_unit,
    v_scaler,
    v_unit,
    i_scaler,
    i_unit,
    **kwargs,
):
    # obs! hard-coded col-names. Please fix me.
    if cycle is None:
        warnings.warn("Only one cycle at a time is supported for matplotlib")
        cycle = 1

    if isinstance(cycle, (list, tuple)):
        warnings.warn("Only one cycle at a time is supported for matplotlib")
        cycle = cycle[0]

    data = cell.data.raw
    table = cell.data.steps

    # Per-cell, not the module-level legacy singletons (#567).
    raw_hdr = _LiveHeaders(cell, "raw")
    step_hdr = _LiveHeaders(cell, "steps")

    span_colors = ["#4682B4", "#FFA07A"]

    voltage_color = "#008B8B"
    current_color = "#CD5C5C"

    m_cycle_data = data[raw_hdr.cycle_index_txt] == cycle
    all_steps = data[m_cycle_data][raw_hdr.step_index_txt].unique()

    color = itertools.cycle(span_colors)

    fig = plt.figure(figsize=(20, 8))
    fig.suptitle(f"Cycle: {cycle}")

    ax3 = plt.subplot2grid((8, 3), (0, 0), colspan=3, rowspan=1, fig=fig)  # steps
    ax4 = plt.subplot2grid((8, 3), (1, 0), colspan=3, rowspan=2, fig=fig)  # info
    ax1 = plt.subplot2grid((8, 3), (3, 0), colspan=3, rowspan=5, fig=fig)  # data

    ax2 = ax1.twinx()
    ax1.set_xlabel(f"time ({t_unit})")
    ax1.set_ylabel(f"voltage ({v_unit})", color=voltage_color)
    ax2.set_ylabel(f"current ({i_unit})", color=current_color)

    annotations_1 = []  # step number (IR)
    annotations_2 = []  # step number
    annotations_4 = []  # info

    for i, s in enumerate(all_steps):
        m = m_cycle_data & (data[raw_hdr.step_index_txt] == s)
        c = data.loc[m, raw_hdr.current_txt] * i_scaler
        v = data.loc[m, raw_hdr.voltage_txt] * v_scaler
        t = data.loc[m, raw_hdr.test_time_txt] * t_scaler
        step_type, rate, current_max, dv, dc, d_discharge, d_charge = _get_info(
            table, cycle, s, step_hdr
        )
        if len(t) > 1:
            fcolor = next(color)

            info_txt = f"{step_type}\ni = |{i_scaler * current_max:0.2f}| {i_unit}\n"
            info_txt += f"delta V = {dv:0.2f} %\ndelta i = {dc:0.2f} %\n"
            info_txt += f"delta C = {d_charge:0.2} %\ndelta DC = {d_discharge:0.2} %\n"

            for ax in [ax2, ax3, ax4]:
                ax.axvspan(t.iloc[0], t.iloc[-1], facecolor=fcolor, alpha=0.2)
            _plot_step(ax1, t, v, voltage_color)
            _plot_step(ax2, t, c, current_color)
            annotations_1.append([f"{s}", t.mean()])
            annotations_4.append([info_txt, t.mean()])
        else:
            info_txt = f"{s}({step_type})"
            annotations_2.append([info_txt, t.mean()])
    ax3.set_ylim(0, 1)
    for s in annotations_1:
        ax3.annotate(f"{s[0]}", (s[1], 0.2), ha="center")

    for s in annotations_2:
        ax3.annotate(f"{s[0]}", (s[1], 0.6), ha="center")

    for s in annotations_4:
        ax4.annotate(f"{s[0]}", (s[1], 0.0), ha="center")

    for ax in [ax3, ax4]:
        ax.axes.get_yaxis().set_visible(False)
        ax.axes.get_xaxis().set_visible(False)

    if x := kwargs.get("xlim"):
        ax1.set_xlim(x)
        ax2.set_xlim(x)
        ax3.set_xlim(x)
        ax4.set_xlim(x)

    if get_axes:
        return ax1, ax2, ax2, ax4


@dataclasses.dataclass
class CyclesPlotterConfig:
    """Configuration dataclass for cycles_plot parameters.

    Encapsulates all parameters for cycles_plot to improve maintainability
    and enable easier refactoring. Note that 'c' (cellpy object) and 'df'
    (dataframe) are passed separately as they are data objects, not configuration.
    """

    # Data objects (computed during function execution)
    form_cycles: Optional[pd.DataFrame] = None
    rest_cycles: Optional[pd.DataFrame] = None

    # Plot metadata
    fig_title: Optional[str] = None
    capacity_unit: Optional[str] = None

    # Plotly-specific
    plotly_template: Optional[str] = None
    force_colorbar: bool = False
    force_nonbar: bool = False

    # Matplotlib-specific
    figsize: tuple = (6, 4)
    cbar_aspect: int = 30

    # Common styling
    colormap: str = "Blues_r"
    formation_colormap: str = "autumn"
    cut_colorbar: bool = True
    width: int = 600
    height: int = 400
    marker_size: int = 5
    formation_line_color: str = "rgba(152, 0, 0, .8)"
    xlim: Optional[list[float]] = None
    ylim: Optional[list[float]] = None

    # Cycle information
    n_rest_cycles: Optional[int] = None
    n_form_cycles: Optional[int] = None
    show_formation: bool = True

    # Seaborn-specific (for matplotlib backend)
    seaborn_style_dict: Optional[dict] = None
    seaborn_context: str = "notebook"
    seaborn_facecolor: str = "#EAEAF2"
    seaborn_edgecolor: str = "black"
    seaborn_style: str = "dark"
    seaborn_palette: str = "deep"


@notebook_docstring_printer
def cycles_plot(
    c,
    cycles=None,
    inter_cycle_shift=True,
    cycle_mode=None,
    formation_cycles=3,
    show_formation=True,
    mode="gravimetric",
    method="forth-and-forth",
    interpolated=True,
    number_of_points=200,
    colormap="Blues_r",
    formation_colormap="autumn",
    cut_colorbar=True,
    title=None,
    figsize=(6, 4),
    x_range=None,
    y_range=None,
    xlim=None,
    ylim=None,
    interactive=True,
    return_figure=None,
    width=800,
    height=600,
    marker_size=5,
    formation_line_color="rgba(152, 0, 0, .8)",
    force_colorbar=False,
    force_nonbar=False,
    plotly_template=None,
    seaborn_palette: str = "deep",
    seaborn_style: str = "dark",
    return_data=False,
    **kwargs,
):
    """
    Plot the voltage vs. capacity for different cycles of a cell.

    This function is meant as an easy way of visualizing the voltage vs. capacity for different cycles of a cell. The
    cycles are plotted with different colors, and the formation cycles are highlighted with a different colormap.
    It is not intended to provide you with high quality plots, but rather to give you a quick overview of the data.

    Args:
        c: cellpy object containing the data to plot.
        cycles (list, optional): List of cycle numbers to plot. If None, all cycles are plotted.
        inter_cycle_shift (bool, optional): Whether to shift the cycles by one. Default is True.
        cycle_mode (str, optional): Mode for the test (anode or other). Default is None (i.e. use the cellpy cell object's cycle_mode).
        formation_cycles (int, optional): Number of formation cycles to highlight. Default is 3.
        show_formation (bool, optional): Whether to show formation cycles. Default is True.
        mode (str, optional): Mode for capacity ('gravimetric', 'areal', etc.). Default is 'gravimetric'.
        method (str, optional): Method for interpolation. Default is 'forth-and-forth'.
        interpolated (bool, optional): Whether to interpolate the data. Default is True.
        number_of_points (int, optional): Number of points for interpolation. Default is 200.
        colormap (str, optional): Colormap for the cycles. Default is 'Blues_r'.
        formation_colormap (str, optional): Colormap for the formation cycles. Default is 'autumn'.
        cut_colorbar (bool, optional): Whether to cut the colorbar. Default is True.
        title (str, optional): Title of the plot. If None, the cell name is used.
        figsize (tuple, optional): Size of the figure for matplotlib. Default is (6, 4).
        xlim (list, optional): Limits for the x-axis.
        ylim (list, optional): Limits for the y-axis.
        interactive (bool, optional): Whether to use interactive plotting (Plotly). Default is True.
        return_figure (bool, optional): Whether to return the figure object. Default is opposite of interactive.
        width (int, optional): Width of the figure for Plotly. Default is 600.
        height (int, optional): Height of the figure for Plotly. Default is 400.
        marker_size (int, optional): Size of the markers for Plotly. Default is 5.
        formation_line_color (str, optional): Color for the formation cycle lines in Plotly. Default is 'rgba(152, 0, 0, .8)'.
        force_colorbar (bool, optional): Whether to force the colorbar to be shown. Default is False.
        force_nonbar (bool, optional): Whether to force the colorbar to be hidden. Default is False.
        plotly_template (str, optional): Plotly template to use (uses default template if None).
        seaborn_palette: name of the seaborn palette to use (only if seaborn is available).
        seaborn_style: name of the seaborn style to use (only if seaborn is available).
        return_data (bool, optional): Whether to return the data used for the plot. Default is False.
        **kwargs: Additional keyword arguments for the plotting backend.

    Additional keyword arguments for Plotly:
        plotly_max_individual_traces_for_lines (int, optional): Maximum number of individual traces (not including formation cycles) for lines in Plotly. Default is 8.
        plotly_xaxes_kwargs (dict, optional): propagated to plotly.update_xaxes.
        plotly_yaxes_kwargs (dict, optional): propagated to plotly.update_yaxes.
        plotly_layout_kwargs (dict, optional): propagated to plotly.update_layout.

    Returns:
        The figure is a matplotlib.figure.Figure or a plotly.graph_objects.Figure, depending on the backend used.
        If return_data is True:
            tuple: (figure, data)
        If return_figure is True:
            figure: The generated plot figure (same as the return value).
        Else:
            None: The plot is shown in the default browser.
    """

    if interactive and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        interactive = False

    if return_figure is None:
        return_figure = not interactive

    if cycles is None:
        cycles = c.get_cycle_numbers()

    if title is None:
        _bold = "<b>" if interactive else "'"
        _end_bold = "</b>" if interactive else "'"
        _newline = "<br>" if interactive else "\n"
        _small = '<span style="font-size: 14px;">' if interactive else ""
        _end_small = "</span>" if interactive else ""
        top_title_line = f"Capacity plots for {_bold}{c.cell_name}{_end_bold}"
        second_title_line = f"{_small} - {mode} mode"
        if interpolated:
            second_title_line = f"{second_title_line}, interpolated ({number_of_points} points){_end_small}"
        else:
            second_title_line = f"{second_title_line}{_end_small}"

        title = _newline.join([top_title_line, second_title_line])

    kw_arguments = dict(
        method=method,
        interpolated=interpolated,
        label_cycle_number=True,
        categorical_column=True,
        number_of_points=number_of_points,
        insert_nan=True,
        mode=mode,
        cycle_mode=cycle_mode,
        inter_cycle_shift=inter_cycle_shift,
    )
    df = c.get_cap(cycles=cycles, **kw_arguments)
    # Temporary fix to ensure that the cycles are plotted in the correct order:
    df = df.sort_values(by=[_CCOLS.cycle_num, "direction"])

    selector = df[_CCOLS.cycle_num] <= formation_cycles
    form_cycles = df.loc[selector, :]
    rest_cycles = df.loc[~selector, :]

    n_form_cycles = len(form_cycles[_CCOLS.cycle_num].unique())
    n_rest_cycles = len(rest_cycles[_CCOLS.cycle_num].unique())

    capacity_unit = _get_capacity_unit(c, mode=mode)

    # Preparing for more homogeneous parameters:
    if x_range is not None:
        xlim = x_range
    if y_range is not None:
        ylim = y_range

    # Extracting seaborn-specific parameters from kwargs (for matplotlib backend):
    seaborn_context = kwargs.pop("seaborn_context", "notebook")
    seaborn_facecolor = kwargs.pop("seaborn_facecolor", "#EAEAF2")
    seaborn_edgecolor = kwargs.pop("seaborn_edgecolor", "black")
    seaborn_style_dict = kwargs.pop("seaborn_style_dict", None)

    config = CyclesPlotterConfig(
        form_cycles=form_cycles,
        rest_cycles=rest_cycles,
        fig_title=title,
        capacity_unit=capacity_unit,
        plotly_template=plotly_template,
        colormap=colormap,
        formation_colormap=formation_colormap,
        cut_colorbar=cut_colorbar,
        cbar_aspect=30,
        figsize=figsize,
        force_colorbar=force_colorbar,
        force_nonbar=force_nonbar,
        n_rest_cycles=n_rest_cycles,
        n_form_cycles=n_form_cycles,
        show_formation=show_formation,
        width=width,
        height=height,
        marker_size=marker_size,
        formation_line_color=formation_line_color,
        xlim=xlim,
        ylim=ylim,
        seaborn_style=seaborn_style,
        seaborn_palette=seaborn_palette,
        seaborn_context=seaborn_context,
        seaborn_facecolor=seaborn_facecolor,
        seaborn_edgecolor=seaborn_edgecolor,
        seaborn_style_dict=seaborn_style_dict,
    )

    if interactive:
        fig = _cycles_plotter_plotly(c, df, config, **kwargs)
        if return_data:
            return fig, df
        elif return_figure:
            return fig
        else:
            fig.show()

    else:
        fig = _cycles_plotter_matplotlib(c, df, config, **kwargs)
        if return_figure or return_data:
            plt.close(fig)
        if return_data:
            return fig, df
        elif return_figure:
            return fig


def _cycles_plotter_matplotlib(
    c,
    df,
    config: CyclesPlotterConfig,
    **kwargs,
):
    import numpy as np
    import matplotlib
    from matplotlib.colors import Normalize, ListedColormap

    if seaborn_available:
        import seaborn as sns

        seaborn_style_dict = config.seaborn_style_dict or {
            "axes.facecolor": config.seaborn_facecolor,
            "axes.edgecolor": config.seaborn_edgecolor,
        }
        sns.set_style(config.seaborn_style, seaborn_style_dict)
        sns.set_palette(config.seaborn_palette)
        sns.set_context(config.seaborn_context)

    fig, ax = plt.subplots(1, 1, figsize=config.figsize)
    fig_width, fig_height = config.figsize

    if not config.form_cycles.empty and config.show_formation:
        if fig_width < 6:
            logging.critical(
                "Warning: try setting the figsize to (6, 4) or larger for better visualization"
            )
        if fig_width > 8:
            logging.critical(
                "Warning: try setting the figsize to (8, 4) or smaller for better visualization"
            )
        min_cycle, max_cycle = (
            config.form_cycles[_CCOLS.cycle_num].min(),
            config.form_cycles[_CCOLS.cycle_num].max(),
        )
        norm_formation = Normalize(vmin=min_cycle, vmax=max_cycle)
        cycle_sequence = np.arange(min_cycle, max_cycle + 1, 1)

        shrink = min(1.0, (1 / 8) * config.n_form_cycles)

        c_m_formation = ListedColormap(
            plt.get_cmap(config.formation_colormap, 2 * len(cycle_sequence))(
                cycle_sequence
            )
        )
        s_m_formation = matplotlib.cm.ScalarMappable(
            cmap=c_m_formation, norm=norm_formation
        )
        for name, group in config.form_cycles.groupby(_CCOLS.cycle_num):
            ax.plot(
                group["capacity"],
                group[_CCOLS.potential],
                lw=2,  # alpha=0.7,
                color=s_m_formation.to_rgba(name),
                label=f"Cycle {name}",
            )
        cbar_formation = fig.colorbar(
            s_m_formation,
            ax=ax,  # label="Formation Cycle",
            ticks=np.arange(
                config.form_cycles[_CCOLS.cycle_num].min(),
                config.form_cycles[_CCOLS.cycle_num].max() + 1,
                1,
            ),
            shrink=shrink,
            aspect=config.cbar_aspect * shrink,
            location="right",
            anchor=(0.0, 0.0),
        )
        cbar_formation.set_label(
            "Form. Cycle",
            rotation=270,
            labelpad=12,
        )

    norm = Normalize(
        vmin=config.rest_cycles[_CCOLS.cycle_num].min(), vmax=config.rest_cycles[_CCOLS.cycle_num].max()
    )
    if config.cut_colorbar:
        cycle_sequence = np.arange(
            config.rest_cycles[_CCOLS.cycle_num].min(), config.rest_cycles[_CCOLS.cycle_num].max() + 1, 1
        )
        n = int(np.round(1.2 * config.rest_cycles[_CCOLS.cycle_num].max()))
        c_m = ListedColormap(plt.get_cmap(config.colormap, n)(cycle_sequence))
    else:
        c_m = plt.get_cmap(config.colormap)

    s_m = matplotlib.cm.ScalarMappable(cmap=c_m, norm=norm)
    for name, group in config.rest_cycles.groupby(_CCOLS.cycle_num):
        ax.plot(
            group["capacity"],
            group[_CCOLS.potential],
            lw=1,
            color=s_m.to_rgba(name),
            label=f"Cycle {name}",
        )
    cbar = fig.colorbar(
        s_m,
        ax=ax,
        label="Cycle",
        aspect=config.cbar_aspect,
        location="right",
    )
    cbar.set_label(
        "Cycle",
        rotation=270,
        labelpad=12,
    )
    # cbar.ax.yaxis.set_ticks_position("left")

    ax.set_xlabel(f"Capacity ({config.capacity_unit})")
    ax.set_ylabel(with_cellpy_unit("Voltage", "voltage", units=c.cellpy_units))

    ax.set_title(config.fig_title, loc="left", wrap=True)

    fig.tight_layout()

    if config.xlim:
        ax.set_xlim(config.xlim)
    if config.ylim:
        ax.set_ylim(config.ylim)

    return fig


def _cycles_plotter_plotly(
    c,
    df,
    config: CyclesPlotterConfig,
    **kwargs,
):
    import plotly.express as px
    import plotly.graph_objects as go

    set_plotly_template(config.plotly_template)

    color_scales = px.colors.named_colorscales()
    plotly_max_individual_traces_for_lines = kwargs.pop("plotly_max_individual_traces_for_lines", 8)
    if config.colormap not in color_scales:
        colormap = "Blues_r"
    else:
        colormap = config.colormap

    if config.cut_colorbar:
        range_color = [df[_CCOLS.cycle_num].min(), 1.2 * df[_CCOLS.cycle_num].max()]
    else:
        range_color = [df[_CCOLS.cycle_num].min(), df[_CCOLS.cycle_num].max()]
    if (
        config.n_rest_cycles is not None
        and config.n_rest_cycles < plotly_max_individual_traces_for_lines
        and not config.force_colorbar
    ) or config.force_nonbar:
        logging.info("using px.line for non-formation cycles")
        show_formation_legend = True
        cmap = px.colors.sample_colorscale(
            colorscale=colormap,
            samplepoints=config.n_rest_cycles,
            low=0.0,
            high=0.8,
            colortype="rgb",
        )

        fig = px.line(
            config.rest_cycles,
            x="capacity",
            y=_CCOLS.potential,
            color=_CCOLS.cycle_num,
            title=config.fig_title,
            labels={
                "capacity": f"Capacity ({config.capacity_unit})",
                _CCOLS.potential: with_cellpy_unit("Voltage", "voltage", units=c.cellpy_units),
            },
            color_discrete_sequence=cmap,
        )

    else:
        logging.info("using px.scatter for non-formation cycles")
        show_formation_legend = False
        fig = px.scatter(
            config.rest_cycles,
            x="capacity",
            y=_CCOLS.potential,
            title=config.fig_title,
            color=_CCOLS.cycle_num,
            labels={
                "capacity": f"Capacity ({config.capacity_unit})",
                _CCOLS.potential: with_cellpy_unit("Voltage", "voltage", units=c.cellpy_units),
            },
            color_continuous_scale=colormap,
            range_color=range_color,
        )

        fig.update_traces(mode="lines+markers", line_color="white", line_width=1)

    if not config.form_cycles.empty and config.show_formation:
        for name, group in config.form_cycles.groupby(_CCOLS.cycle_num):
            logging.info(f"using go.Scatter for formation cycle(s) {name}")
            trace = go.Scatter(
                x=group["capacity"],
                y=group[_CCOLS.potential],
                name=f"{name} (f.c.)",
                hovertemplate=f"Formation Cycle {name}<br>Capacity: %{{x}}<br>Voltage: %{{y}}",
                mode="lines",
                marker=dict(color=config.formation_line_color),
                showlegend=show_formation_legend,
                legendrank=1,
                legendgroup="formation",
            )

            fig.add_trace(trace)

    fig.update_traces(marker=dict(size=config.marker_size))

    if config.xlim:
        fig.update_xaxes(range=config.xlim)
    if config.ylim:
        fig.update_yaxes(range=config.ylim)

    plotly_xaxes_kwargs = kwargs.pop("plotly_xaxes_kwargs", {})
    plotly_yaxes_kwargs = kwargs.pop("plotly_yaxes_kwargs", {})
    if plotly_xaxes_kwargs:
        fig.update_xaxes(**plotly_xaxes_kwargs)
    if plotly_yaxes_kwargs:
        fig.update_yaxes(**plotly_yaxes_kwargs)

    plotly_layout_kwargs = kwargs.pop("plotly_layout_kwargs", {})

    fig.update_layout(
        height=config.height,
        width=config.width,
        **plotly_layout_kwargs,
    )

    return fig


def _cell_and_output_path():
    import pathlib
    import cellpy

    this_file = pathlib.Path(__file__)
    # p = this_file.parent.parent.parent / "testdata/hdf5/20160805_test001_45_cc.h5"
    p = pathlib.Path(r"C:\scripting\cellpy\local\20240516_nor000_01_fccc_01.h5")
    out = this_file.parent.parent.parent / "tmp"

    print(f"{p=}")
    print(f"{out=}")

    print(f"{p.exists()=}")
    print(f"{out.exists()=}")

    # c = cellpy.get(p)
    c = cellpy.get(
        p, instrument="arbin_sql_h5", cycle_mode="fullcell", 
        mass=15.5, area=1.767, loading=8.8, nominal_capacity=150.0)
    return c, out


def _check_plotter_plotly():
    import pathlib

    import cellpy

    p = pathlib.Path("../../testdata/hdf5/20160805_test001_45_cc.h5")
    out = pathlib.Path("../../tmp")
    assert out.exists()
    c = cellpy.get(p)
    fig = cycles_plot(
        c,
        ylim=[0.0, 1.0],
        show_formation=False,
        cut_colorbar=False,
        title="My nice plot",
        interactive=True,
        return_figure=True,
    )
    print("saving figure")
    print(f"{fig=}")
    print(f"{type(fig)=}")
    save_image_files(fig, out / "test_plot_plotly", backend="plotly")
    fig.show()


def _check_plotter_matplotlib():
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pathlib

    import cellpy

    p = pathlib.Path("../../testdata/hdf5/20160805_test001_45_cc.h5")
    out = pathlib.Path("../../tmp")
    assert out.exists()
    c = cellpy.get(p)
    fig = cycles_plot(
        c,
        ylim=[0.0, 1.0],
        show_formation=False,
        cut_colorbar=False,
        title="My nice plot",
        interactive=False,
        return_figure=True,
    )
    print("saving figure")
    print(f"{fig=}")
    print(f"{type(fig)=}")
    save_image_files(fig, out / "test_plot_matplotlib", backend="matplotlib")
    # need to create a new manager to show the figure since it is closed in
    # the plot_cycles function when issuing return_figure=True:
    make_matplotlib_manager(fig)
    plt.show()


def _check_summary_plotter_plotly():
    c, out = _cell_and_output_path()
    print("Checking summary_plotter_plotly")
    fig = summary_plot(
        c,
        # x="normalized_cycle_index",
        y="fullcell_standard_gravimetric",
        fullcell_standard_normalization_type="on-cycles",
        # fullcell_standard_normalization_factor=1500.0,
        fullcell_standard_normalization_cycle_numbers=[18],
        # ce_range=[0.0, 200.0],
        # ylim=[0.0, 1.0],
        # show_formation=False,
        # cut_colorbar=False,
        # split=True,
        title="My nice plot",
        interactive=True,  # rangeslider=True,
        show_formation=True,
        # return_data=False,
    )
    # print("saving figure")
    # print(f"{fig=}")
    # print(f"{type(fig)=}")
    # save_image_files(fig, out / "test_plot_plotly", backend="plotly")
    fig.show(renderer="browser")
    print("DONE")


def _check_summary_plotter_seaborn():
    import matplotlib

    matplotlib.use("Agg")
    print("Checking summary_plotter_seaborn")

    c, out = _cell_and_output_path()
    # Set non-interactive backend for VS Code/Cursor compatibility
    fig = summary_plot(
        c,
        # x="normalized_cycle_index",
        # y="capacities_gravimetric_split_constant_voltage",
        y="fullcell_standard_gravimetric",
        fullcell_standard_normalization_type="on-cycles",
        # fullcell_standard_normalization_factor=1500.0,
        fullcell_standard_normalization_cycle_numbers=[18],
        # ce_range=[0.0, 200.0],
        # ylim=[0.0, 1.0],
        # show_formation=False,
        # cut_colorbar=False,
        # split=True,
        title="My nice plot",
        interactive=False,  # rangeslider=True,
        show_formation=True,  # return_figure=True,
    )
    # print("saving figure")
    # print(f"{fig=}")
    # print(f"{type(fig)=}")
    # save_image_files(fig, out / "test_plot_plotly", backend="plotly")
    # Note: In VS Code/Cursor, use save_image_files instead of show()
    # fig.figure.show()  # This doesn't work in VS Code/Cursor
    save_image_files(fig, out / "test_plot_seaborn", backend="seaborn")
    print("DONE")


def _check_cycles_plotter_plotly():
    c, out = _cell_and_output_path()
    print("Checking cycle_plotter_plotly")
    fig = cycles_plot(
        c,
        y="capacities_gravimetric",
        cycles=[1, 2, 3, 4, 5, 20, 40, 60],
        interactive=True,
        return_figure=True,
    )
    save_image_files(fig, out / "test_plot_cycles_plotly", backend="plotly")
    print("DONE")


def _check_cycles_plotter_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    c, out = _cell_and_output_path()
    print("Checking cycle_plotter_matplotlib")
    fig = cycles_plot(
        c,
        y="capacities_gravimetric",
        interactive=False,
        return_figure=True,
    )
    save_image_files(fig, out / "test_plot_cycles_matplotlib", backend="matplotlib")
    print("DONE")


if __name__ == "__main__":
    # _check_plotter_plotly()
    # _check_plotter_matplotlib()
    # _check_summary_plotter_plotly()
    _check_summary_plotter_seaborn()
    # _check_cycles_plotter_plotly()
    # _check_cycles_plotter_matplotlib()
