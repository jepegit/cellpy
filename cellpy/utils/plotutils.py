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
# plotutils / collectors / (retired) batch_plotters (#567 / #658). Re-exported
# here so the `from cellpy.utils.plotutils import load_figure` spelling keeps
# working.
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
from cellpy.plotting.headers import LiveHeaders as _LiveHeaders
from cellpy.plotting.theme import make_plotly_template as _make_plotly_template

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


#: Prefer ``cellpy.plotting.headers.LiveHeaders`` (#647).
_MAPPING_FRAME = {"raw": "raw", "steps": "step", "summary": "cycle"}


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
        for family in plot_registry.iter_families(entry_point="summary_plot"):
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

    # Copies — `set_index(..., inplace=True)` must not touch `c.data.summary`
    # (#567). Frames come from helpers (exclude_step_types + full−non_cv; #654).
    summary, summary_no_cv, summary_only_cv = helpers._cv_partition_summary_frames(
        c
    )
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
    backend: Optional[str] = None,
    interactive: Optional[bool] = None,
    plot_type="voltage-current",
    double_y=True,
    **kwargs,
):
    """Plot raw data.

    Draws through prepare → spec → render (#647).

    Args:
        cell: cellpy object
        y (str or list): y-axis column
        y_label (str or list): label for y-axis
        x (str): x-axis column
        x_label (str): label for x-axis
        title (str): title of the plot
        backend (str, optional): ``"plotly"`` (default) or ``"matplotlib"``.
        interactive (bool, optional): Deprecated alias for backend selection
            (``True``→plotly, ``False``→matplotlib; removal 2.1).
        plot_type (str): type of plot (defaults to "voltage-current") (overrides given y if y is not None),
          currently only "voltage-current", "raw", "capacity", "capacity-current", and "full" is supported.
        double_y (bool): use double y-axis (only for matplotlib and when plot_type with 2 rows is used)
        **kwargs: additional parameters for the plotting backend

    Returns:
        ``matplotlib`` figure or ``plotly`` figure

    """
    resolved_backend = backend
    if interactive is not None:
        warn_once(
            "raw_plot(interactive=...)",
            'backend="plotly"|"matplotlib"',
            removal="2.1",
        )
        if resolved_backend is None:
            resolved_backend = "plotly" if interactive else "matplotlib"
    if resolved_backend is None:
        resolved_backend = "plotly"

    if resolved_backend == "plotly" and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        resolved_backend = "matplotlib"

    from cellpy.plotting.backends import get_backend
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.raw import RawPrepareConfig, prepare as prepare_raw

    prep_config = RawPrepareConfig(
        y=y,
        y_label=y_label,
        x=x,
        x_label=x_label,
        title=title,
        plot_type=plot_type,
        double_y=double_y,
        backend=resolved_backend,
        additional_kwargs=dict(kwargs),
    )
    ctx = from_source(cell)
    family = plot_registry.get("raw")
    frame, spec = prepare_raw(ctx, family, prep_config)
    if spec.extras.get("unsupported_plot_type"):
        return None
    fig = get_backend(resolved_backend).render(frame, spec)
    if resolved_backend == "matplotlib" and fig is not None:
        plt.close(fig)
    return fig


