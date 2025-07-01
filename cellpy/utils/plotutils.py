# -*- coding: utf-8 -*-
"""
Utilities for helping to plot cellpy-data.
"""

import collections
import importlib
import itertools
import logging
from multiprocessing import Process
import os
import pickle as pkl
import sys
from typing import Any, Callable, Optional
import warnings
from io import StringIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from cellpy.parameters.internal_settings import (
    get_headers_journal,
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
)
from cellpy.utils import helpers

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
                if ipython is not None and hasattr(ipython, 'kernel'):
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
def load_figure(filename, backend=None):
    """Load figure from file."""

    filename = Path(filename)

    if backend is None:
        suffix = filename.suffix
        if suffix in [".pkl", ".pickle"]:
            backend = "matplotlib"
        elif suffix in [".json", ".plotly", ".jsn"]:
            backend = "plotly"
        else:
            backend = "plotly"

    if backend == "plotly":
        return load_plotly_figure(filename)
    elif backend == "seaborn":
        return load_matplotlib_figure(filename)
    elif backend == "matplotlib":
        return load_matplotlib_figure(filename)
    else:
        print(f"WARNING: {backend=} is not supported at the moment")
        return None


def save_matplotlib_figure(fig, filename):
    pkl.dump(fig, open(filename, "wb"))


def make_matplotlib_manager(fig):
    """Create a new manager for a matplotlib figure."""
    # create a dummy figure and use its
    # manager to display "fig"  ; based on https://stackoverflow.com/a/54579616/8508004
    dummy = plt.figure()
    new_manager = dummy.canvas.manager
    new_manager.canvas.figure = fig
    fig.set_canvas(new_manager.canvas)
    return fig


def load_matplotlib_figure(filename, create_new_manager=False):
    fig = pkl.load(open(filename, "rb"))
    if create_new_manager:
        fig = make_matplotlib_manager(fig)
    return fig


def load_plotly_figure(filename):
    """Load plotly figure from file."""

    # TODO: create a decorator for this:
    if not plotly_available:
        print("Plotly not available")
        return None
    import plotly.io as pio

    try:
        fig = pio.read_json(filename)
    except Exception as e:
        print("Could not load figure from json file")
        print(e)
        return None
    return fig


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
def save_image_files(figure: Any, name: str = "my_figure", scale: float = 3.0, dpi: int = 300, backend: str = "plotly", formats: Optional[list] = None):
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


def _make_plotly_template(name="axis"):
    if not plotly_available:
        print("Plotly not available")
        return None
    import plotly.graph_objects as go
    import plotly.io as pio

    tick_label_width = 6
    title_font_size = 22
    title_font_family = "Arial"
    axis_font_size = 16
    axis_standoff = 15
    linecolor = "rgb(36,36,36)"

    t = go.layout.Template(
        layout=dict(
            font_family=title_font_family,
            title=dict(
                font_size=title_font_size,
                x=0,
                xref="paper",
            ),
            xaxis=dict(
                linecolor=linecolor,
                mirror=True,
                showline=True,
                zeroline=False,
                title=dict(
                    standoff=axis_standoff,
                    font_size=axis_font_size,
                ),
            ),
            yaxis=dict(
                linecolor=linecolor,
                mirror=True,
                showline=True,
                zeroline=False,
                tickformat=f"{tick_label_width}",
                title=dict(
                    standoff=axis_standoff,
                    font_size=axis_font_size,
                ),
            ),
        )
    )
    pio.templates[name] = t


# from batch_plotters:
def _plotly_remove_markers(trace):
    trace.update(marker=None, mode="lines")
    return trace


def _plotly_legend_replacer(trace, df, group_legends=True):
    name = trace.name
    parts = name.split(",")
    if len(parts) == 2:
        group = int(parts[0])
        subgroup = int(parts[1])
    else:
        print("Have not implemented replacing legend labels that are not on the form a,b yet.")
        print(f"legend label: {name}")
        return trace

    cell_label = df.loc[(df["group"] == group) & (df["sub_group"] == subgroup), "cell"].values[0]
    if group_legends:
        trace.update(
            name=cell_label,
            legendgroup=group,
            hovertemplate=f"{cell_label}<br>{trace.hovertemplate}",
        )
    else:
        trace.update(
            name=cell_label,
            legendgroup=cell_label,
            hovertemplate=f"{cell_label}<br>{trace.hovertemplate}",
        )


import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

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


_hdr_summary = get_headers_summary()
_hdr_raw = get_headers_normal()
_hdr_steps = get_headers_step_table()
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
    pio.templates[name] = go.layout.Template(layout=dict(title=title, xaxis=axis, yaxis=axis), data=data)
    return name


def create_colormarkerlist_for_journal(journal, symbol_label="all", color_style_label="seaborn-colorblind"):
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


def create_colormarkerlist(groups, sub_groups, symbol_label="all", color_style_label="seaborn-colorblind"):
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


def create_col_info(c: Any) -> tuple[tuple, dict, dict, dict]:
    """Create column information for summary plots.

    This function is called by summary_plot together with create_label_dict. The two functions need to be updated together.
    Not optimal. So feel free to refactor it.

    Args:
        c: cellpy object

    Returns:
        x_columns (tuple), y_cols (dict), x_transformations (dict), y_transformations (dict)

    """
    
    def _normalize_col(x: np.ndarray, normalization_factor: float = 1.0, normalization_type: str = "max", normalization_scaler: float = 1.0) -> np.ndarray:
        # a bit random collection of normalization types...

        if normalization_type == "divide":
            return (x / normalization_factor) * normalization_scaler
        elif normalization_type == "shift-divide":
            return ((normalization_factor - x) / normalization_factor) * normalization_scaler
        elif normalization_type == "multiply":
            return (x * normalization_factor) * normalization_scaler
        elif normalization_type == "area":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                area = np.trapzoid(x, dx=1)
            return (x / area / normalization_factor) * normalization_scaler
        elif normalization_type == "max":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                x_max = x.max()
            return (x / x_max / normalization_factor) * normalization_scaler
        else:
            raise ValueError(f"Invalid normalization type: {normalization_type}")

    hdr = c.headers_summary
    _cap_cols = [hdr.charge_capacity_raw, hdr.discharge_capacity_raw]
    _capacities_gravimetric = [col + "_gravimetric" for col in _cap_cols]
    _capacities_gravimetric_split = (
        _capacities_gravimetric
        + [col + "_cv" for col in _capacities_gravimetric]
        + [col + "_non_cv" for col in _capacities_gravimetric]
    )
    _capacities_areal = [col + "_areal" for col in _cap_cols]
    _capacities_areal_split = (
        _capacities_areal + [col + "_cv" for col in _capacities_areal] + [col + "_non_cv" for col in _capacities_areal]
    )
    _capacities_absolute = [col + "_absolute" for col in _cap_cols]
    _capacities_absolute_split = (
        _capacities_absolute
        + [col + "_cv" for col in _capacities_absolute]
        + [col + "_non_cv" for col in _capacities_absolute]
    )

    x_columns = (
        [
            hdr.cycle_index,
            hdr.data_point,
            hdr.test_time,
            hdr.datetime,
            hdr.normalized_cycle_index,
        ],
    )
    y_cols = dict(
        voltages=[hdr.end_voltage_charge, hdr.end_voltage_discharge],
        capacities_gravimetric=_capacities_gravimetric,
        capacities_areal=_capacities_areal,
        capacities_absolute=_capacities_absolute,
        capacities=_cap_cols,
        capacities_gravimetric_split_constant_voltage=_capacities_gravimetric_split,
        capacities_areal_split_constant_voltage=_capacities_areal_split,
        capacities_gravimetric_coulombic_efficiency=_capacities_gravimetric + [hdr.coulombic_efficiency],
        capacities_areal_coulombic_efficiency=_capacities_areal + [hdr.coulombic_efficiency],
        capacities_absolute_coulombic_efficiency=_capacities_absolute + [hdr.coulombic_efficiency],

        fullcell_standard_cumloss_gravimetric=[
            hdr.charge_capacity+"_gravimetric" + "_cv",
            hdr.cumulated_discharge_capacity_loss + "_gravimetric",
            hdr.discharge_capacity+"_gravimetric",
            hdr.coulombic_efficiency,
            ],
        fullcell_standard_cumloss_areal=[
            hdr.charge_capacity+"_areal" + "_cv",
            hdr.cumulated_discharge_capacity_loss + "_areal",
            hdr.discharge_capacity+"_areal",
            hdr.coulombic_efficiency,
            ],
        fullcell_standard_cumloss_absolute=[
            hdr.charge_capacity+"_absolute" + "_cv",
            hdr.cumulated_discharge_capacity_loss + "_absolute",
            hdr.discharge_capacity+"_absolute",
            hdr.coulombic_efficiency,
            ],
        fullcell_standard_gravimetric=[
            hdr.charge_capacity+"_gravimetric" + "_cv",
            hdr.discharge_capacity + "_gravimetric",
            "mod_01_"+hdr.discharge_capacity+"_gravimetric",
            hdr.coulombic_efficiency,
            ],
        fullcell_standard_areal=[
            hdr.charge_capacity+"_areal" + "_cv",
            hdr.discharge_capacity + "_areal",
            "mod_01_"+hdr.discharge_capacity+"_areal",
            hdr.coulombic_efficiency,
            ],
        fullcell_standard_absolute=[
            hdr.charge_capacity+"_absolute" + "_cv",
            hdr.discharge_capacity + "_absolute",
            "mod_01_"+hdr.discharge_capacity+"_absolute",
            hdr.coulombic_efficiency,
            ],
        fullcell_standard_dev=[
            hdr.charge_capacity+"_gravimetric" + "_cv",
            hdr.discharge_capacity + "_gravimetric",
            hdr.coulombic_efficiency,
            "mod_01_"+hdr.discharge_capacity+"_gravimetric",
            ],
    )

    x_transformations = dict(
    )

        
    # transformation info on the form: column_name: {(row_number, new_column_name): transformation_function}
    y_transformations: dict[str, dict[tuple[int, str], dict[str, Callable]]] = dict(
        fullcell_standard_cumloss_gravimetric={
            hdr.cumulated_discharge_capacity_loss + "_gravimetric": {
                (2, hdr.cumulated_discharge_capacity_loss + "_gravimetric"): _normalize_col
                },
        },
        fullcell_standard_cumloss_areal={
            hdr.cumulated_discharge_capacity_loss + "_areal": {
                (2, hdr.cumulated_discharge_capacity_loss + "_areal"): _normalize_col
                },
        },
        fullcell_standard_cumloss_absolute={
            hdr.cumulated_discharge_capacity_loss + "_absolute": {
                (2, hdr.cumulated_discharge_capacity_loss + "_absolute"): _normalize_col
                },
        },
        fullcell_standard_gravimetric={
            "mod_01_"+hdr.discharge_capacity+"_gravimetric": {
                (2, hdr.discharge_capacity + "_retention" + "_gravimetric"): _normalize_col
                },
        },
        fullcell_standard_areal={
            "mod_01_"+hdr.discharge_capacity+"_areal": {
                (2, hdr.discharge_capacity + "_retention" + "_areal"): _normalize_col
                },
        },
        fullcell_standard_absolute={
            "mod_01_"+hdr.discharge_capacity+"_absolute": {
                (2, hdr.discharge_capacity + "_retention" + "_absolute"): _normalize_col
                },
        },
        fullcell_standard_dev={
            "mod_01_"+hdr.discharge_capacity+"_gravimetric": {
                (2, hdr.discharge_capacity + "_retention" + "_gravimetric"): _normalize_col
                },
        },
    )

    return x_columns, y_cols, x_transformations, y_transformations


