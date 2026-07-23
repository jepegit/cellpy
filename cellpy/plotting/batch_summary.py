"""Batch cycle-life summary plots (#658).

Relocated from ``cellpy.utils.batch_tools.batch_plotters`` so ``Batch.plot``
delegates into ``cellpy.plotting``. Public backends: ``plotly`` (primary) and
``matplotlib``. ``seaborn`` is a deprecated alias for ``matplotlib``; ``bokeh``
raises.
"""

from __future__ import annotations

import functools
import importlib
import itertools
import logging
import warnings
from typing import Any, Optional

import matplotlib.pyplot as plt
import pandas as pd

import cellpy.config as config
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.plotting.labels import legend_replacer as _plotly_legend_replacer
from cellpy.plotting.theme import make_plotly_template as _make_plotly_template

plotly_available = importlib.util.find_spec("plotly") is not None
if plotly_available:
    import plotly.express as px

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()

SUPPORTED_BATCH_PLOT_BACKENDS = ("plotly", "matplotlib")


def resolve_batch_plot_backend(backend: Optional[str]) -> str:
    """Normalize Batch.plot backend names (triage for #658)."""
    from cellpy._deprecation import warn_once

    if backend is None:
        backend = getattr(config.batch, "backend", None) or "plotly"
    key = str(backend).strip().lower()
    if key == "seaborn":
        warn_once(
            'Batch.plot(backend="seaborn")',
            'backend="matplotlib"',
            stacklevel=3,
        )
        key = "matplotlib"
    if key == "bokeh":
        raise ValueError(
            'Batch.plot backend "bokeh" was removed; use backend="plotly" '
            'or backend="matplotlib".'
        )
    if key not in SUPPORTED_BATCH_PLOT_BACKENDS:
        raise ValueError(
            f"backend {backend!r} not supported; use "
            f"{list(SUPPORTED_BATCH_PLOT_BACKENDS)!r}"
        )
    return key


def batch_summary_plot(
    experiment: Any,
    *,
    backend: Optional[str] = None,
    show: Optional[bool] = None,
    **kwargs: Any,
) -> Any:
    """Draw the Batch cycle-life summary figure (cap / CE / IR / rate panels).

    Args:
        experiment: ``CyclingExperiment`` with ``memory_dumped["summary_engine"]``.
        backend: ``plotly`` or ``matplotlib`` (after triage).
        show: if True, call ``figure.show()`` for plotly (default True for plotly).
        **kwargs: forwarded to frame prep / renderers (``capacity_specifics``,
            ``ce_range``, ``ir``, ``rate``, filters, …).

    Returns:
        Backend-native figure/canvas, or ``None`` if prep/render fails.
    """
    backend_key = resolve_batch_plot_backend(backend)
    if backend_key == "plotly":
        if not plotly_available:
            raise ImportError("plotly is required for Batch.plot(backend='plotly')")
        try:
            frame = generate_summary_frame_for_plotting(
                experiment.journal.pages, experiment, **kwargs
            )
        except KeyError as e:
            logging.info("could not process the summaries (%s)", e)
            return None
        try:
            canvas = plot_cycle_life_summary_plotly(frame, **kwargs)
        except Exception as e:
            logging.info("could not generate summary plots (%s)", e)
            return None
        if show is None:
            show = True
        if show and canvas is not None and hasattr(canvas, "show"):
            canvas.show()
        return canvas

    # matplotlib — wide MultiIndex frame (legacy cycle-life layout)
    width = kwargs.pop("width", config.batch.summary_plot_width)
    height = kwargs.pop("height", config.batch.summary_plot_height)
    height_fractions = kwargs.pop(
        "height_fractions", config.batch.summary_plot_height_fractions
    )
    try:
        keys = [df.name for df in experiment.memory_dumped["summary_engine"]]
        summaries = pd.concat(
            experiment.memory_dumped["summary_engine"], keys=keys, axis=1
        )
    except KeyError:
        logging.info("could not parse the summaries for matplotlib batch plot")
        return None
    return plot_cycle_life_summary_matplotlib(
        experiment.journal.pages,
        summaries,
        width,
        height,
        height_fractions,
        **kwargs,
    )


