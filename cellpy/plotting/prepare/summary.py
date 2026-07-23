"""Summary-plot prepare path: tidy frame + FigureSpec (#638).

Extracted from ``cellpy.utils.plotutils.SummaryPlotDataPreparer``. Public
``summary_plot`` calls :func:`prepare` then hands ``(frame, spec)`` to a
backend renderer.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

import cellpy.plotting.registry as registry
from cellpy.plotting.context import from_source
from cellpy.plotting.spec import AxisSpec, FigureSpec, PanelSpec

logger = logging.getLogger(__name__)

_NORMALIZED_CYCLE_INDEX = "normalized_cycle_index"
Y_HEADER = "value"
COLOR = "variable"
ROW = "row"
COL_ID = "cycle_type"


def _plotly_top_row_label(y: str) -> Optional[str]:
    if y.endswith("_efficiency"):
        return "Coulombic Efficiency"
    if y.endswith("_with_rate"):
        return "C-rate (1/h)"
    return None


def _capacity_unit(c: Any, mode: str = "gravimetric") -> str:
    from cellpy.exceptions import UnitsError
    from cellpy.units import units_label

    try:
        return units_label("charge", mode, units=c.cellpy_units)
    except UnitsError:
        return "-"


def _range_tuple(value: Any) -> Optional[tuple[float, float]]:
    if value is None:
        return None
    return (float(value[0]), float(value[1]))


def _build_formation_extras(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    config: Any,
    number_of_rows: int,
    max_cycle: Any,
    min_cycle: Any,
    max_val_normalized_col: float,
    formation_cycle_selector: Any,
    c: Any,
    additional_kwargs: dict,
) -> dict[str, Any]:
    """Pre-compute formation / no-formation layout knobs for PlotlyBackend."""
    show_y_labels_on_right_pane = additional_kwargs.get(
        "show_y_labels_on_right_pane", False
    )
    plotly_row_ratios = additional_kwargs.get(
        "fullcell_standard_row_height_ratios", [0.3, 0.6, 0.9]
    )
    plotly_row_space = additional_kwargs.get("fullcell_standard_row_space", 0.02)
    top_row_label = _plotly_top_row_label(y) if number_of_rows == 2 else None
    capacity_unit = None
    if y.startswith("fullcell_standard_"):
        capacity_unit = _capacity_unit(c, mode=y.split("_")[-1])

    if config.show_formation:
        x_axis_domain_formation = [
            0.0,
            config.x_axis_domain_formation_fraction - config.column_separator / 2,
        ]
        x_axis_domain_rest = [
            config.x_axis_domain_formation_fraction + config.column_separator / 2,
            0.95,
        ]
        max_cycle_formation = data.loc[formation_cycle_selector, x].max()
        min_cycle_rest = data.loc[~formation_cycle_selector, x].min()
        dd = 0.1 if x == _NORMALIZED_CYCLE_INDEX else 0.4
        x_axis_range_formation = [min_cycle - dd, max_cycle_formation + dd]
        x_axis_range_rest = [min_cycle_rest - dd, max_cycle + dd]
        if config.x_range is not None:
            x_axis_range_rest = [
                x_axis_range_rest[0],
                min(config.x_range[1], x_axis_range_rest[1]),
            ]

        row_y_ranges: list[Optional[list]] = [None] * number_of_rows
        if number_of_rows == 2:
            row_y_ranges[0] = config.y_range
            row_y_ranges[1] = config.ce_range
        elif number_of_rows == 4 and y.startswith("fullcell_standard_"):
            row_y_ranges[0] = config.cv_share_range
            if config.fullcell_standard_normalization_type is not False:
                row_y_ranges[1] = config.norm_range or [
                    0.0,
                    max(
                        max_val_normalized_col,
                        config.fullcell_standard_normalization_scaler,
                    ),
                ]
            row_y_ranges[2] = config.y_range
            row_y_ranges[3] = config.ce_range

        fullcell = None
        if number_of_rows == 4 and y.startswith("fullcell_standard_"):
            fullcell = {
                "plotly_row_ratios": list(plotly_row_ratios),
                "plotly_row_space": plotly_row_space,
                "capacity_unit": capacity_unit,
                "y": y,
                "show_formation": True,
                "x_axis_domain_formation_fraction": config.x_axis_domain_formation_fraction,
                "link_capacity_scales": config.link_capacity_scales,
                "normalization_type": config.fullcell_standard_normalization_type,
                "normalization_factor": config.fullcell_standard_normalization_factor,
                "normalization_scaler": config.fullcell_standard_normalization_scaler,
            }

        return {
            "show_formation": True,
            "formation_layout": {
                "n_rows": number_of_rows,
                "x_axis_domain_formation": x_axis_domain_formation,
                "x_axis_domain_rest": x_axis_domain_rest,
                "x_axis_range_formation": x_axis_range_formation,
                "x_axis_range_rest": x_axis_range_rest,
                "show_y_labels_on_right_pane": show_y_labels_on_right_pane,
                "row_y_ranges": row_y_ranges,
                "top_row_label": top_row_label,
                "fullcell_standard_domains": fullcell,
            },
            "no_formation_layout": None,
            "capacity_unit": capacity_unit,
            "top_row_label": _plotly_top_row_label(y),
            "plotly_row_ratios": list(plotly_row_ratios),
            "plotly_row_space": plotly_row_space,
        }

    return {
        "show_formation": False,
        "formation_layout": None,
        "no_formation_layout": {
            "y": y,
            "number_of_rows": number_of_rows,
            "max_val_normalized_col": max_val_normalized_col,
            "top_row_label": _plotly_top_row_label(y),
            "capacity_unit": capacity_unit,
            "plotly_row_ratios": list(plotly_row_ratios),
            "plotly_row_space": plotly_row_space,
            "ce_range": config.ce_range,
            "y_range": config.y_range,
            "norm_range": config.norm_range,
            "cv_share_range": config.cv_share_range,
            "fullcell_standard_normalization_type": config.fullcell_standard_normalization_type,
            "fullcell_standard_normalization_factor": config.fullcell_standard_normalization_factor,
            "fullcell_standard_normalization_scaler": config.fullcell_standard_normalization_scaler,
        },
        "capacity_unit": capacity_unit,
        "top_row_label": _plotly_top_row_label(y),
        "plotly_row_ratios": list(plotly_row_ratios),
        "plotly_row_space": plotly_row_space,
    }


def _build_figure_spec(
    prepared: dict[str, Any],
    *,
    family: Any,
    config: Any,
    c: Any,
) -> FigureSpec:
    data = prepared["data"]
    x = config.x if config.x is not None else c.schema.summary.cycle_num
    y = config.y
    number_of_rows = prepared["number_of_rows"]
    additional_kwargs = dict(getattr(config, "additional_kwargs", {}) or {})

    panels = tuple(
        PanelSpec(
            columns=tuple(family.columns(c.headers_summary)) if i == 0 else (),
            y_axis=AxisSpec(),
        )
        for i in range(max(number_of_rows, 1))
    )

    layout = _build_formation_extras(
        data,
        x=x,
        y=y,
        config=config,
        number_of_rows=number_of_rows,
        max_cycle=prepared["max_cycle"],
        min_cycle=prepared["min_cycle"],
        max_val_normalized_col=prepared["max_val_normalized_col"],
        formation_cycle_selector=prepared["formation_cycle_selector"],
        c=c,
        additional_kwargs=additional_kwargs,
    )

    title = config.title
    if title is None:
        title = f"Summary <b>{c.cell_name}</b>"

    extras: dict[str, Any] = {
        "x": x,
        "y": y,
        "y_header": Y_HEADER,
        "y_label": prepared["y_label"],
        "color": COLOR,
        "row": ROW,
        "col_id": COL_ID,
        "number_of_rows": number_of_rows,
        "cell_name": c.cell_name,
        "prepared_data_info": {
            "number_of_rows": prepared["number_of_rows"],
            "x_label": prepared["x_label"],
            "y_label": prepared["y_label"],
            "max_cycle": prepared["max_cycle"],
            "min_cycle": prepared["min_cycle"],
            "max_val_normalized_col": prepared["max_val_normalized_col"],
            "formation_cycle_selector": prepared["formation_cycle_selector"],
        },
        "render": {
            "height": config.height,
            "width": config.width,
            "markers": config.markers,
            "title": title,
            "split": config.split,
            "hover_columns": list(config.hover_columns or []),
            "show_legend": config.show_legend,
            "show_formation": config.show_formation,
            "share_y": config.share_y,
            "rangeslider": config.rangeslider,
            "auto_convert_legend_labels": config.auto_convert_legend_labels,
            "y_range": config.y_range,
            "x_range": config.x_range,
            "plotly_template": config.plotly_template,
            "additional_kwargs": additional_kwargs,
            **layout,
        },
    }

    return FigureSpec(
        panels=panels,
        x_axis=AxisSpec(label=prepared["x_label"], range=_range_tuple(config.x_range)),
        title=title,
        supports_formation=bool(getattr(family, "supports_formation", True))
        and bool(config.show_formation),
        extras=extras,
    )


def prepare(
    source: Any,
    family: Any,
    config: Any,
    plot_info: Any = None,
) -> tuple[pd.DataFrame, FigureSpec]:
    """Prepare a tidy summary frame and a :class:`FigureSpec`.

    Args:
        source: ``CellpyCell`` or :class:`~cellpy.plotting.context.CellContext`.
        family: registered :class:`~cellpy.plotting.registry.PlotFamily`.
        config: ``SummaryPlotConfig`` (or duck-typed equivalent).
        plot_info: optional ``SummaryPlotInfo``; built from the cell when omitted.

    Returns:
        ``(frame, spec)`` — frame shape matches the pre-#638 preparer output.
    """
    ctx = from_source(source)
    c = ctx.cell
    if plot_info is None:
        from cellpy.utils.plotutils import SummaryPlotInfo

        plot_info = SummaryPlotInfo(c)

    # Ensure registry agrees with config.y (family may be passed explicitly).
    if getattr(family, "name", None) and family.name != config.y:
        raise ValueError(
            f"family.name {family.name!r} does not match config.y {config.y!r}"
        )

    prepared = SummaryPlotDataPreparer().prepare_data(c, config, plot_info)
    spec = _build_figure_spec(prepared, family=family, config=config, c=c)
    return prepared["data"], spec


class SummaryPlotDataPreparer:
    """Handles data collection and transformation for summary plots.

    Data preparation for summary_plot (extracted from the pre-2.0 monolith)
    to improve maintainability and testability.
    """

    def __init__(self):
        self.y_header = "value"
        self.color = "variable"
        self.row = "row"
        self.col_id = "cycle_type"

    def prepare_data(
        self,
        c: Any,
        config: Any,
        plot_info: Any,
    ) -> dict:
        """Prepare data for plotting.

        Args:
            c: cellpy object
            config: SummaryPlotConfig with all parameters
            summary_plot_info: SummaryPlotInfo containing information about pre-defined columns and labels
        Returns:
            Dictionary with keys:
                - data: prepared DataFrame
                - number_of_rows: number of rows for subplot layout
                - x_label: x-axis label
                - y_label: y-axis label
                - max_cycle: maximum cycle number
                - min_cycle: minimum cycle number
                - max_val_normalized_col: max value for normalized columns
                - formation_cycle_selector: boolean selector for formation cycles
        """
        x = config.x if config.x is not None else c.schema.summary.cycle_num
        y = config.y
        registry.get(y)

        number_of_rows = 1
        max_val_normalized_col = 0.0

        if config.hover_columns and (
            y.startswith("fullcell_standard_")
            or y.endswith("_split_constant_voltage")
        ):
            logging.warning(
                "summary_plot: hover_columns is currently only supported for "
                "standard plot types; ignoring for y=%r",
                y,
            )

        # Prepare data based on plot type
        if y.startswith("fullcell_standard_"):
            s, number_of_rows = self._prepare_fullcell_standard_data(
                c, x, y, plot_info.y_cols, plot_info.y_trans, config
            )
            max_val_normalized_col = (
                s.loc[s["variable"].str.contains("retention"), "value"].max()
                if len(s.loc[s["variable"].str.contains("retention")]) > 0
                else 0.0
            )
        elif y.endswith("_split_constant_voltage"):
            s, number_of_rows = self._prepare_cv_split_data(
                c, x, y, plot_info.y_cols, config
            )
        else:
            s, number_of_rows = self._prepare_standard_data(
                c, x, y, plot_info.y_cols, config
            )

        # Calculate cycle ranges
        max_cycle = s[x].max()
        min_cycle = s[x].min()

        # Get labels
        x_label = plot_info.x_axis_labels.get(x, x)
        if y in plot_info.y_axis_label:
            y_label = plot_info.y_axis_label.get(y, y)
        else:
            y_label = y.replace("_", " ").title()

        # Mark formation cycles
        formation_cycle_selector = self._mark_formation_cycles(
            s, x, config.formation_cycles, self.col_id
        )

        return {
            "data": s,
            "number_of_rows": number_of_rows,
            "x_label": x_label,
            "y_label": y_label,
            "max_cycle": max_cycle,
            "min_cycle": min_cycle,
            "max_val_normalized_col": max_val_normalized_col,
            "formation_cycle_selector": formation_cycle_selector,
        }

    def _prepare_fullcell_standard_data(
        self, c, x, y, y_cols, y_trans, config
    ) -> tuple:
        """Prepare data for fullcell_standard plots."""

        # The figure has 4 rows: coulombic efficiency, capacity, capacity retention, and CV capacity
        number_of_rows = 4
        column_set = y_cols[y]

        summary = self._preprocess_summary(c, c.data.summary, config)
        if summary.index.name == x:
            summary = summary.reset_index(drop=False)

        # Get CV-only summary
        summary_only_cv = c.make_summary(
            selector_type="only-cv", create_copy=True
        ).data.summary
        if summary_only_cv.index.name == x:
            summary_only_cv = summary_only_cv.reset_index(drop=False)

        # Merge summaries
        s = summary.merge(summary_only_cv, on=x, how="outer", suffixes=("", "_cv"))
        s = s.reset_index(drop=True)
        s = s.melt(x)
        s = s.loc[s.variable.isin(column_set)]

        s[self.row] = 1  # default row for capacity

        # Set row numbers using regex patterns
        s.loc[s["variable"].str.contains(r"_efficiency$"), self.row] = (
            0  # coulombic efficiency
        )
        s.loc[s["variable"].str.contains(r"cumulated.*loss"), self.row] = (
            2  # cumulated loss
        )
        s.loc[s["variable"].str.startswith(r"mod_01_"), self.row] = (
            2  # capacity retention
        )
        s.loc[s["variable"].str.contains(r"_cv$"), self.row] = 3  # cv data

        # Reset losses if requested
        if config.reset_losses:
            logging.debug("Resetting losses")
            first_values = (
                s[s["variable"].str.contains(r"cumulated.*loss")]
                .groupby("variable")["value"]
                .transform("first")
            )
            mask = s["variable"].str.contains(r"cumulated.*loss")
            s.loc[mask, "value"] = s.loc[mask, "value"] - first_values

        # Apply normalization if requested
        if config.fullcell_standard_normalization_type is not False:
            logging.debug("Applying normalization")
            s, max_val_normalized_col = self._apply_normalization(
                s, y, y_trans, config, self.row
            )

        return s, number_of_rows

    def _prepare_cv_split_data(self, c, x, y, y_cols, config) -> tuple:
        """Prepare data for CV split plots."""
        import warnings

        if y.startswith("capacities_gravimetric"):
            cap_type = "capacities_gravimetric"
        elif y.startswith("capacities_areal"):
            cap_type = "capacities_areal"
        elif y.startswith("capacities_absolute"):
            cap_type = "capacities_absolute"
        else:
            raise ValueError(f"Unknown capacity type for CV split: {y}")

        column_set = y_cols[cap_type]

        # Use partition_summary_cv_steps function (lives in plotutils for now)
        from cellpy.utils.plotutils import partition_summary_cv_steps

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = partition_summary_cv_steps(
                c, x, column_set, config.split, self.color, self.y_header
            )

        number_of_rows = 3 if config.split else 1

        return s, number_of_rows

    def _prepare_standard_data(self, c, x, y, y_cols, config) -> tuple:
        """Prepare data for standard plots."""
        column_set = y_cols[y]
        if isinstance(column_set, str):
            column_set = [column_set]

        summary = self._preprocess_summary(c, c.data.summary, config)
        summary = summary.reset_index()

        # Check if requested columns exist in summary
        # For absolute capacities, fall back to base columns if _absolute columns don't exist
        available_columns = set(summary.columns)
        requested_columns = set(column_set)
        missing_columns = requested_columns - available_columns

        if missing_columns and y == "capacities_absolute":
            # For absolute capacities, if _absolute columns don't exist, use base columns
            hdr = c.headers_summary
            base_columns = [hdr.charge_capacity_raw, hdr.discharge_capacity_raw]
            # Check if base columns exist
            if all(col in available_columns for col in base_columns):
                column_set = base_columns
            else:
                # If base columns also don't exist, keep original column_set
                # This will result in empty DataFrame, which will be handled downstream
                pass
        elif missing_columns:
            # For other capacity types, if columns are missing, keep original column_set
            # This will result in empty DataFrame, which will be handled downstream
            pass

        hover_cols = list(config.hover_columns or [])
        if hover_cols:
            missing = [h for h in hover_cols if h not in summary.columns]
            if missing:
                logging.warning(
                    "summary_plot: dropping unknown hover_columns %s "
                    "(available: %s)",
                    missing,
                    sorted(summary.columns),
                )
                hover_cols = [h for h in hover_cols if h in summary.columns]
            # Avoid duplicating x and value columns in id_vars
            hover_cols = [h for h in hover_cols if h != x and h not in column_set]

        id_vars = [x, *hover_cols]
        s = summary.melt(id_vars=id_vars)
        s = s.loc[s.variable.isin(column_set)]
        s = s.reset_index(drop=True)

        # Check if we have any data after filtering
        if len(s) == 0:
            raise ValueError(
                f"No data found for plot type '{y}'. "
                f"Requested columns: {column_set}. "
                f"Available columns in summary: {list(available_columns)}"
            )

        s[self.row] = 1

        number_of_rows = 1
        if config.split:
            if y.endswith("_efficiency"):
                s[self.row] = 1
                s.loc[s["variable"].str.contains("efficiency"), self.row] = 0
                number_of_rows = 2
            elif y.endswith("_with_rate"):
                hdr = c.headers_summary
                rate_cols = {hdr.charge_c_rate, hdr.discharge_c_rate}
                s[self.row] = 1
                s.loc[s["variable"].isin(rate_cols), self.row] = 0
                number_of_rows = 2

        return s, number_of_rows

    def _apply_normalization(self, s, y, y_trans, config, row_col) -> tuple:
        """Apply normalization transformations to data."""
        import re
        from collections.abc import Iterable

        max_val_normalized_col = 0.0
        normalization_factor = config.fullcell_standard_normalization_factor
        normalization_type = config.fullcell_standard_normalization_type
        normalization_cycle_numbers = (
            config.fullcell_standard_normalization_cycle_numbers
        )

        # TODO: check if this is really needed!!
        # Determine normalization factor if not provided
        if normalization_factor is None:
            logging.debug(
                f"No normalization factor provided for {y}, using {normalization_type}"
            )

        if y.startswith("fullcell_standard_cumloss_") and normalization_type != "max":
            logging.debug("only allowing for 'max' for cumloss plots")
            normalization_type = "max"

        if normalization_type in ["on-cycles", "on-cycle"]:
            if normalization_cycle_numbers is None:
                raise ValueError(
                    "Normalization cycle numbers are required for on-cycles normalization"
                )
            if isinstance(normalization_cycle_numbers, Iterable):
                cycle_numbers = [cycle - 1 for cycle in normalization_cycle_numbers]
            else:
                cycle_numbers = [normalization_cycle_numbers - 1]
            normalization_cycle_numbers = cycle_numbers

        trans_kwargs = dict(
            normalization_factor=normalization_factor,
            normalization_type=normalization_type,
            normalization_scaler=config.fullcell_standard_normalization_scaler,
            normalization_indexes=normalization_cycle_numbers,
        )

        # Transform the data
        max_row_val = s[row_col].max()
        for col, trans_dict in y_trans.get(y, {}).items():
            for (new_row_val, new_col), trans in trans_dict.items():
                if new_col in s["variable"].values:
                    # Transforming on existing column
                    s.loc[s["variable"] == col, "value"] = trans(
                        s.loc[s["variable"] == col, "value"].values, **trans_kwargs
                    )
                else:
                    # Creating new column
                    old_col = col
                    if new_row_val is not None:
                        row_val = new_row_val
                    else:
                        row_val = s.loc[s["variable"] == col, row_col]
                        if not row_val.empty:
                            row_val = row_val.values[0]
                        else:
                            max_row_val += 1
                            row_val = max_row_val

                    if old_col.startswith("mod_"):
                        old_col = re.sub(r"^mod_\d{2}_", "", old_col)
                    new_col_frame_section = s.loc[s["variable"] == old_col].copy()
                    new_col_frame_section["variable"] = new_col
                    new_col_frame_section[row_col] = row_val
                    transformed_values = trans(
                        new_col_frame_section["value"].values, **trans_kwargs
                    )
                    new_col_frame_section["value"] = transformed_values
                    s = pd.concat([s, new_col_frame_section], ignore_index=True)
                    s = s.reset_index(drop=True)
                    s = s.sort_values(by=[row_col, "variable"])

                max_val_normalized_col = s.loc[s["variable"] == new_col, "value"].max()

        return s, max_val_normalized_col

    def _mark_formation_cycles(self, s, x, formation_cycles, col_id):
        """Mark formation cycles in the data."""
        formation_cycle_selector = slice(None, None)
        if formation_cycles > 0:
            formation_cycle_selector = s[x] <= formation_cycles
            s[col_id] = "standard"
            s.loc[formation_cycle_selector, col_id] = "formation"
        return formation_cycle_selector

    @staticmethod
    def _preprocess_summary(c: Any, summary: pd.DataFrame, config) -> pd.DataFrame:
        """Apply optional rate-rescaling and row filtering to a summary copy.

        Two opt-in steps, both no-ops when their config field is ``None``:

        * ``config.nominal_capacity`` rescales the existing
          ``charge_c_rate`` / ``discharge_c_rate`` columns to use a new
          nominal capacity instead of the one set on the cell. The
          rescale factor is ``c.data.nom_cap / nominal_capacity``: since
          ``rate = current / nom_cap``, the rate columns are multiplied
          by ``old_nom_cap / new_nom_cap``.
        * ``config.filters`` is forwarded to
          :func:`cellpy.filters.filter_summary`. The default
          ``rate_filter_columns`` resolves to both rate columns from
          ``c.headers_summary`` (charge AND discharge).

        Operates on a copy; the caller's ``summary`` argument is not
        mutated.
        """
        out = summary.copy() if summary is not None else summary

        if config.nominal_capacity is not None:
            hdr = c.headers_summary
            old_nom_cap = getattr(c.data, "nom_cap", None)
            if old_nom_cap in (None, 0):
                logging.warning(
                    "summary_plot: nominal_capacity override requested but "
                    "cell.data.nom_cap is %r; skipping rate rescale.",
                    old_nom_cap,
                )
            else:
                scale = float(old_nom_cap) / float(config.nominal_capacity)
                for col in (hdr.charge_c_rate, hdr.discharge_c_rate):
                    if col in out.columns:
                        out[col] = out[col] * scale
                logging.debug(
                    "summary_plot: rescaled rate columns by %.6g "
                    "(old nom_cap=%s, new=%s)",
                    scale,
                    old_nom_cap,
                    config.nominal_capacity,
                )

        if config.filters:
            from cellpy.filters import filter_summary

            hdr = c.headers_summary
            filter_kwargs = dict(config.filters)
            if (
                "rate" in filter_kwargs
                and "rate_columns" not in filter_kwargs
            ):
                if config.rate_filter_columns is not None:
                    filter_kwargs["rate_columns"] = config.rate_filter_columns
                else:
                    filter_kwargs["rate_columns"] = (
                        hdr.charge_c_rate,
                        hdr.discharge_c_rate,
                    )
            before = len(out)
            out = filter_summary(out, **filter_kwargs)
            logging.debug(
                "summary_plot: filters %s reduced rows %d -> %d",
                filter_kwargs,
                before,
                len(out),
            )

        return out