def create_label_dict(c):
    """Create label dictionary for summary plots.

    This function is called by summary_plot together with create_col_info. The two functions need to be updated together.
    Not optimal. So feel free to refactor it.

    Args:
        c: cellpy object

    Returns:
        x_axis_labels (dict), y_axis_label (dict)

    """

    hdr = c.headers_summary
    x_axis_labels = {
        hdr.cycle_index: "Cycle Number",
        hdr.data_point: "Point",
        hdr.test_time: f"Test Time ({c.cellpy_units.time})",
        hdr.datetime: "Date",
        hdr.normalized_cycle_index: "Equivalent Full Cycle",  # hdr.normalized_cycle_index: "Normalized Cycle Number",
    }

    _cap_gravimetric_label = f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_gravimetric})"
    _cap_areal_label = f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_areal})"
    _cap_absolute_label = f"Capacity ({c.cellpy_units.charge})"
    _cap_label = f"Capacity ({c.data.raw_units.charge})"

    y_axis_label = {
        "voltages": f"Voltage ({c.cellpy_units.voltage})",
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
        "fullcell_standard_gravimetric": _cap_gravimetric_label,
        "fullcell_standard_areal": _cap_areal_label,
        "fullcell_standard_absolute": _cap_absolute_label,
    }
    return x_axis_labels, y_axis_label


def _get_capacity_unit(c, mode="gravimetric", seperator="/"):
    specific_selector = {
        "gravimetric": f"{c.cellpy_units.charge}{seperator}{c.cellpy_units.specific_gravimetric}",
        "areal": f"{c.cellpy_units.charge}{seperator}{c.cellpy_units.specific_areal}",
        "volumetric": f"{c.cellpy_units.charge}{seperator}{c.cellpy_units.specific_volumetric}",
        "absolute": f"{c.cellpy_units.charge}",
    }
    return specific_selector.get(mode, "-")