def create_legend(info, c, option="clean", use_index=False):
    """creating more informative legends"""

    logging.debug("    - creating legends")
    mass, loading, label = info.loc[
        c, [hdr_journal.mass, hdr_journal.loading, hdr_journal.label]
    ]

    if use_index or not label:
        label = c.split("_")
        label = "_".join(label[1:])

    if option == "clean":
        logging.debug(f"label: {label}")
        return label

    if option == "mass":
        label = f"{label} ({mass:.2f} mg)"
    elif option == "loading":
        label = f"{label} ({loading:.2f} mg/cm2)"
    elif option == "all":
        label = f"{label} ({mass:.2f} mg) ({loading:.2f} mg/cm2)"
    logging.debug(f"advanced label: {label}")
    return label


def look_up_group(info, c):
    logging.debug("    - looking up groups")
    g, sg = info.loc[c, [hdr_journal.group, hdr_journal.sub_group]]
    return int(g), int(sg)


def create_plot_option_dicts(
    info, marker_types=None, colors=None, line_dash=None, size=None, palette=None
):
    """Create two dictionaries with plot-options.

    The first iterates colors (based on group-number), the second iterates
    through marker types.

    Returns: group_styles (dict), sub_group_styles (dict)
    """

    logging.debug("    - creating plot-options-dict")
    if palette is None:
        palette = {
            1: ["k"],
            3: ["k", "r"],
            4: ["k", "r", "b"],
            5: ["k", "r", "b", "g"],
            6: ["k", "r", "b", "g", "c"],
            7: ["k", "r", "b", "g", "c", "m"],
            8: ["k", "r", "b", "g", "c", "m", "y"],
        }

    max_palette_row = max(palette.keys())
    if marker_types is None:
        marker_types = [
            "circle",
            "square",
            "triangle",
            "inverted_triangle",
            "diamond",
            "asterisk",
            "cross",
        ]

    if line_dash is None:
        line_dash = [0, 0]

    if size is None:
        size = 10

    groups = info[hdr_journal.group].unique()
    number_of_groups = len(groups)
    if colors is None:
        if number_of_groups < 4:
            colors = palette[3]

        else:
            colors = palette[min(max_palette_row, number_of_groups)]

    sub_groups = info[hdr_journal.sub_group].unique()
    marker_it = itertools.cycle(marker_types)
    colors_it = itertools.cycle(colors)

    group_styles = dict()
    sub_group_styles = dict()

    for j in groups:
        color = next(colors_it)
        marker_options = {"line_color": color, "fill_color": color}

        line_options = {"line_color": color}
        group_styles[j] = {"marker": marker_options, "line": line_options}

    for j in sub_groups:
        marker_type = next(marker_it)
        marker_options = {"marker": marker_type, "size": size}

        line_options = {"line_dash": line_dash}
        sub_group_styles[j] = {"marker": marker_options, "line": line_options}
    return group_styles, sub_group_styles