def cycle_info_plot(
    cell,
    cycle=None,
    get_axes=False,
    backend: Optional[str] = None,
    interactive: Optional[bool] = None,
    t_unit="hours",
    v_unit="V",
    i_unit="mA",
    **kwargs,
):
    """Show raw data together with step and cycle information.

    Draws through prepare → spec → render (#647).

    Args:
        cell: cellpy object
        cycle (int or list or tuple): cycle(s) to select (must be int for matplotlib)
        get_axes (bool): return axes (for matplotlib) or figure (for plotly)
        backend (str, optional): ``"plotly"`` (default) or ``"matplotlib"``.
        interactive (bool, optional): Deprecated alias for backend selection
            (``True``→plotly, ``False``→matplotlib; removal 2.1).
        t_unit (str): unit for x-axis (default: "hours")
        v_unit (str): unit for y-axis (default: "V")
        i_unit (str): unit for current (default: "mA")
        **kwargs: parameters specific to plotting backend.

    Returns:
        ``matplotlib.axes`` or None (or a figure when ``get_axes`` / backend semantics require it)
    """
    resolved_backend = backend
    if interactive is not None:
        warn_once(
            "cycle_info_plot(interactive=...)",
            'backend="plotly"|"matplotlib"',
            removal="2.1",
        )
        if resolved_backend is None:
            resolved_backend = "plotly" if interactive else "matplotlib"
    if resolved_backend is None:
        resolved_backend = "plotly"

    if resolved_backend == "plotly" and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        resolved_backend = "matplotlib"

    from cellpy.plotting.backends import get_backend
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.steps import (
        CycleInfoPrepareConfig,
        prepare as prepare_cycle_info,
    )

    prep_config = CycleInfoPrepareConfig(
        cycle=cycle,
        get_axes=get_axes,
        t_unit=t_unit,
        v_unit=v_unit,
        i_unit=i_unit,
        backend=resolved_backend,
        additional_kwargs=dict(kwargs),
    )
    ctx = from_source(cell)
    family = plot_registry.get("cycle_info")
    frame, spec = prepare_cycle_info(ctx, family, prep_config)
    fig = get_backend(resolved_backend).render(frame, spec)

    if resolved_backend == "plotly":
        if get_axes:
            return fig
        fig.show()
        return None

    # matplotlib: historical default returns None unless get_axes=True.
    if get_axes:
        return fig
    return None



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
    backend: Optional[str] = None,
    interactive: Optional[bool] = None,
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

    Draws through prepare → spec → render (#646).

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
        x_range (list, optional): Limits for the x-axis.
        y_range (list, optional): Limits for the y-axis.
        xlim (list, optional): Deprecated alias for ``x_range`` (removal 2.1).
        ylim (list, optional): Deprecated alias for ``y_range`` (removal 2.1).
        backend (str, optional): ``"plotly"`` (default) or ``"matplotlib"``.
        interactive (bool, optional): Deprecated alias for backend selection
            (``True``→plotly, ``False``→matplotlib; removal 2.1).
        return_figure (bool, optional): Whether to return the figure object.
            Default is ``True`` for matplotlib and ``False`` for plotly (``fig.show()``).
        width (int, optional): Width of the figure for Plotly. Default is 800.
        height (int, optional): Height of the figure for Plotly. Default is 600.
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
    # Resolve backend= vs deprecated interactive= (#646 / same as #639).
    resolved_backend = backend
    if interactive is not None:
        warn_once(
            "cycles_plot(interactive=...)",
            'backend="plotly"|"matplotlib"',
            removal="2.1",
        )
        if resolved_backend is None:
            resolved_backend = "plotly" if interactive else "matplotlib"
    if resolved_backend is None:
        resolved_backend = "plotly"

    if resolved_backend == "plotly" and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        resolved_backend = "matplotlib"

    if return_figure is None:
        return_figure = resolved_backend != "plotly"

    # Canonical range spelling: x_range/y_range; xlim/ylim are warn_once aliases.
    if xlim is not None:
        warn_once(
            "cycles_plot(xlim=...)",
            "cycles_plot(x_range=...)",
            removal="2.1",
        )
        if x_range is None:
            x_range = xlim
    if ylim is not None:
        warn_once(
            "cycles_plot(ylim=...)",
            "cycles_plot(y_range=...)",
            removal="2.1",
        )
        if y_range is None:
            y_range = ylim

    seaborn_context = kwargs.pop("seaborn_context", "notebook")
    seaborn_facecolor = kwargs.pop("seaborn_facecolor", "#EAEAF2")
    seaborn_edgecolor = kwargs.pop("seaborn_edgecolor", "black")
    seaborn_style_dict = kwargs.pop("seaborn_style_dict", None)

    from cellpy.plotting.backends import get_backend
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.curves import CyclesPrepareConfig, prepare as prepare_curves

    prep_config = CyclesPrepareConfig(
        cycles=cycles,
        inter_cycle_shift=inter_cycle_shift,
        cycle_mode=cycle_mode,
        formation_cycles=formation_cycles,
        show_formation=show_formation,
        mode=mode,
        method=method,
        interpolated=interpolated,
        number_of_points=number_of_points,
        colormap=colormap,
        formation_colormap=formation_colormap,
        cut_colorbar=cut_colorbar,
        title=title,
        figsize=figsize,
        x_range=x_range,
        y_range=y_range,
        width=width,
        height=height,
        marker_size=marker_size,
        formation_line_color=formation_line_color,
        force_colorbar=force_colorbar,
        force_nonbar=force_nonbar,
        plotly_template=plotly_template,
        seaborn_palette=seaborn_palette,
        seaborn_style=seaborn_style,
        seaborn_context=seaborn_context,
        seaborn_facecolor=seaborn_facecolor,
        seaborn_edgecolor=seaborn_edgecolor,
        seaborn_style_dict=seaborn_style_dict,
        backend=resolved_backend,
        additional_kwargs=dict(kwargs),
    )

    ctx = from_source(c)
    family = plot_registry.get("cycles")
    frame, spec = prepare_curves(ctx, family, prep_config)
    fig = get_backend(resolved_backend).render(frame, spec)

    if resolved_backend == "matplotlib" and (return_figure or return_data):
        plt.close(fig)

    if return_data:
        return fig, frame
    if return_figure:
        return fig
    if resolved_backend == "plotly":
        fig.show()
    return None


def _resolve_plot_backend(
    *,
    backend: Optional[str],
    interactive: Optional[bool],
    deprecation_site: str,
) -> str:
    """Resolve ``backend=`` vs deprecated ``interactive=`` for plot entry points."""
    resolved = backend
    if interactive is not None:
        warn_once(
            deprecation_site,
            'backend="plotly"|"matplotlib"',
            removal="2.1",
        )
        if resolved is None:
            resolved = "plotly" if interactive else "matplotlib"
    if resolved is None:
        resolved = "plotly"
    if resolved == "plotly" and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        resolved = "matplotlib"
    return resolved


def ica_plot(
    cell,
    cycles=None,
    direction="both",
    options=None,
    *,
    backend: Optional[str] = None,
    interactive: Optional[bool] = None,
    title=None,
    colormap="viridis",
    width=800,
    height=600,
    figsize=(6, 4),
    x_range=None,
    y_range=None,
    plotly_template=None,
    return_data=False,
    **kwargs,
):
    """Plot incremental capacity (dQ/dV vs voltage).

    Draws through prepare → spec → render (#648). Data come from
    [`cellpy.ica.dqdv`][cellpy.ica.dqdv]; both half-cycles are overlaid when
    ``direction="both"`` (plotly hover shows charge/discharge).

    Args:
        cell: cellpy object.
        cycles: Cycle number or list (``None`` = all).
        direction: ``"charge"``, ``"discharge"``, or ``"both"``.
        options: Optional [`IcaOptions`][cellpy.ica.IcaOptions].
        backend: ``"plotly"`` (default) or ``"matplotlib"``.
        interactive: Deprecated alias for backend selection (removal 2.1).
        title: Figure title.
        colormap: Cycle colour map.
        width, height: Plotly figure size.
        figsize: Matplotlib figure size.
        x_range, y_range: Optional axis ranges.
        plotly_template: Optional plotly template name.
        return_data: If True, return ``(figure, frame)``.
        **kwargs: Extra knobs (``strict``, ``cycle_mode``, ``number_of_points``,
            and individual ``IcaOptions`` field overrides).

    Returns:
        Plotly or matplotlib figure (or ``(figure, frame)`` when ``return_data``).
    """
    from cellpy.plotting.backends import get_backend
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.ica import IcaPrepareConfig, prepare as prepare_ica

    resolved_backend = _resolve_plot_backend(
        backend=backend,
        interactive=interactive,
        deprecation_site="ica_plot(interactive=...)",
    )

    option_keys = {
        "voltage_resolution",
        "capacity_resolution",
        "pre_smoothing",
        "diff_smoothing",
        "post_smoothing",
        "savgol_window_divisor",
        "savgol_order",
        "voltage_fwhm",
        "capacity_fwhm",
        "gaussian",
        "normalize",
        "normalizing_factor",
        "normalizing_roof",
        "increment_method",
    }
    option_overrides = {k: kwargs.pop(k) for k in list(kwargs) if k in option_keys}
    strict = kwargs.pop("strict", False)
    cycle_mode = kwargs.pop("cycle_mode", None)
    number_of_points = kwargs.pop("number_of_points", None)

    prep_config = IcaPrepareConfig(
        derivative="dqdv",
        cycles=cycles,
        direction=direction,
        options=options,
        strict=strict,
        cycle_mode=cycle_mode,
        number_of_points=number_of_points,
        title=title,
        colormap=colormap,
        width=width,
        height=height,
        figsize=figsize,
        x_range=x_range,
        y_range=y_range,
        plotly_template=plotly_template,
        backend=resolved_backend,
        option_overrides=option_overrides,
        additional_kwargs=dict(kwargs),
    )
    ctx = from_source(cell)
    family = plot_registry.get("ica")
    frame, spec = prepare_ica(ctx, family, prep_config)
    fig = get_backend(resolved_backend).render(frame, spec)
    if resolved_backend == "matplotlib" and fig is not None:
        plt.close(fig)
    if return_data:
        return fig, frame
    return fig


def dva_plot(
    cell,
    cycles=None,
    direction="both",
    options=None,
    *,
    backend: Optional[str] = None,
    interactive: Optional[bool] = None,
    title=None,
    colormap="viridis",
    width=800,
    height=600,
    figsize=(6, 4),
    x_range=None,
    y_range=None,
    plotly_template=None,
    return_data=False,
    **kwargs,
):
    """Plot differential voltage analysis (dV/dQ vs capacity).

    Draws through prepare → spec → render (#648). Data come from
    [`cellpy.ica.dvdq`][cellpy.ica.dvdq]; both half-cycles are overlaid when
    ``direction="both"`` (plotly hover shows charge/discharge).

    Args:
        cell: cellpy object.
        cycles: Cycle number or list (``None`` = all).
        direction: ``"charge"``, ``"discharge"``, or ``"both"``.
        options: Optional [`IcaOptions`][cellpy.ica.IcaOptions] (defaults to
            DVA-oriented options inside ``dvdq``).
        backend: ``"plotly"`` (default) or ``"matplotlib"``.
        interactive: Deprecated alias for backend selection (removal 2.1).
        title: Figure title.
        colormap: Cycle colour map.
        width, height: Plotly figure size.
        figsize: Matplotlib figure size.
        x_range, y_range: Optional axis ranges.
        plotly_template: Optional plotly template name.
        return_data: If True, return ``(figure, frame)``.
        **kwargs: Extra knobs (``strict``, ``cycle_mode``, ``number_of_points``,
            and individual ``IcaOptions`` field overrides).

    Returns:
        Plotly or matplotlib figure (or ``(figure, frame)`` when ``return_data``).
    """
    from cellpy.plotting.backends import get_backend
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.ica import IcaPrepareConfig, prepare as prepare_ica

    resolved_backend = _resolve_plot_backend(
        backend=backend,
        interactive=interactive,
        deprecation_site="dva_plot(interactive=...)",
    )

    option_keys = {
        "voltage_resolution",
        "capacity_resolution",
        "pre_smoothing",
        "diff_smoothing",
        "post_smoothing",
        "savgol_window_divisor",
        "savgol_order",
        "voltage_fwhm",
        "capacity_fwhm",
        "gaussian",
        "normalize",
        "normalizing_factor",
        "normalizing_roof",
        "increment_method",
    }
    option_overrides = {k: kwargs.pop(k) for k in list(kwargs) if k in option_keys}
    strict = kwargs.pop("strict", False)
    cycle_mode = kwargs.pop("cycle_mode", None)
    number_of_points = kwargs.pop("number_of_points", None)

    prep_config = IcaPrepareConfig(
        derivative="dvdq",
        cycles=cycles,
        direction=direction,
        options=options,
        strict=strict,
        cycle_mode=cycle_mode,
        number_of_points=number_of_points,
        title=title,
        colormap=colormap,
        width=width,
        height=height,
        figsize=figsize,
        x_range=x_range,
        y_range=y_range,
        plotly_template=plotly_template,
        backend=resolved_backend,
        option_overrides=option_overrides,
        additional_kwargs=dict(kwargs),
    )
    ctx = from_source(cell)
    family = plot_registry.get("dva")
    frame, spec = prepare_ica(ctx, family, prep_config)
    fig = get_backend(resolved_backend).render(frame, spec)
    if resolved_backend == "matplotlib" and fig is not None:
        plt.close(fig)
    if return_data:
        return fig, frame
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