# TODO: consistent parameter names (e.g. y_range vs ylim) between summary_plot, plot_cycles, raw_plot, cycle_info_plot and batchutils
# TODO: consistent function names (raw_plot vs plot_raw etc)
@notebook_docstring_printer
def summary_plot(
    c,
    x: Optional[str] = None,
    y: str = "capacities_gravimetric_coulombic_efficiency",  # Consider setting default to 'fullcell_standard_gravimetric'
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
    """Create a summary plot.

    Args:
        c: cellpy object
        x: x-axis column (default: 'cycle_index')
        y: y-axis column or column set. Currently, the following predefined sets exists:
            "voltages", "capacities_gravimetric", "capacities_areal", "capacities_absolute",
            "capacities_gravimetric_split_constant_voltage", "capacities_areal_split_constant_voltage",
            "capacities_gravimetric_coulombic_efficiency", "capacities_areal_coulombic_efficiency",
            "capacities_absolute_coulombic_efficiency",
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
        auto_convert_legend_labels: convert the legend labels to a nicer format.
        interactive: use interactive plotting (plotly)
        rangeslider: add a range slider to the x-axis (only for plotly)
        share_y: share y-axis (only for plotly)
        return_data: return the data used for plotting
        verbose: print out some extra information to make it easier to find out what to plot next time
        plotly_template: name of the plotly template to use
        seaborn_palette: name of the seaborn palette to use
        seaborn_style: name of the seaborn style to use
        formation_cycles: number of formation cycles to show
        show_formation: show formation cycles
        show_legend: show the legend
        x_axis_domain_formation_fraction: fraction of the x-axis domain for the formation cycles (default: 0.2)
        column_separator: separation between columns when splitting the plot (only for plotly)
        reset_losses: reset the losses to the first cycle (only for fullcell_standard plots)
        link_capacity_scales: link the capacity scales (only for fullcell_standard plots)
        fullcell_standard_normalization_type: normalization type for the fullcell standard plots (capacity retention) 
            (divide, multiply, area, max, on-max, False)
            if normalization_type is on-max, the normalization factor is set to the maximum value of the capacity column if not provided
            if normalization_type is max, the normalization factor is set to the maximum value of the capacity column if not provided
            if normalization_type is shift-divide, the normalization is done by shifting the data by the normalization factor and 
            then dividing by the normalization factor
            if normalization_type is divide, the normalization is done by dividing by the normalization factor and 
            then multiplying by the scaler
            if normalization_type is multiply, the normalization is done by multiplying by the normalization factor 
            and then multiplying by the scaler
            if normalization_type is area, the normalization is done by dividing by the area and then multiplying by the scaler
            if normalization_type is False, no normalization is done
        fullcell_standard_normalization_factor: normalization factor for the fullcell standard plots
        fullcell_standard_normalization_scaler: scaler for the fullcell standard plots
        plotly_[update trace parameter]: additional parameters for the plotly traces
            (e.g. use plotly_marker_size=10 for updating the marker_size to 10)
        seaborn_[update line parameter]: additional parameters for the seaborn lines (not many options available yet)
            (e.g. use seaborn_marker_size=10 for updating the marker_size to 10)
        seaborn_line_hooks: list of functions to hook into the seaborn lines (e.g. to update the marker_size)
        **kwargs: includes additional parameters for the plotting backend (not properly documented yet).

    Returns:
        if ``return_data`` is True, returns a tuple with the figure and the data used for plotting.
        Otherwise, it returns only the figure. If ``interactive`` is True, the figure is a ``plotly`` figure,
        else it is a ``matplotlib`` figure.

    Hint:
        If you want to modify the non-interactive (matplotlib) plot, you can get the axes from the
        returned figure by ``axes = figure.get_axes()``:

        >> axes = figure.get_axes()
        >> ylabel = axes[0].get_ylabel()
        >> if "Coulombic" in ylabel:
        >>     axes[0].set_ylabel("C.E. (%)")
        >> else:
        >>     print(f"This is not the coulombic efficiency axis: {ylabel=}")


    """
    from copy import deepcopy
    import re

    dev_mode = kwargs.pop("dev_mode", False)
    if dev_mode:
        print("DEV: dev_mode")

    smart_link = kwargs.pop("smart_link", True)
    show_y_labels_on_right_pane = kwargs.pop("show_y_labels_on_right_pane", False)
    seaborn_facecolor = kwargs.pop("seaborn_facecolor", "#EAEAF2")
    seaborn_edgecolor = kwargs.pop("seaborn_edgecolor", "black")
    seaborn_style_dict_default = {"axes.facecolor": seaborn_facecolor, "axes.edgecolor": seaborn_edgecolor}
    seaborn_style_dict = kwargs.pop("seaborn_style_dict", seaborn_style_dict_default)
    seaborn_marker_size = kwargs.pop("seaborn_marker_size", 7)

    # only used for fullcell_standard plots in interactive mode for now
    plotly_row_ratios = kwargs.pop("fullcell_standard_row_height_ratios", [0.3, 0.6, 0.9])
    plotly_row_space = kwargs.pop("fullcell_standard_row_space", 0.02)
    # fullcell_standard does not respect the split parameter
    if y.startswith("fullcell_standard_") and not split:
        logging.debug("fullcell_standard does not respect the split parameter")

    number_of_rows = 1
    max_val_normalized_col = 0.0

    if interactive and not plotly_available:
        warnings.warn("plotly not available, and it is currently the only supported interactive backend")
        return None

    if title is None:
        if interactive:
            title = f"Summary <b>{c.cell_name}</b>"
        else:
            title = f"Summary {c.cell_name}"

    if x is None:
        x = "cycle_index"
    xlim_formation = kwargs.pop("xlim_formation", (0.6, formation_cycles + 0.4))

    eff_lim = ce_range

    if formation_cycles < 1:
        show_formation = False

    x_cols, y_cols, x_trans, y_trans = create_col_info(c)
    x_axis_labels, y_axis_label = create_label_dict(c)


    def _auto_range(fig: Any, axis_name_1: str, axis_name_2: str) -> list:
        # only works for plotly
        min_y = np.inf
        max_y = -np.inf
        full_axis_name_1 = axis_name_1.replace("y", "yaxis")
        full_axis_name_2 = axis_name_2.replace("y", "yaxis")

        _range_1 = fig.layout[f"{full_axis_name_1}_range"]
        _range_2 = fig.layout[f"{full_axis_name_2}_range"]
        if _range_1 is None:
            _range_1 = [np.inf, -np.inf]
        if _range_2 is None:
            _range_2 = [np.inf, -np.inf]
        _range = [min(_range_1[0], _range_2[0]), max(_range_1[1], _range_2[1])]

        for i,t in enumerate(deepcopy(fig.data)):
            if t.yaxis in [axis_name_1, axis_name_2]:
                y = deepcopy(t.y)
                try:
                    y = np.array(y, dtype=float)
                    min_y = np.ma.masked_invalid(y).min()
                    max_y = np.ma.masked_invalid(y).max()
                except Exception as e:
                    warnings.warn(f"Could not calculate min and max for y-axis (data set {i}): {e}")

                _range = [min(_range[0], min_y), max(_range[1], max_y)]
        _range = [0.95 * _range[0], 1.05 * _range[1]]
        return _range
    

    y_header = "value"
    color = "variable"
    row = "row"
    col_id = "cycle_type"
    additional_kwargs_plotly = dict(
        color=color,
        height=height,
        markers=markers,
        title=title,
        width=width,
    )

    additional_kwargs_plotly_update_traces = dict()
    for k in list(kwargs.keys()):
        if k.startswith("plotly_"):
            additional_kwargs_plotly_update_traces[k.replace("plotly_", "")] = kwargs.pop(k)

    additional_kwargs_seaborn = dict()

    # ------------------- collecting data -----------------------------------------

    if y.startswith("fullcell_standard_"):
        if additional_kwargs_plotly.get("height") is None:
            additional_kwargs_plotly["height"] = 800
        column_set = y_cols.get(y, y)

        summary = c.data.summary.copy()
        if summary.index.name == x:
            summary = summary.reset_index(drop=False)

        # Remark! Possible code duplication with the 'partition_summary_cv_steps' used in 
        # the 'if y.endswith("_split_constant_voltage")' block:
        summary_only_cv = c.make_summary(selector_type="only-cv", create_copy=True).data.summary
        if summary_only_cv.index.name == x:
            summary_only_cv = summary_only_cv.reset_index(drop=False)

        s = summary.merge(summary_only_cv, on=x, how="outer", suffixes=("", "_cv"))

        s = s.reset_index(drop=True)
        s = s.melt(x)
        s = s.loc[s.variable.isin(column_set)]  # using strickt naming convention for "duplicated" columns ('mod_<nn>_<column_name>' so it will not be picked up here)

        number_of_rows = 4
        s[row] = 1  # default row for capacity
        # Set row numbers using regex patterns
        s.loc[s["variable"].str.contains(r"_efficiency$"), row] = 0  # coulombic efficiency
        s.loc[s["variable"].str.contains(r"cumulated.*loss"), row] = 2  # cumulated loss [will be removed?]
        s.loc[s["variable"].str.startswith(r"mod_01_"), row] = 2  # capacity retention
        s.loc[s["variable"].str.contains(r"_cv$"), row] = 3  # cv data
        additional_kwargs_plotly["facet_row"] = row

        if reset_losses:
            # Get the first value for each cumulated loss variable
            first_values = s[s["variable"].str.contains(r"cumulated.*loss")].groupby("variable")["value"].transform("first")
            # Shift all values by subtracting the first value
            mask = s["variable"].str.contains(r"cumulated.*loss")
            s.loc[mask, "value"] = s.loc[mask, "value"] - first_values


        if fullcell_standard_normalization_type is not False:
            
            if fullcell_standard_normalization_factor is None:

                # need a special case for the cumloss plots
                if y.startswith("fullcell_standard_cumloss_"):
                    print("only allowing for 'divide' for cumloss plots")
                    fullcell_standard_normalization_factor = s[s[row] == 1].max().value
                    fullcell_standard_normalization_type = "divide"

                else:
                    if fullcell_standard_normalization_type == "on-max":
                        fullcell_standard_normalization_factor = s[s[row] == 1].max().value
                        fullcell_standard_normalization_type = "shift-divide"

                    elif fullcell_standard_normalization_type == "max":
                        fullcell_standard_normalization_factor = s[s[row] == 1].max().value
                        fullcell_standard_normalization_type = "shift-divide"

                    elif fullcell_standard_normalization_type == "area":
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            area = np.trapezoid(s[s[row] == 1].value, dx=1)
                        fullcell_standard_normalization_factor = area
                        fullcell_standard_normalization_type = "shift-divide"

                    else:
                        fullcell_standard_normalization_factor = 1.0

            trans_kwargs = dict(
                normalization_factor=fullcell_standard_normalization_factor,
                normalization_type=fullcell_standard_normalization_type,
                normalization_scaler=fullcell_standard_normalization_scaler,
            )


            # transform the data
            max_row_val = s[row].max()
            for col, trans_dict in y_trans.get(y, {}).items():
                
                for (new_row_val, new_col), trans in trans_dict.items():

                    if new_col in s["variable"].values:
                        # transforming on existing column (not using the new_row_val)
                        s.loc[s["variable"] == col, "value"] = trans(s.loc[s["variable"] == col, "value"].values, **trans_kwargs)
                    else:
                        # creating new column (using the new_row_val)
                        old_col = col
                        if new_row_val is not None:
                            row_val = new_row_val
                        else:
                            row_val = s.loc[s["variable"] == col, row]
                            if not row_val.empty:
                                row_val = row_val.values[0]
                            else:
                                max_row_val += 1
                                row_val = max_row_val
                        
                        if old_col.startswith("mod_"):
                            old_col = re.sub(r'^mod_\d{2}_', '', old_col)
                        new_col_frame_section = s.loc[s["variable"] == old_col].copy()
                        new_col_frame_section["variable"] = new_col
                        new_col_frame_section["row"] = row_val
                        transformed_values = trans(new_col_frame_section["value"].values, **trans_kwargs)
                        new_col_frame_section["value"] = transformed_values
                        s = pd.concat([s, new_col_frame_section], ignore_index=True)
                        s = s.reset_index(drop=True)
                        s = s.sort_values(by=["row", "variable"])

                    max_val_normalized_col = s.loc[s["variable"] == new_col, "value"].max()

    # filter on constant voltage vs constant current
    # Remark! uses the 'partition_summary_cv_steps' function - consider using that also for the fullcell standard plot to avoid code duplication
    elif y.endswith("_split_constant_voltage"):
        cap_type = "capacities_gravimetric" if y.startswith("capacities_gravimetric") else "capacities_areal"
        column_set = y_cols[cap_type]

        # turning off warnings when splitting the data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = partition_summary_cv_steps(c, x, column_set, split, color, y_header)
        if split:
            additional_kwargs_plotly["facet_row"] = row
            number_of_rows = 3
            if additional_kwargs_plotly.get("height") is None:
                additional_kwargs_plotly["height"] = 800

    else:
        column_set = y_cols.get(y, y)
        if isinstance(column_set, str):
            column_set = [column_set]
        summary = c.data.summary
        summary = summary.reset_index()
        s = summary.melt(x)
        s = s.loc[s.variable.isin(column_set)]
        s = s.reset_index(drop=True)
        s[row] = 1
        if split:
            if y.endswith("_efficiency"):
                s[row] = 1
                s.loc[s["variable"].str.contains("efficiency"), row] = 0
                additional_kwargs_plotly["facet_row"] = row
                number_of_rows = 2

        if additional_kwargs_plotly.get("height") is None:
            additional_kwargs_plotly["height"] = 200 + 200 * number_of_rows

    max_cycle = s[x].max()
    min_cycle = s[x].min()

    x_label = x_axis_labels.get(x, x)
    if y in y_axis_label:
        y_label = y_axis_label.get(y, y)
    else:
        y_label = y.replace("_", " ").title()

    if split and show_formation and not smart_link:
        column_separator = max(column_separator, 0.06)
        show_y_labels_on_right_pane = True

    formation_cycle_selector = slice(None, None)
    if formation_cycles > 0:
        formation_cycle_selector = s[x] <= formation_cycles
        s[col_id] = "standard"
        s.loc[formation_cycle_selector, col_id] = "formation"

    if verbose or dev_mode:
        _report_summary_plot_info(c, x, y, x_label, x_axis_labels, x_cols, y_label, y_axis_label, y_cols)

    if interactive:
        import plotly.express as px
        # from plotly.subplots import make_subplots

        set_plotly_template(plotly_template)

        if show_formation:
            additional_kwargs_plotly["facet_col"] = col_id

        fig = px.line(
            s,
            x=x,
            y=y_header,
            **additional_kwargs_plotly,
            labels={
                x: x_label,
                y_header: y_label,
            },
            **kwargs,
        )

        fig.update_traces(**additional_kwargs_plotly_update_traces)
        if not show_legend:
            fig.update_layout(showlegend=False)

        if y_range is not None:
            fig.update_layout(yaxis=dict(range=y_range))

        if show_formation:
            formation_header = '<span style="color:red">Formation</span>'
            x_axis_domain_formation = [0.0, x_axis_domain_formation_fraction - column_separator / 2]
            x_axis_domain_rest = [x_axis_domain_formation_fraction + column_separator / 2, 0.95]
            max_cycle_formation = s.loc[formation_cycle_selector, x].max()
            min_cycle_rest = s.loc[~formation_cycle_selector, x].min()
            if x == _hdr_summary.normalized_cycle_index:
                dd = 0.1
            else:
                dd = 0.4
            x_axis_range_formation = [min_cycle - dd, max_cycle_formation + dd]
            x_axis_range_rest = [min_cycle_rest - dd, max_cycle + dd]

            if x_range is not None:
                x_axis_range_rest = [x_axis_range_rest[0], min(x_range[1], x_axis_range_rest[1])]

            if number_of_rows == 1:
                fig.update_layout(
                    xaxis_domain=x_axis_domain_formation,
                    scene_domain_x=x_axis_domain_formation,
                    xaxis=dict(range=x_axis_range_formation),
                    xaxis2=dict(
                        range=x_axis_range_rest,
                        domain=x_axis_domain_rest,
                        matches=None,
                    ),
                )
                annotations = [{"text": formation_header, "x": 0.08, "y": 1.02, "showarrow": False}, PLOTLY_BLANK_LABEL]
                fig.update_layout(annotations=annotations)
                fig.update_layout(yaxis2=dict(matches="y", showticklabels=show_y_labels_on_right_pane),)

            elif number_of_rows == 2:
                fig.update_yaxes(matches="y")
                fig.update_yaxes(autorange=False)
                if y.endswith("_efficiency"):
                    fig.update_layout(
                        yaxis3={"title": dict(text="Coulombic Efficiency"), "domain": [0.7, 1.0]},
                        yaxis1=dict(domain=[0.0, 0.65]),
                        yaxis2=dict(domain=[0.0, 0.65]),
                        yaxis4=dict(domain=[0.70, 1.0]),
                    )

                fig.update_layout(xaxis_domain=x_axis_domain_formation, scene_domain_x=x_axis_domain_formation)
                range_1 = y_range or _auto_range(fig, "y", "y2")
                range_2 = eff_lim or _auto_range(fig, "y3", "y4")
                # seems to be problematic for plotly having a range_2 that is [value, inf] ([87.0012, inf])
                fig.update_layout(
                    xaxis2=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches=None),
                    xaxis3=dict(range=x_axis_range_formation, domain=x_axis_domain_formation, matches="x"),
                    xaxis4=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches="x2"),
                    yaxis=dict(
                        matches="y2",
                        range=range_1,
                    ),
                    yaxis2=dict(
                        matches="y",
                        showticklabels=show_y_labels_on_right_pane,
                        range=range_1,
                    ),
                    yaxis3=dict(
                        matches="y4",
                        range=range_2,
                    ),
                    yaxis4=dict(
                        matches="y3",
                        showticklabels=show_y_labels_on_right_pane,
                        range=range_2,
                    ),
                )
                annotations = [_plotly_label_dict(formation_header, 0.08, 1.0)] + 3 * [PLOTLY_BLANK_LABEL]
                fig.layout["annotations"] = annotations

            elif number_of_rows == 3:
                fig.update_yaxes(matches="y")
                fig.update_yaxes(autorange=False)
                fig.update_layout(xaxis_domain=x_axis_domain_formation, scene_domain_x=x_axis_domain_formation)

                range_1 = _auto_range(fig, "y", "y2")
                range_2 = _auto_range(fig, "y3", "y4")
                range_3 = _auto_range(fig, "y5", "y6")

                fig.update_layout(
                    xaxis2=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches=None),
                    xaxis3=dict(range=x_axis_range_formation, domain=x_axis_domain_formation, matches="x"),
                    xaxis4=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches="x2"),
                    xaxis5=dict(range=x_axis_range_formation, domain=x_axis_domain_formation, matches="x"),
                    xaxis6=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches="x2"),
                    yaxis=dict(matches="y2", range=range_1),
                    yaxis2=dict(matches="y", showticklabels=show_y_labels_on_right_pane, range=range_1),
                    yaxis3=dict(matches="y4", range=range_2),
                    yaxis4=dict(matches="y3", showticklabels=show_y_labels_on_right_pane, range=range_2),
                    yaxis5=dict(matches="y6", range=range_3),
                    yaxis6=dict(matches="y5", showticklabels=show_y_labels_on_right_pane, range=range_3),
                )
                annotations = [_plotly_label_dict(formation_header, 0.08, 1.0)] + 5 * [PLOTLY_BLANK_LABEL]
                fig.layout["annotations"] = annotations

            elif number_of_rows == 4:
                fig.update_yaxes(matches="y")
                fig.update_yaxes(autorange=False)
                fig.update_layout(xaxis_domain=x_axis_domain_formation, scene_domain_x=x_axis_domain_formation)

                range_1 = _auto_range(fig, "y", "y2") 

                if y.startswith("fullcell_standard_") and fullcell_standard_normalization_type is not False:
                    range_2 = [0.0, max(max_val_normalized_col, fullcell_standard_normalization_scaler)]
                    range_2 = norm_range or range_2
                else:
                    range_2 = _auto_range(fig, "y3", "y4") 

                range_3 = _auto_range(fig, "y5", "y6")    
                range_4 = _auto_range(fig, "y7", "y8")

                if y.startswith("fullcell_standard_"):
                    range_4 = eff_lim or range_4
                    range_3 = y_range or range_3
                    range_1 = cv_share_range or range_1

                fig.update_layout(
                    xaxis2=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches=None),
                    xaxis3=dict(range=x_axis_range_formation, domain=x_axis_domain_formation, matches="x"),
                    xaxis4=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches="x2"),
                    xaxis5=dict(range=x_axis_range_formation, domain=x_axis_domain_formation, matches="x"),
                    xaxis6=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches="x2"),
                    xaxis7=dict(range=x_axis_range_formation, domain=x_axis_domain_formation, matches="x"),
                    xaxis8=dict(range=x_axis_range_rest, domain=x_axis_domain_rest, matches="x2"),
                    yaxis=dict(matches="y2", range=range_1),
                    yaxis2=dict(matches="y", showticklabels=show_y_labels_on_right_pane, range=range_1),
                    yaxis3=dict(matches="y4", range=range_2),
                    yaxis4=dict(matches="y3", showticklabels=show_y_labels_on_right_pane, range=range_2),
                    yaxis5=dict(matches="y6", range=range_3),
                    yaxis6=dict(matches="y5", showticklabels=show_y_labels_on_right_pane, range=range_3),
                    yaxis7=dict(matches="y8", range=range_4),
                    yaxis8=dict(matches="y7", showticklabels=show_y_labels_on_right_pane, range=range_4),
                )
                annotations = [_plotly_label_dict(formation_header, 0.08, 1.0)] + 7 * [PLOTLY_BLANK_LABEL]
                fig.layout["annotations"] = annotations

                if y.startswith("fullcell_standard_"):
                    ce_domain_start, ce_domain_end = plotly_row_ratios[2], 1.0
                    capacity_domain_start, capacity_domain_end = plotly_row_ratios[1], plotly_row_ratios[2] - plotly_row_space
                    loss_domain_start, loss_domain_end = plotly_row_ratios[0], plotly_row_ratios[1] - plotly_row_space
                    cv_domain_start, cv_domain_end = 0.0, plotly_row_ratios[0] - plotly_row_space

                    # Format y-axis labels with HTML for proper alignment
                    mode = y.split("_")[-1]
                    capacity_unit = _get_capacity_unit(c, mode=mode)
                
                    ce_label = "Coulombic<br>Efficiency (%)"
                    capacity_label = f"Capacity<br>({capacity_unit})"
                    if fullcell_standard_normalization_type:
                        _norm_label = f"[{fullcell_standard_normalization_scaler:.1f}/{fullcell_standard_normalization_factor:.1f} {capacity_unit}]"
                        loss_label = f"Capacity<br>Retention (norm.)<br>{_norm_label}"

                    else:
                        loss_label = f"Capacity<br>Retention ({capacity_unit})"
                    cv_label = f"CV Capacity<br>({capacity_unit})"

                    fig.update_layout(
                        yaxis8={"domain": [ce_domain_start, ce_domain_end]},
                        yaxis7={"title": dict(text=ce_label), "domain": [ce_domain_start, ce_domain_end]},
                        yaxis6={"domain": [capacity_domain_start, capacity_domain_end]},
                        yaxis5={"title": dict(text=capacity_label), "domain": [capacity_domain_start, capacity_domain_end]},
                        yaxis4={"domain": [loss_domain_start, loss_domain_end]},
                        yaxis3={"title": dict(text=loss_label), "domain": [loss_domain_start, loss_domain_end]},
                        yaxis2={"domain": [cv_domain_start, cv_domain_end]},
                        yaxis1={"title": dict(text=cv_label), "domain": [cv_domain_start, cv_domain_end]},
                    )
                    if show_formation:
                        fig.update_layout(
                            xaxis1={"title": dict(text="")},
                        )
                        if x_axis_domain_formation_fraction < 0.1:
                            fig.update_layout(
                                xaxis1={"showticklabels": False},
                            )

                    if link_capacity_scales:
                        fig.update_layout(
                            yaxis={"matches": "y2"},
                            yaxis2={"matches": "y3"},
                            yaxis3={"matches": "y4"},
                            yaxis4={"matches": "y5"},
                            yaxis5={"matches": "y6"},
                        )
            else:
                raise NotImplementedError("Not implemented for more than four rows")
        else:
            # TODO: refactor so that we do not have specify this:
            if y.endswith("_efficiency"):
                fig.update_layout(
                    yaxis=dict(domain=[0.0, 0.65]),
                    yaxis2={"title": dict(text="Coulombic Efficiency"), "domain": [0.7, 1.0]},
                )
            if y.startswith("fullcell_standard_"):
                range_1 = eff_lim or _auto_range(fig, "y4", "y4")
                range_2 = y_range or _auto_range(fig, "y3", "y3")
                range_3 = _auto_range(fig, "y2", "y2")
                if fullcell_standard_normalization_type is not False:
                    range_3 = [0.0, max(max_val_normalized_col, fullcell_standard_normalization_scaler)]
                range_3 = norm_range or range_3
                
                range_4 = cv_share_range or _auto_range(fig, "y", "y")
                fig.layout["annotations"] = 4 * [PLOTLY_BLANK_LABEL]

                ce_domain_start, ce_domain_end = plotly_row_ratios[2], 1.0
                capacity_domain_start, capacity_domain_end = plotly_row_ratios[1], plotly_row_ratios[2] - plotly_row_space
                loss_domain_start, loss_domain_end = plotly_row_ratios[0], plotly_row_ratios[1] - plotly_row_space
                cv_domain_start, cv_domain_end = 0.0, plotly_row_ratios[0] - plotly_row_space

                # Format y-axis labels with HTML for proper alignment
                capacity_unit = _get_capacity_unit(c, mode=y.split("_")[-1])
                ce_label = "Coulombic<br>Efficiency (%)"
                capacity_label = f"Capacity<br>({capacity_unit})"
                if fullcell_standard_normalization_type:
                    _norm_label = f"[{fullcell_standard_normalization_scaler:.1f}/{fullcell_standard_normalization_factor:.1f} {capacity_unit}]"
                    loss_label = f"Capacity<br>Retention (norm.)<br>{_norm_label}"

                else:
                    loss_label = f"Capacity<br>Retention ({capacity_unit})"
                cv_label = f"CV Capacity<br>({capacity_unit})"

                fig.update_layout(
                    yaxis4={"title": dict(text=ce_label), "domain": [ce_domain_start, ce_domain_end], "matches": None, "range": range_1},
                    yaxis3={"title": dict(text=capacity_label), "domain": [capacity_domain_start, capacity_domain_end], "matches": None, "range": range_2},
                    yaxis2={"title": dict(text=loss_label), "domain": [loss_domain_start, loss_domain_end], "matches": None, "range": range_3},
                    yaxis={"title": dict(text=cv_label), "domain": [cv_domain_start, cv_domain_end], "matches": None, "range": range_4},
                )

        if x_range is not None:
            if not show_formation:
                fig.update_layout(xaxis=dict(range=x_range))

            # The x_range is handled a bit differently when showing formation cycles
            # This is done within if show_formation block

        if split:
            if show_formation:
                if not share_y and not smart_link:
                    fig.update_yaxes(matches=None)
            elif not share_y:
                fig.update_yaxes(matches=None)

        if rangeslider:
            if show_formation:
                print("Can not add rangeslider when showing formation cycles")
            else:
                fig.update_layout(xaxis_rangeslider_visible=True)

        if auto_convert_legend_labels and show_legend:
            for trace in fig.data:
                name = trace.name
                name = name.replace("_", " ").title()
                name = name.replace("Gravimetric", "Grav.")
                name = name.replace("Cv", "(CV)")
                name = name.replace("Non (CV)", "(without CV)")
                hover_template = trace.hovertemplate
                statements = []
                for statement in hover_template.split("<br>"):
                    variable, value = statement.split("=")
                    if value.startswith("%{y}"):
                        variable = name
                    statement = "=".join((variable, value))
                    statements.append(statement)
                hover_template = "<br>".join(statements)
                trace.update(name=name, hovertemplate=hover_template)

        if return_data:
            return fig, s
        return fig

    else:

        if not seaborn_available:
            warnings.warn("seaborn not available, returning only the data so that you can plot it yourself instead")
            return s

        import seaborn as sns

        def _clean_up_axis(fig, info_dicts=None, row_id="row", col_id="cycle_type"):
            # creating a dictionary with keys the same as the axis titles:
            info_dict = {}
            for info in info_dicts:
                if col_id is not None:
                    if row_id is not None:
                        info_text = f'{row_id} = {info["row"]} | {col_id} = {info["col"]}'
                    else:
                        info_text = f'{col_id} = {info["col"]}'
                else:
                    if row_id is not None:
                        info_text = f'{row_id} = {info["row"]}'
                    else:
                        info_text = "single axis"
                info_dict[info_text] = info

            # iterating over the axes and setting the properties:
            for a in fig.get_axes():
                title_text = a.get_title()
                if row_id is None and col_id is None:
                    axis_info = info_dict["single axis"]
                else:
                    axis_info = info_dict.get(title_text, None)
                if axis_info is None:
                    continue
                if xlim := axis_info.get("xlim", None):
                    a.set_xlim(xlim)
                if ylim := axis_info.get("ylim", None):
                    a.set_ylim(ylim)
                if ylabel := axis_info.get("ylabel", None):
                    a.set_ylabel(ylabel)
                a.set_title(axis_info.get("title", ""))
                xticks = axis_info.get("xticks", False)
                yticks = axis_info.get("yticks", False)

                if xticks is False:
                    a.set_xticks([])
                if yticks is False:
                    a.set_yticks([])

        sns.set_style(seaborn_style, seaborn_style_dict)
        sns.set_palette(seaborn_palette)
        sns.set_context(kwargs.pop("seaborn_context", "notebook"))

        facet_kws = dict(despine=False, sharex=False, sharey=False)
        gridspec_kws = dict(hspace=0.07)

        if show_formation:
            additional_kwargs_seaborn["col"] = col_id
            number_of_cols = 2
            gridspec_kws["width_ratios"] = kwargs.pop("width_ratios", [1, 6])
            gridspec_kws["wspace"] = kwargs.pop("wspace", 0.02)
        else:
            number_of_cols = 1
            col_id = None

        if not split:
            number_of_rows = 1
            row_id = None
        else:
            row_id = row
            additional_kwargs_seaborn["row"] = row
            number_of_rows = s[row].nunique()

        def _calculate_seaborn_plot_properties(number_of_rows, number_of_cols, plot_type="default"):
            ## Maybe implement some proper calculations later...
            # _default_seaborn_plot_height = 2.4 + 0.4 * number_of_rows
            # _default_seaborn_plot_aspect = 1.0 + 2.0 / number_of_rows
            # seaborn_plot_height = 2.0  #  hardcoded for now
            # seaborn_plot_aspect = 1.5 if show_formation else 3.0 #  hardcoded for now

            if plot_type == "fullcell_standard":
                _selector = {
                    (4, 1): (2.0, 4.0),
                    (4, 2): (2.0, 2.0),
                }
            else:
                _selector = {
                    (1, 1): (4.0, 2.05),
                    (1, 2): (4.0, 1.0),
                    (2, 1): (2.8, 2.8),
                    (2, 2): (2.8, 1.4),
                    (3, 1): (3.0, 2.7),
                    (3, 2): (3.0, 1.35),
                    (4, 1): (3.0, 2.7),
                    (4, 2): (3.0, 1.35),
                }
            return _selector.get((number_of_rows, number_of_cols), (4.0, 1.8))
            
        if y.startswith("fullcell_standard_"):
            plot_type = "fullcell_standard"
        else:
            plot_type = "default"

        _default_seaborn_plot_height, _default_seaborn_plot_aspect = _calculate_seaborn_plot_properties(
            number_of_rows, number_of_cols, plot_type=plot_type
        )
        seaborn_plot_height = kwargs.pop("seaborn_plot_height", _default_seaborn_plot_height)
        seaborn_plot_aspect = kwargs.pop("seaborn_plot_aspect", _default_seaborn_plot_aspect)

        is_efficiency_plot = y.endswith("_efficiency")
        is_fullcell_standard_plot = y.startswith("fullcell_standard_")
        is_split_constant_voltage_plot = y.endswith("_split_constant_voltage")
        is_multi_row = number_of_rows > 1

        info_dicts = []

        # axis limits:
        if eff_lim is None:
            eff_vals = s.loc[s[color].str.contains("_efficiency"), y_header].replace([np.inf, -np.inf], np.nan).dropna()
            eff_min, eff_max = eff_vals.min(), eff_vals.max()
            eff_lim = [eff_min - 0.05 * abs(eff_min), eff_max + 0.05 * abs(eff_max)]

        if x_range is None:
            cycle_range = max_cycle - formation_cycles
            if cycle_range <= 0:
                cycle_range = 10  # arbitrary value
            x_range = (formation_cycles + 1 - 0.02 * abs(cycle_range), max_cycle + 0.02 * abs(cycle_range))

        if y_range is None:
            y_vals = s.loc[~s[color].str.contains("_efficiency"), y_header].replace([np.inf, -np.inf], np.nan).dropna()
            min_value, max_value = y_vals.min(), y_vals.max()
            y_range = y_range or [min_value - 0.05 * abs(min_value), max_value + 0.05 * abs(max_value)]

        _efficiency_label = r"Efficiency (%)"

        if is_efficiency_plot:
            facet_kws["sharey"] = False
            gridspec_kws["height_ratios"] = [1, 4]
            if show_formation:
                info_dicts.append(
                    dict(
                        ylabel=_efficiency_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=eff_lim,
                        row=0,
                        col="formation",
                        yticks=None,
                        xticks=False,
                    )
                )
                info_dicts.append(
                    dict(
                        ylabel="",
                        title="",
                        xlim=x_range,
                        ylim=eff_lim,
                        row=0,
                        col="standard",
                        yticks=False,
                        xticks=False,
                    )
                )
                info_dicts.append(
                    dict(
                        ylabel="",
                        title="",
                        xlim=xlim_formation,
                        ylim=y_range,
                        row=1,
                        col="formation",
                        yticks=None,
                        xticks=None,
                    )
                )
                info_dicts.append(
                    dict(
                        ylabel="",
                        title="",
                        xlim=x_range,
                        ylim=y_range,
                        row=1,
                        col="standard",
                        yticks=False,
                        xticks=None,
                    )
                )
            else:
                info_dicts.append(
                    dict(
                        ylabel=_efficiency_label,
                        title="",
                        xlim=x_range,
                        ylim=eff_lim,
                        row=0,
                        col=None,
                        yticks=None,
                        xticks=False,
                    )
                )
                info_dicts.append(
                    dict(
                        ylabel="",
                        title="",
                        xlim=x_range,
                        ylim=y_range,
                        row=1,
                        col=None,
                        yticks=None,
                        xticks=None,
                    )
                )

        elif is_split_constant_voltage_plot:
            if is_multi_row:
                cv_share_range = cv_share_range or y_range
                for r, _x, _y_range in zip(
                    ["all", "without CV", "with CV"], [False, False, None], [y_range, y_range, cv_share_range]
                ):
                    _d = dict(
                        ylabel=y_label,
                        title="",
                        xlim=x_range,
                        ylim=_y_range,
                        row=r,
                        col=None,
                        yticks=None,
                        xticks=_x,
                    )

                    if show_formation:
                        _d["col"] = "standard"
                        _d["yticks"] = False
                        _d["ylabel"] = ""
                        info_dicts.append(
                            dict(
                                ylabel=y_label,
                                title="",
                                xlim=xlim_formation,
                                ylim=_y_range,
                                row=r,
                                col="formation",
                                yticks=None,
                                xticks=_x,
                            )
                        )
                    info_dicts.append(_d)
            else:
                _d = dict(
                    ylabel=y_label,
                    title="",
                    xlim=x_range,
                    ylim=y_range,
                    row=None,
                    col=None,
                    yticks=None,
                    xticks=None,
                )
                if show_formation:
                    _d["col"] = "standard"
                    _d["yticks"] = False
                    _d["ylabel"] = ""
                    info_dicts.append(
                        dict(
                            ylabel=y_label,
                            title="",
                            xlim=xlim_formation,
                            ylim=y_range,
                            row=None,
                            col="formation",
                            yticks=None,
                            xticks=None,
                        )
                    )
                info_dicts.append(_d)

        elif is_fullcell_standard_plot:


            capacity_unit = _get_capacity_unit(c, mode=y.split("_")[-1])
            ce_label = "Coulombic\nEfficiency (%)"
            capacity_label = f"Capacity\n({capacity_unit})"

            loss_label = f"Capacity\nRetention\n({capacity_unit})"
            if fullcell_standard_normalization_type:
                _norm_label = f"[{fullcell_standard_normalization_scaler:.1f}/{fullcell_standard_normalization_factor:.1f} {capacity_unit}]"
                loss_label = f"Capacity\nRetention (norm.)\n{_norm_label}"
            else:
                loss_label = f"Capacity\nRetention\n({capacity_unit})"

            cv_label = f"CV Capacity\n({capacity_unit})"

            facet_kws["sharey"] = False
            gridspec_kws["height_ratios"] = [1, 3, 3, 3]

            number_of_rows = 4

            if fullcell_standard_normalization_type is not False:
                cum_loss_info_range = norm_range or [0.0, max(max_val_normalized_col, fullcell_standard_normalization_scaler)]

            cv_info = dict(
                title="",
                xlim=x_range,
                ylim=cv_share_range or y_range,
                row=3,
                col="standard",
                yticks=False,
                xticks=True,
            )
            cum_loss_info = dict(
                title="",
                xlim=x_range,
                ylim=cum_loss_info_range,
                row=2,
                col="standard",
                yticks=False,
                xticks=False,
            )
            capacity_info = dict(
                title="",
                xlim=x_range,
                ylim=y_range,
                row=1,
                col="standard",
                yticks=False,
                xticks=False,
            )
            ce_info = dict(
                title="",
                xlim=x_range,
                ylim=eff_lim,
                row=0,
                col="standard",
                yticks=False,
                xticks=False,
            )
            if not show_formation:
                cv_info["ylabel"] = cv_label
                cum_loss_info["ylabel"] = loss_label
                capacity_info["ylabel"] = capacity_label
                ce_info["ylabel"] = ce_label

                cv_info["yticks"] = True
                cum_loss_info["yticks"] = True
                capacity_info["yticks"] = True
                ce_info["yticks"] = True

            info_dicts.append(cv_info)
            info_dicts.append(cum_loss_info)
            info_dicts.append(capacity_info)
            info_dicts.append(ce_info)

            if show_formation:
                cv_info_formation = dict(
                        ylabel=cv_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=cv_share_range or y_range,
                        row=3,
                        col="formation",
                        yticks=True,
                        xticks=True,
                    )
                loss_info_formation = dict(
                        ylabel=loss_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=cum_loss_info_range,
                        row=2,
                        col="formation",
                        yticks=True,
                        xticks=False,
                    )
                cap_info_formation = dict(
                        ylabel=capacity_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=y_range,
                        row=1,
                        col="formation",
                        yticks=True,
                        xticks=False,
                    )
                ce_info_formation = dict(
                        ylabel=ce_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=eff_lim,
                        row=0,
                        col="formation",
                        yticks=True,
                        xticks=False,
                    )
                info_dicts.append(cv_info_formation)
                info_dicts.append(loss_info_formation)
                info_dicts.append(cap_info_formation)
                info_dicts.append(ce_info_formation)

            if verbose:
                print(f"{y_header=}")
                print(f"{color=}")
                print(f"{seaborn_plot_height=}")
                print(f"{seaborn_plot_aspect=}")
                print(f"{markers=}")
                print(f"{additional_kwargs_seaborn=}")
                print(f"{facet_kws=}")
                print(f"{kwargs=}")
                print(f"{info_dicts=}")
            
        else:
            if is_multi_row:
                for i in range(number_of_rows):
                    info_dicts.append(
                        dict(
                            ylabel=y_label,
                            title="",
                            xlim=x_range,
                            ylim=y_range,
                            row=i,
                            col=None,
                            yticks=None,
                            xticks=False,
                        )
                    )
                    if show_formation:
                        info_dicts.append(
                            dict(
                                ylabel=y_label,
                                title="",
                                xlim=xlim_formation,
                                ylim=y_range,
                                row=i,
                                col="formation",
                                yticks=None,
                                xticks=False,
                            )
                        )
            else:
                _r = 1 if split else None
                _d = dict(
                    ylabel=y_label,
                    title="",
                    xlim=x_range,
                    ylim=y_range,
                    row=_r,
                    col=None,
                    yticks=None,
                    xticks=None,
                )
                if show_formation:
                    _d["col"] = "standard"
                    _d["yticks"] = False
                    _d["ylabel"] = ""
                    info_dicts.append(
                        dict(
                            ylabel=y_label,
                            title="",
                            xlim=xlim_formation,
                            ylim=y_range,
                            row=_r,
                            col="formation",
                            yticks=None,
                            xticks=None,
                        )
                    )
                info_dicts.append(_d)


        facet_kws["gridspec_kws"] = gridspec_kws

        sns_fig = sns.relplot(
            data=s,
            x=x,
            y=y_header,
            hue=color,
            height=seaborn_plot_height,
            aspect=seaborn_plot_aspect,
            kind="line",
            marker="o" if markers else None,
            legend=show_legend,
            **additional_kwargs_seaborn,
            facet_kws=facet_kws,
            **kwargs,
        )

        sns_fig.set_axis_labels(x_label, y_label)

        if auto_convert_legend_labels and show_legend:
            legend = sns_fig.legend
            if legend is not None:
                for le in legend.get_texts():
                    name = le.get_text()
                    name = name.replace("_", " ").title()
                    name = name.replace("Gravimetric", "Grav.")
                    name = name.replace("Cv", "(CV)")
                    name = name.replace("Non (CV)", "(without CV)")
                    le.set_text(name)
                sns_fig.legend.set_title(None)

        if markers:
            for ax in sns_fig.axes.flat:
                lines = ax.get_lines()
                for line in lines:
                    line.set_markersize(seaborn_marker_size)

        if seaborn_line_hooks:
            for ax in sns_fig.axes.flat:
                lines = ax.get_lines()
                for line in lines:
                    for hook, args, kwargs in seaborn_line_hooks:
                        if hasattr(line, hook):
                            getattr(line, hook)(*args, **kwargs)

        fig = sns_fig.figure
        _clean_up_axis(fig, info_dicts=info_dicts, row_id=row_id, col_id=col_id)
        fig.align_ylabels()
        _hack_to_position_legend = {1: 0.97, 2: 0.95, 3: 0.92, 4: 0.92, 5: 0.92}
        fig.suptitle(title, y=_hack_to_position_legend[number_of_rows])

        plt.close(fig)
        if return_data:
            return fig, s
        return fig