def generate_summary_frame_for_plotting(pages, experiment, **kwargs) -> pd.DataFrame:
    trim_pages = kwargs.pop("trim_pages", False)
    capacity_specifics = kwargs.get("capacity_specifics", "gravimetric")
    only_selected = kwargs.get("only_selected", False)
    hdr_journal_selected = hdr_journal.selected
    selected = None

    if only_selected:
        if hdr_journal_selected not in pages.columns:
            logging.critical("no 'selected' column in pages")
            only_selected = False
        else:
            selected = pages.loc[pages[hdr_journal_selected] > 0, :].index

    summary_frames = []
    keys = []
    for df in experiment.memory_dumped["summary_engine"]:
        if only_selected:
            df_filtered = df.copy()
            df_filtered = df_filtered.loc[:, selected]
            summary_frames.append(df_filtered)
        else:
            summary_frames.append(df)
        keys.append(df.name)

    summaries = pd.concat(summary_frames, keys=keys, axis=1)
    hdr_cycle = hdr_summary["cycle_index"]
    # Summary farms often carry an unnamed cycle index after join_summaries;
    # name it so reset_index() yields a selectable ``cycle_index`` column.
    if summaries.index.name is None:
        summaries.index.name = hdr_cycle
    summaries = summaries.reset_index()
    summaries.columns.names = ["variable", "cell"]

    hdr_charge, hdr_discharge = _get_capacity_columns(
        capacity_specifics=capacity_specifics
    )
    hdr_ce = hdr_summary["coulombic_efficiency"]
    hdr_ir_charge = hdr_summary["ir_charge"]
    hdr_ir_discharge = hdr_summary["ir_discharge"]
    hdr_charge_rate = hdr_summary["charge_c_rate"]
    hdr_discharge_rate = hdr_summary["discharge_c_rate"]

    _required_summaries = [hdr_cycle, hdr_ce, hdr_charge, hdr_discharge]
    _optional_summaries = [
        hdr_ir_charge,
        hdr_ir_discharge,
        hdr_charge_rate,
        hdr_discharge_rate,
    ]
    for _optional_summary in _optional_summaries:
        if _optional_summary in summaries.columns:
            _required_summaries.append(_optional_summary)
    try:
        summaries = summaries.loc[:, _required_summaries]
    except KeyError as e:
        logging.critical(f"could not get the required summaries ({type(e)}: {e})")
        raise e
    id_var = summaries.columns[0]
    summaries = summaries.melt(
        id_vars=[id_var],
        # prior to pandas 2.2.0, the following line was used
        #   id_vars=[hdr_cycle],
    )

    # due to pandas 2.2.0 change, the following line is needed:
    summaries = summaries.rename(columns={id_var: hdr_cycle})
    pages = pages.copy()
    pages.index.name = "cell"
    pages = pages.reset_index()

    if trim_pages:
        try:
            pages = pages.loc[
                :,
                [
                    "cell",
                    hdr_journal.mass,
                    hdr_journal.total_mass,
                    hdr_journal.loading,
                    hdr_journal.nom_cap,
                    hdr_journal.area,
                    hdr_journal.label,
                    hdr_journal.cell_type,
                    hdr_journal.instrument,
                    hdr_journal.group,
                    hdr_journal.sub_group,
                ],
            ]
        except KeyError as e:
            logging.debug(f"could not trim pages ({e})")
    try:
        summaries = summaries.merge(pages, on="cell")
    except Exception as e:
        logging.debug(f"could not merge summaries and pages ({e})")
    return summaries


def _make_labels():
    labels = {
        hdr_summary.cycle_index: "Cycle number",
        hdr_summary["charge_capacity_gravimetric"]: "Gravimetric Charge Capacity",
        hdr_summary["charge_capacity_areal"]: "Areal Charge Capacity",
        hdr_summary["charge_capacity_absolute"]: "Absolute Charge Capacity",
        hdr_summary.charge_capacity: "Charge Capacity",
        hdr_summary["discharge_capacity_gravimetric"]: "Gravimetric Discharge Capacity",
        hdr_summary["discharge_capacity_areal"]: "Areal Discharge Capacity",
        hdr_summary["discharge_capacity_absolute"]: "Absolute Discharge Capacity",
        hdr_summary.discharge_capacity: "Discharge Capacity",
        hdr_summary.charge_c_rate: "C-rate (charge)",
        hdr_summary.discharge_c_rate: "C-rate (discharge)",
        hdr_summary.coulombic_efficiency: "Coulombic Efficiency",
        hdr_summary.ir_charge: "IR (charge)",
        hdr_summary.ir_discharge: "IR (discharge)",
        hdr_journal.group: "Group",
        hdr_journal.sub_group: "Sub-group",
        "variable": "Variable",
        "value": "Value",
    }
    return labels