def _report_summary_plot_info(c, x, y, x_label, x_axis_labels, x_cols, y_label, y_axis_label, y_cols):
    from pprint import pprint, pformat
    import textwrap

    print("Running summary_plot in verbose mode\n")
    print("Selected columns:")
    print(60 * "-")
    print(f"x: {x}")
    print(f"y: {y}")
    print("\nSelected Labels:")
    print(60 * "-")
    print(f"x: {x_label}")
    print(f"y: {y_label}")
    print("\nAvailable x-columns:")
    print(60 * "-")
    for col in x_cols[0]:
        print(f"{col}")
    print("\nAvailable y-columns sets:")
    print(60 * "-")
    for key, cols in y_cols.items():
        print(f"{key}:")
        for line in textwrap.wrap(pformat(cols, width=60), width=60):
            print("  " + line)
    print("\nAvailable y-columns:")
    print(60 * "-")
    cols = list(c.data.summary.columns)
    for line in textwrap.wrap(pformat(cols, width=60), width=60):
        print("  " + line)
    print("\nAvailable pre-defined labels:")
    print(60 * "-")
    print("x_axis_labels")
    pprint(x_axis_labels)
    print("y_axis_label")
    pprint(y_axis_label)


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

    summary = c.data.summary

    summary_no_cv = c.make_summary(selector_type="non-cv", create_copy=True).data.summary
    summary_only_cv = c.make_summary(selector_type="only-cv", create_copy=True).data.summary
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
    summary_no_cv = summary_no_cv.melt(id_vars, var_name=var_name, value_name=value_name)
    summary_only_cv = summary_only_cv.melt(id_vars, var_name=var_name, value_name=value_name)
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
    from cellpy.readers.core import Q

    _set_individual_y_labels = False
    _special_height = None

    raw = cell.data.raw.copy()
    if y is not None:
        if y_label is None:
            y_label = y
        y = [y]
        y_label = [y_label]

    elif plot_type is not None:
        # special pre-defined plot types
        if plot_type == "voltage-current":
            y1 = _hdr_raw["voltage_txt"]
            y1_label = f"Voltage ({cell.data.raw_units.voltage})"
            y2 = _hdr_raw["current_txt"]
            y2_label = f"Current ({cell.data.raw_units.current})"
            y = [y1, y2]
            y_label = [y1_label, y2_label]

        elif plot_type == "capacity":
            _y = [
                (
                    _hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
            ]
            y, y_label = zip(*_y)

        elif plot_type == "raw":
            _y = [
                (
                    _hdr_raw["cycle_index_txt"],
                    f"Cycle index (#)",
                ),
                (
                    _hdr_raw["step_index_txt"],
                    f"Step index (#)",
                ),
                (_hdr_raw["voltage_txt"], f"Voltage ({cell.data.raw_units.voltage})"),
                (_hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
            ]
            y, y_label = zip(*_y)
            _special_height = 600

        elif plot_type == "capacity-current":
            _y = [
                (
                    _hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
                (_hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
            ]
            y, y_label = zip(*_y)
            _special_height = 500

        elif plot_type == "full":
            _y = [
                (_hdr_raw["voltage_txt"], f"Voltage ({cell.data.raw_units.voltage})"),
                (_hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
                (
                    _hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["cycle_index_txt"],
                    f"Cycle index (#)",
                ),
                (
                    _hdr_raw["step_index_txt"],
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
        y = [_hdr_raw["voltage_txt"]]
        y_label = [f"Voltage ({cell.data.raw_units.voltage})"]

    if x is None:
        x = "test_time_hrs"

    if x in ["test_time_hrs", "test_time_hours"]:
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("hours").magnitude
        raw[x] = raw[_hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (hours)"
    elif x == "test_time_days":
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("days").magnitude
        raw[x] = raw[_hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (days)"
    elif x == "test_time_years":
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("years").magnitude
        raw[x] = raw[_hdr_raw["test_time_txt"]] * conv_factor
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

        fig, axes = plt.subplots(nrows=number_of_rows, ncols=1, figsize=figsize, sharex=True)

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

    raw_hdr = get_headers_normal()
    step_hdr = get_headers_step_table()

    data = cell.data.raw.copy()
    table = cell.data.steps.copy()

    if cycle is None:
        cycle = list(data["cycle_index"].unique())

    if not isinstance(cycle, (list, tuple)):
        cycle = [cycle]

    delta = "_delta"
    v_delta = step_hdr["voltage"] + delta
    i_delta = step_hdr["current"] + delta
    c_delta = step_hdr["charge"] + delta
    dc_delta = step_hdr["discharge"] + delta
    cycle_ = step_hdr["cycle"]
    step_ = step_hdr["step"]
    type_ = step_hdr["type"]

    time_hdr = raw_hdr["test_time_txt"]
    cycle_hdr = raw_hdr["cycle_index_txt"]
    step_number_hdr = raw_hdr["step_index_txt"]
    current_hdr = raw_hdr["current_txt"]
    voltage_hdr = raw_hdr["voltage_txt"]

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


def _get_info(table, cycle, step):
    # obs! hard-coded col-names. Please fix me.
    m_table = (table.cycle == cycle) & (table.step == step)
    p1, p2 = table.loc[m_table, ["point_min", "point_max"]].values[0]
    c1, c2 = table.loc[m_table, ["current_min", "current_max"]].abs().values[0]
    d_voltage, d_current = table.loc[m_table, ["voltage_delta", "current_delta"]].values[0]
    d_discharge, d_charge = table.loc[m_table, ["discharge_delta", "charge_delta"]].values[0]
    current_max = (c1 + c2) / 2
    rate = table.loc[m_table, "rate_avr"].values[0]
    step_type = table.loc[m_table, "type"].values[0]
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

    span_colors = ["#4682B4", "#FFA07A"]

    voltage_color = "#008B8B"
    current_color = "#CD5C5C"

    m_cycle_data = data.cycle_index == cycle
    all_steps = data[m_cycle_data]["step_index"].unique()

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
        m = m_cycle_data & (data.step_index == s)
        c = data.loc[m, "current"] * i_scaler
        v = data.loc[m, "voltage"] * v_scaler
        t = data.loc[m, "test_time"] * t_scaler
        step_type, rate, current_max, dv, dc, d_discharge, d_charge = _get_info(table, cycle, s)
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


def cycles_plot(
    c,
    cycles=None,
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
    xlim=None,
    ylim=None,
    interactive=True,
    return_figure=None,
    width=600,
    height=400,
    marker_size=5,
    formation_line_color="rgba(152, 0, 0, .8)",
    force_colorbar=False,
    force_nonbar=False,
    plotly_template=None,
    seaborn_palette: str = "deep",
    seaborn_style: str = "dark",
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
        seaborn_palette: name of the seaborn palette to use (only if seaborn is available)
        seaborn_style: name of the seaborn style to use (only if seaborn is available)
        **kwargs: Additional keyword arguments for the plotting backend.

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure: The generated plot figure.
    """

    import numpy as np
    import matplotlib
    from matplotlib.colors import Normalize, ListedColormap

    if interactive and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        interactive = False

    if return_figure is None:
        return_figure = not interactive

    if cycles is None:
        cycles = c.get_cycle_numbers()

    if interactive and title is None:
        fig_title = f"Capacity plots for <b>{c.cell_name}</b>"
        fig_title += f"<br>{mode} mode"
        if interpolated:
            fig_title += f", interpolated ({number_of_points} points)"

    else:
        fig_title = title or f"Capacity plots for {c.cell_name}"

    kw_arguments = dict(
        method=method,
        interpolated=interpolated,
        label_cycle_number=True,
        categorical_column=True,
        number_of_points=number_of_points,
        insert_nan=True,
        mode=mode,
    )
    df = c.get_cap(cycles=cycles, **kw_arguments)

    selector = df["cycle"] <= formation_cycles
    form_cycles = df.loc[selector, :]
    rest_cycles = df.loc[~selector, :]

    n_form_cycles = len(form_cycles["cycle"].unique())
    n_rest_cycles = len(rest_cycles["cycle"].unique())

    capacity_unit = _get_capacity_unit(c, mode=mode)

    cbar_aspect = 30

    if not interactive:
        if seaborn_available:
            import seaborn as sns

            seaborn_facecolor = kwargs.pop("seaborn_facecolor", "#EAEAF2")
            seaborn_edgecolor = kwargs.pop("seaborn_edgecolor", "black")
            seaborn_style_dict_default = {"axes.facecolor": seaborn_facecolor, "axes.edgecolor": seaborn_edgecolor}
            seaborn_style_dict = kwargs.pop("seaborn_style_dict", seaborn_style_dict_default)

            sns.set_style(seaborn_style, seaborn_style_dict)
            sns.set_palette(seaborn_palette)
            sns.set_context(kwargs.pop("seaborn_context", "notebook"))

        fig, ax = plt.subplots(1, 1, figsize=figsize)
        fig_width, fig_height = figsize

        if not form_cycles.empty and show_formation:
            if fig_width < 6:
                print("Warning: try setting the figsize to (6, 4) or larger")
            if fig_width > 8:
                print("Warning: try setting the figsize to (8, 4) or smaller")
            min_cycle, max_cycle = (
                form_cycles["cycle"].min(),
                form_cycles["cycle"].max(),
            )
            norm_formation = Normalize(vmin=min_cycle, vmax=max_cycle)
            cycle_sequence = np.arange(min_cycle, max_cycle + 1, 1)

            shrink = min(1.0, (1 / 8) * n_form_cycles)

            c_m_formation = ListedColormap(plt.get_cmap(formation_colormap, 2 * len(cycle_sequence))(cycle_sequence))
            s_m_formation = matplotlib.cm.ScalarMappable(cmap=c_m_formation, norm=norm_formation)
            for name, group in form_cycles.groupby("cycle"):
                ax.plot(
                    group["capacity"],
                    group["voltage"],
                    lw=2,  # alpha=0.7,
                    color=s_m_formation.to_rgba(name),
                    label=f"Cycle {name}",
                )
            cbar_formation = fig.colorbar(
                s_m_formation,
                ax=ax,  # label="Formation Cycle",
                ticks=np.arange(
                    form_cycles["cycle"].min(),
                    form_cycles["cycle"].max() + 1,
                    1,
                ),
                shrink=shrink,
                aspect=cbar_aspect * shrink,
                location="right",
                anchor=(0.0, 0.0),
            )
            cbar_formation.set_label(
                "Form. Cycle",
                rotation=270,
                labelpad=12,
            )

        norm = Normalize(vmin=rest_cycles["cycle"].min(), vmax=rest_cycles["cycle"].max())
        if cut_colorbar:
            cycle_sequence = np.arange(rest_cycles["cycle"].min(), rest_cycles["cycle"].max() + 1, 1)
            n = int(np.round(1.2 * rest_cycles["cycle"].max()))
            c_m = ListedColormap(plt.get_cmap(colormap, n)(cycle_sequence))
        else:
            c_m = plt.get_cmap(colormap)

        s_m = matplotlib.cm.ScalarMappable(cmap=c_m, norm=norm)
        for name, group in rest_cycles.groupby("cycle"):
            ax.plot(
                group["capacity"],
                group["voltage"],
                lw=1,
                color=s_m.to_rgba(name),
                label=f"Cycle {name}",
            )
        cbar = fig.colorbar(
            s_m,
            ax=ax,
            label="Cycle",
            aspect=cbar_aspect,
            location="right",
        )
        cbar.set_label(
            "Cycle",
            rotation=270,
            labelpad=12,
        )
        # cbar.ax.yaxis.set_ticks_position("left")

        ax.set_xlabel(f"Capacity ({capacity_unit})")
        ax.set_ylabel(f"Voltage ({c.cellpy_units.voltage})")

        ax.set_title(fig_title)

        if xlim:
            ax.set_xlim(xlim)
        if ylim:
            ax.set_ylim(ylim)

        if return_figure:
            plt.close(fig)
            return fig
    else:

        import plotly.express as px
        import plotly.graph_objects as go

        set_plotly_template(plotly_template)

        color_scales = px.colors.named_colorscales()
        if colormap not in color_scales:
            colormap = "Blues_r"

        if cut_colorbar:
            range_color = [df["cycle"].min(), 1.2 * df["cycle"].max()]
        else:
            range_color = [df["cycle"].min(), df["cycle"].max()]
        if (n_rest_cycles < 8 and not force_colorbar) or force_nonbar:
            show_formation_legend = True
            cmap = px.colors.sample_colorscale(
                colorscale=colormap,
                samplepoints=n_rest_cycles,
                low=0.0,
                high=0.8,
                colortype="rgb",
            )

            fig = px.line(
                rest_cycles,
                x="capacity",
                y="voltage",
                color="cycle",
                title=fig_title,
                labels={
                    "capacity": f"Capacity ({capacity_unit})",
                    "voltage": f"Voltage ({c.cellpy_units.voltage})",
                },
                color_discrete_sequence=cmap,
            )

        else:
            show_formation_legend = False
            fig = px.scatter(
                rest_cycles,
                x="capacity",
                y="voltage",
                color="cycle",
                title=fig_title,
                labels={
                    "capacity": f"Capacity ({capacity_unit})",
                    "voltage": f"Voltage ({c.cellpy_units.voltage})",
                },
                color_continuous_scale=colormap,
                range_color=range_color,
            )
            fig.update_traces(mode="lines+markers", line_color="white", line_width=1)

        if not form_cycles.empty and show_formation:
            for name, group in form_cycles.groupby("cycle"):
                trace = go.Scatter(
                    x=group["capacity"],
                    y=group["voltage"],
                    name=f"{name} (f.c.)",
                    hovertemplate=f"Formation Cycle {name}<br>Capacity: %{{x}}<br>Voltage: %{{y}}",
                    mode="lines",
                    marker=dict(color=formation_line_color),
                    showlegend=show_formation_legend,
                    legendrank=1,
                    legendgroup="formation",
                )

                fig.add_trace(trace)

        fig.update_traces(marker=dict(size=marker_size))
        fig.update_layout(height=height, width=width)
        if xlim:
            fig.update_xaxes(range=xlim)
        if ylim:
            fig.update_yaxes(range=ylim)

        if return_figure:
            return fig
        fig.show()


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
    import pathlib

    import cellpy

    p = pathlib.Path("../../testdata/hdf5/20160805_test001_45_cc.h5")
    out = pathlib.Path("../../tmp")
    assert out.exists()
    c = cellpy.get(p)
    fig = summary_plot(
        c,
        # x="normalized_cycle_index",
        y="capacities_gravimetric_coulombic_efficiency",
        # ce_range=[0.0, 200.0],
        # ylim=[0.0, 1.0],
        # show_formation=False,
        # cut_colorbar=False,
        split=True,
        title="My nice plot",
        interactive=True,  # rangeslider=True,
        show_formation=True,  # return_figure=True,
    )
    print("saving figure")
    print(f"{fig=}")
    print(f"{type(fig)=}")
    # save_image_files(fig, out / "test_plot_plotly", backend="plotly")
    fig.show()





if __name__ == "__main__":
    # _check_plotter_plotly()
    # _check_plotter_matplotlib()
    _check_summary_plotter_plotly()