def _get_capacity_columns(capacity_specifics="gravimetric"):
    if capacity_specifics == "raw":
        hdr_charge = hdr_summary["charge_capacity"]
        hdr_discharge = hdr_summary["discharge_capacity"]
        return hdr_charge, hdr_discharge

    hdr_charge = hdr_summary["_".join(["charge_capacity", capacity_specifics])]
    hdr_discharge = hdr_summary["_".join(["discharge_capacity", capacity_specifics])]
    return hdr_charge, hdr_discharge


def plot_cycle_life_summary_plotly(summaries: pd.DataFrame, **kwargs):
    """Plotting cycle life summaries using plotly."""

    # TODO: get either units or experiment object to get units and send it to _make_labels

    group_legends = kwargs.pop("group_legends", True)
    base_template = kwargs.pop("base_template", "plotly")
    inverted_mode = kwargs.pop("inverted_mode", False)
    color_map = kwargs.pop("color_map", px.colors.qualitative.Set1)

    if isinstance(color_map, str):
        if hasattr(px.colors.qualitative, color_map):
            color_map = getattr(px.colors.qualitative, color_map)
        else:
            logging.warning(f"could not find color map {color_map}")

    ce_range = kwargs.pop("ce_range", None)
    min_cycle = kwargs.pop("min_cycle", None)
    max_cycle = kwargs.pop("max_cycle", None)

    title = kwargs.pop("title", "Cycle Summary")
    x_label = kwargs.pop("x_label", "Cycle Number")
    x_range = kwargs.pop("x_range", None)
    direction = kwargs.pop("direction", "charge")
    rate = kwargs.pop("rate", False)
    ir = kwargs.pop("ir", True)
    filter_by_group = kwargs.pop("filter_by_group", None)
    filter_by_name = kwargs.pop("filter_by_name", None)
    width = kwargs.pop("width", 1000)
    capacity_specifics = kwargs.pop("capacity_specifics", "gravimetric")

    individual_plot_height = 250
    header_height = 200
    individual_legend_height = 20
    legend_header_height = 20

    hdr_cycle = hdr_summary["cycle_index"]

    hdr_charge, hdr_discharge = _get_capacity_columns(capacity_specifics)

    hdr_ce = hdr_summary["coulombic_efficiency"]
    hdr_ir_charge = hdr_summary["ir_charge"]
    hdr_ir_discharge = hdr_summary["ir_discharge"]
    hdr_charge_rate = hdr_summary["charge_c_rate"]
    hdr_discharge_rate = hdr_summary["discharge_c_rate"]
    hdr_group = hdr_journal.group
    hdr_sub_group = hdr_journal.sub_group

    legend_dict = {"title": "<b>Cell</b>", "orientation": "v"}

    additional_template = "axes_with_borders"
    _make_plotly_template(additional_template)

    available_summaries = summaries.variable.unique()

    color_selector = hdr_group
    symbol_selector = hdr_sub_group
    if inverted_mode:
        color_selector, symbol_selector = symbol_selector, color_selector

    if direction == "discharge":
        hdr_ir = hdr_ir_discharge
        hdr_rate = hdr_discharge_rate
        selected_summaries = [hdr_cycle, hdr_ce, hdr_discharge]
    else:
        selected_summaries = [hdr_cycle, hdr_ce, hdr_charge]
        hdr_ir = hdr_ir_charge
        hdr_rate = hdr_charge_rate

    if ir:
        if hdr_ir in available_summaries:
            selected_summaries.append(hdr_ir)
        else:
            logging.debug("no ir data available")
    if rate:
        if hdr_rate in available_summaries:
            selected_summaries.append(hdr_rate)
        else:
            logging.debug("no rate data available")

    plotted_summaries = selected_summaries[1:]

    summaries = summaries.loc[summaries.variable.isin(selected_summaries), :]
    if max_cycle:
        summaries = summaries.loc[summaries[hdr_cycle] <= max_cycle, :]

    if min_cycle:
        summaries = summaries.loc[summaries[hdr_cycle] >= min_cycle, :]

    labels = _make_labels()
    sub_titles = [labels.get(n, n.replace("_", " ").title()) for n in plotted_summaries]
    if max_cycle or min_cycle:
        sub_titles.append(f"[{min_cycle}, {max_cycle}]")
    sub_titles = ", ".join(sub_titles)

    number_of_cells = len(summaries.cell.unique())
    number_of_rows = len(plotted_summaries)
    legend_height = legend_header_height + individual_legend_height * number_of_cells
    plot_height = max(legend_height, individual_plot_height * number_of_rows)
    total_height = header_height + plot_height

    if filter_by_group is not None:
        if not isinstance(filter_by_group, (list, tuple)):
            filter_by_group = [filter_by_group]
        summaries = summaries.loc[summaries[hdr_group].isin(filter_by_group), :]

    if filter_by_name is not None:
        summaries = summaries.loc[summaries.cell.str.contains(filter_by_name), :]

    # TODO: consider performing a sanity check here

    logging.debug(f"number of cells: {number_of_cells}")
    logging.debug(f"number of rows: {number_of_rows}")
    logging.debug(f"data shape: {summaries.shape}")
    logging.debug(f"data columns: {summaries.columns}")
    logging.debug(f"x and x range: {hdr_cycle}, {x_range}")
    logging.debug(f"color and symbol selectors: {color_selector}, {symbol_selector}")
    logging.debug(f"labels: {labels}")
    logging.debug(f"total height: {total_height}")
    logging.debug(f"width: {width}")
    logging.debug(f"plotted summaries (category_orders): {plotted_summaries}")

    try:
        canvas = px.line(
            summaries,
            x=hdr_cycle,
            y="value",
            facet_row="variable",
            color=color_selector,
            symbol=symbol_selector,
            labels=labels,
            height=total_height,
            width=width,
            category_orders={"variable": plotted_summaries},
            template=f"{base_template}+{additional_template}",
            color_discrete_sequence=color_map,
            title=f"<b>{title}</b><br>{sub_titles}",
            range_x=x_range,
        )
    except Exception as e:
        logging.critical(f"could not create plotly plot ({e})")
        raise e

    logging.debug("plotly plot created")
    logging.debug(f"canvas: {canvas}")

    adjust_row_heights = True
    if number_of_rows == 1:
        domains = [[0.0, 1.00]]
    elif number_of_rows == 2:
        domains = [[0.0, 0.79], [0.8, 1.00]]
    elif number_of_rows == 3:
        domains = [[0.0, 0.39], [0.4, 0.79], [0.8, 1.00]]

    elif number_of_rows == 4:
        domains = [[0.0, 0.24], [0.25, 0.49], [0.5, 0.74], [0.75, 1.00]]

    else:
        adjust_row_heights = False
        domains = None

    canvas.for_each_trace(
        functools.partial(
            _plotly_legend_replacer,
            df=summaries,
            group_legends=group_legends,
            inverted_mode=inverted_mode,
        )
    )

    canvas.for_each_annotation(lambda a: a.update(text=""))
    canvas.update_traces(marker=dict(size=8))

    canvas.update_xaxes(row=1, title_text=f"<b>{x_label}</b>")

    for i, n in enumerate(reversed(plotted_summaries)):
        n = labels.get(n, n.replace("_", " ").title())
        update_kwargs = dict(
            row=i + 1,
            autorange=True,
            matches=None,
            title_text=f"<b>{n}</b>",
        )
        if adjust_row_heights:
            domain = domains[i]
            update_kwargs["domain"] = domain

        canvas.update_yaxes(**update_kwargs)

    if hdr_ce in plotted_summaries and ce_range is not None:
        canvas.update_yaxes(row=number_of_rows, autorange=False, range=ce_range)

    canvas.update_layout(
        legend=legend_dict,
        showlegend=True,
    )
    return canvas


def plot_cycle_life_summary_matplotlib(
    info,
    summaries,
    width=900,
    height=800,
    height_fractions=None,
    legend_option="all",
    **kwargs,
):
    warnings.warn(
        "This utility function is not maintained anymore",
        category=DeprecationWarning,
    )

    logging.debug(f"   * stacking and plotting")
    logging.debug(f"      backend: {config.batch.backend}")
    logging.debug(f"      received kwargs: {kwargs}")

    # Not used (yet?) - requires a more advanced generation of sub-plots
    if height_fractions is None:
        height_fractions = [0.3, 0.4, 0.3]

    # print(" running matplotlib plotter ".center(80,"="))
    # convert from bokeh to matplotlib - figsize - inch-ish
    width /= 80
    height /= 120
    discharge_capacity = summaries[hdr_summary["discharge_capacity_gravimetric"]]
    charge_capacity = summaries[hdr_summary["charge_capacity_gravimetric"]]
    coulombic_efficiency = summaries.coulombic_efficiency
    try:
        ir_charge = summaries.ir_charge
    except AttributeError:
        logging.debug("the data is missing ir charge")
        ir_charge = None

    plt.rcParams["figure.figsize"] = (10, 10)
    marker_types = [
        "o",
        "s",
        "v",
        "^",
        "<",
        ">",
        "8",
        "p",
        "P",
        "*",
        "h",
        "H",
        "+",
        "x",
        "X",
        "D",
        "d",
        ".",
        ",",
    ]

    marker_size = kwargs.pop("marker_size", None)
    group_styles, sub_group_styles = create_plot_option_dicts(
        info, marker_types=marker_types, size=marker_size
    )
    if ir_charge is None:
        canvas, (ax_ce, ax_cap) = plt.subplots(
            2,
            1,
            figsize=(width, height),
            sharex=True,
            gridspec_kw={"height_ratios": height_fractions[:-1]},
        )
    else:
        canvas, (ax_ce, ax_cap, ax_ir) = plt.subplots(
            3,
            1,
            figsize=(width, height),
            sharex=True,
            gridspec_kw={"height_ratios": height_fractions},
        )
    for label in charge_capacity.columns.get_level_values(0):
        name = create_legend(info, label, option=legend_option)
        g, sg = look_up_group(info, label)

        group_style = group_styles[g]
        sub_group_style = sub_group_styles[sg]

        marker = sub_group_style["marker"]
        line = group_style["line"]

        c = line["line_color"]
        m = marker["marker"]
        f = "white"

        try:
            ax_cap.plot(
                charge_capacity[label], label=name, color=c, marker=m, markerfacecolor=c
            )
        except Exception as e:
            logging.debug(f"Could not plot charge capacity for {label} ({e})")
        try:
            ax_cap.plot(
                discharge_capacity[label],
                label=name,
                color=c,
                marker=m,
                markerfacecolor=f,
            )
        except Exception as e:
            logging.debug(f"Could not plot discharge capacity for {label} ({e})")

        ax_ce.plot(
            coulombic_efficiency[label],
            label=name,
            color=c,
            marker=m,
            markerfacecolor=c,
        )

        if ir_charge is not None:
            try:
                ax_ir.plot(
                    ir_charge[label], color=c, label=name, marker=m, markerfacecolor=c
                )
            except Exception as e:
                logging.debug(f"Could not plot IR for {label} ({e})")

    ax_all = [ax_cap, ax_ce]
    ax_ce.set_ylabel("Coulombic\nEfficiency (%)")
    ax_ce.set_ylim((0, 110))
    ax_cap.set_ylabel("Capacity\n(mAh/g)")

    if ir_charge is not None:
        ax_ir.set_ylabel("IR\n(charge)")
        ax_ir.set_xlabel("Cycle")
        ax_all.append(ax_ir)
    else:
        ax_cap.set_xlabel("Cycle")

    for ax in ax_all:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.6, box.height])

    # Put a legend to the right of the current axis
    legend = ax_cap.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    legend.get_frame().set_facecolor("none")
    legend.get_frame().set_linewidth(0.0)

    return canvas


