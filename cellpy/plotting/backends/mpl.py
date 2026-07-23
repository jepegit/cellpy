"""Matplotlib backend for prepare → spec → render (#639).

Seaborn provides palette/style/faceting helpers only; the public backend name
is ``matplotlib``.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any, Optional

import numpy as np
import pandas as pd

from cellpy.exceptions import UnitsError
from cellpy.plotting.spec import FigureSpec
from cellpy.units import units_label

logger = logging.getLogger(__name__)


def _seaborn_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("seaborn") is not None


def _capacity_unit(c: Any, mode: str = "gravimetric") -> str:
    try:
        return units_label("charge", mode, units=c.cellpy_units)
    except UnitsError:
        return "-"


def _seaborn_top_row_label(y: str) -> Optional[str]:
    if y.endswith("_efficiency"):
        return "Coulombic\nEfficiency (%)"
    if y.endswith("_with_rate"):
        return "C-rate\n(1/h)"
    return None


def _has_special_top_row(y: str) -> bool:
    return y.endswith("_efficiency") or y.endswith("_with_rate")


class MatplotlibBackend:
    """Matplotlib backend for summary ``render(frame, spec)`` (#639).

    Seaborn is used only for palette/style/faceting helpers (``relplot``),
    not as a public backend name. Ported from ``SeabornPlotBuilder``.
    """

    name = "matplotlib"

    def __init__(self) -> None:
        self.y_header = "value"
        self.color = "variable"
        self.row = "row"
        self.col_id = "cycle_type"

    def render(self, frame: Any, spec: FigureSpec) -> Any:
        """Render a tidy frame according to *spec* (matplotlib Figure)."""
        extras = dict(spec.extras or {})
        config = extras.get("config")
        c = extras.get("cell")
        if config is None or c is None:
            raise ValueError(
                "FigureSpec.extras must include 'config' and 'cell' for "
                "MatplotlibBackend.render"
            )
        prepared_data_info = dict(extras.get("prepared_data_info") or {})
        prepared_data_info.setdefault("number_of_rows", extras.get("number_of_rows"))
        prepared_data_info.setdefault(
            "x_label", getattr(spec.x_axis, "label", None)
        )
        prepared_data_info.setdefault("y_label", extras.get("y_label"))
        additional_kwargs = dict(getattr(config, "additional_kwargs", {}) or {})
        return self._build_plot(
            frame, prepared_data_info, config, additional_kwargs, c
        )

    def _build_plot(
        self,
        data: Any,
        prepared_data_info: dict,
        config: Any,
        additional_kwargs: dict,
        c: Any,
    ) -> Any:
        """Build matplotlib figure via seaborn styling/faceting helpers.

        Args:
        """
        if not _seaborn_available():
            warnings.warn(
                "seaborn not available, returning only the data so that you can plot it yourself instead"
            )
            return data

        import seaborn as sns
        import matplotlib.pyplot as plt

        # Extract seaborn-specific parameters
        seaborn_facecolor = additional_kwargs.pop("seaborn_facecolor", "#EAEAF2")
        seaborn_edgecolor = additional_kwargs.pop("seaborn_edgecolor", "black")
        seaborn_style_dict_default = {
            "axes.facecolor": seaborn_facecolor,
            "axes.edgecolor": seaborn_edgecolor,
        }
        seaborn_style_dict = additional_kwargs.pop(
            "seaborn_style_dict", seaborn_style_dict_default
        )
        seaborn_marker_size = additional_kwargs.pop("seaborn_marker_size", 7)
        xlim_formation = additional_kwargs.pop(
            "xlim_formation", (0.6, config.formation_cycles + 0.4)
        )

        # Set default title if not provided
        title = config.title
        if title is None:
            title = f"Summary {c.cell_name}"

        x = config.x if config.x is not None else c.schema.summary.cycle_num
        y = config.y
        number_of_rows = prepared_data_info["number_of_rows"]
        x_label = prepared_data_info["x_label"]
        y_label = prepared_data_info["y_label"]
        max_cycle = prepared_data_info["max_cycle"]
        max_val_normalized_col = prepared_data_info["max_val_normalized_col"]

        # Set up seaborn
        sns.set_style(config.seaborn_style, seaborn_style_dict)
        sns.set_palette(config.seaborn_palette)
        sns.set_context(additional_kwargs.pop("seaborn_context", "notebook"))

        # Configure facet and gridspec kwargs
        facet_kws = dict(despine=False, sharex=False, sharey=False)
        gridspec_kws = dict(hspace=0.07)

        # Configure columns for formation cycles
        col_id = None
        if config.show_formation and self.col_id in data.columns:
            additional_kwargs["col"] = self.col_id
            number_of_cols = 2
            col_id = self.col_id
            gridspec_kws["width_ratios"] = additional_kwargs.pop("width_ratios", [1, 6])
            gridspec_kws["wspace"] = additional_kwargs.pop("wspace", 0.02)
        else:
            number_of_cols = 1

        # Configure rows
        # Note: number_of_rows from prepared_data_info is the expected number,
        # but we need to verify it matches the actual data
        row_id = None
        if not config.split:
            number_of_rows = 1
            logging.debug(f"split=False, setting number_of_rows=1")
        else:
            row_id = self.row
            if self.row in data.columns:
                additional_kwargs["row"] = self.row
                actual_number_of_rows = data[self.row].nunique()
                # Use the actual number from data, but log if it differs from expected
                if actual_number_of_rows != number_of_rows:
                    logging.warning(
                        f"Number of rows mismatch: expected {number_of_rows} from data preparer, "
                        f"but data has {actual_number_of_rows} unique row values. Using {actual_number_of_rows}."
                    )
                number_of_rows = actual_number_of_rows
                logging.debug(
                    f"split=True, row column '{self.row}' found, number_of_rows={number_of_rows}"
                )
            else:
                # If split=True but row column doesn't exist, fall back to 1 row
                logging.warning(
                    f"split=True but row column '{self.row}' not found in data. "
                    f"Expected {number_of_rows} rows but falling back to 1 row."
                )
                number_of_rows = 1
                logging.debug(
                    f"split=True but row column '{self.row}' not found, setting number_of_rows=1"
                )

        # Calculate plot properties
        plot_type = (
            "fullcell_standard" if y.startswith("fullcell_standard_") else "default"
        )
        seaborn_plot_height, seaborn_plot_aspect = (
            self._calculate_seaborn_plot_properties(
                number_of_rows, number_of_cols, plot_type
            )
        )
        seaborn_plot_height = additional_kwargs.pop(
            "seaborn_plot_height", seaborn_plot_height
        )
        seaborn_plot_aspect = additional_kwargs.pop(
            "seaborn_plot_aspect", seaborn_plot_aspect
        )

        # Calculate axis limits
        eff_lim = config.ce_range
        if eff_lim is None:
            eff_lim = self._calculate_efficiency_limits(data)

        x_range = config.x_range
        if x_range is None:
            cycle_range = max_cycle - config.formation_cycles
            if cycle_range <= 0:
                cycle_range = 10  # arbitrary value
            x_range = (
                config.formation_cycles + 1 - 0.02 * abs(cycle_range),
                max_cycle + 0.02 * abs(cycle_range),
            )

        y_range = config.y_range
        if y_range is None:
            y_range = self._calculate_y_range(data)

        # Build info_dicts for axis configuration
        info_dicts = self._build_axis_info_dicts(
            y,
            config,
            number_of_rows,
            x_range,
            y_range,
            eff_lim,
            xlim_formation,
            x_label,
            y_label,
            max_val_normalized_col,
            c,
        )

        # Configure facet_kws based on plot type. ``_efficiency`` and
        # ``_with_rate`` share the same row-0-is-different layout:
        # disable shared y-axis and give the top row a smaller height.
        is_efficiency_plot = y.endswith("_efficiency")
        is_special_top_row = _has_special_top_row(y)
        if is_special_top_row:
            facet_kws["sharey"] = False
            if number_of_rows == 2:
                gridspec_kws["height_ratios"] = [1, 4]
            else:
                logging.debug(
                    f"Special-top-row plot with {number_of_rows} rows - not setting height_ratios"
                )

        facet_kws["gridspec_kws"] = gridspec_kws

        # Log configuration for debugging
        logging.debug("Seaborn plot configuration:")
        logging.debug(
            f"  y={y}, split={config.split}, number_of_rows={number_of_rows}, number_of_cols={number_of_cols}"
        )
        logging.debug(f"  row_id={row_id}, col_id={col_id}")
        logging.debug(f"  is_efficiency_plot={is_efficiency_plot}")
        logging.debug(f"  gridspec_kws={gridspec_kws}")
        logging.debug(f"  additional_kwargs keys: {list(additional_kwargs.keys())}")
        if config.verbose:
            logging.info("Seaborn plot configuration:")
            logging.info(
                f"  y={y}, number_of_rows={number_of_rows}, number_of_cols={number_of_cols}"
            )
            logging.info(f"  row_id={row_id}, col_id={col_id}")
            logging.info(f"  is_efficiency_plot={is_efficiency_plot}")
            logging.info(f"  gridspec_kws={gridspec_kws}")
            logging.info(f"  additional_kwargs keys: {list(additional_kwargs.keys())}")

        # Create the plot
        # Suppress tight_layout warning from seaborn when using gridspec_kws
        # (seaborn calls tight_layout internally on axes that may be incompatible)
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*tight_layout.*",
                category=UserWarning,
                module="seaborn.axisgrid",
            )
            sns_fig = sns.relplot(
                data=data,
                x=x,
                y=self.y_header,
                hue=self.color,
                height=seaborn_plot_height,
                aspect=seaborn_plot_aspect,
                kind="line",
                marker="o" if config.markers else None,
                legend=config.show_legend,
                **additional_kwargs,
                facet_kws=facet_kws,
            )

        sns_fig.set_axis_labels(x_label, y_label)

        # Convert legend labels if requested
        if config.auto_convert_legend_labels and config.show_legend:
            self._convert_legend_labels(sns_fig)

        # Set marker sizes
        if config.markers:
            for ax in sns_fig.axes.flat:
                lines = ax.get_lines()
                for line in lines:
                    line.set_markersize(seaborn_marker_size)

        # Apply line hooks if provided
        if config.seaborn_line_hooks:
            for ax in sns_fig.axes.flat:
                lines = ax.get_lines()
                for line in lines:
                    for hook, args, hook_kwargs in config.seaborn_line_hooks:
                        if hasattr(line, hook):
                            getattr(line, hook)(*args, **hook_kwargs)

        # Clean up axes and set title
        fig = sns_fig.figure
        self._clean_up_axis(fig, info_dicts=info_dicts, row_id=row_id, col_id=col_id)
        fig.align_ylabels()
        _hack_to_position_legend = {1: 0.97, 2: 0.95, 3: 0.92, 4: 0.92, 5: 0.92}
        fig.suptitle(title, y=_hack_to_position_legend.get(number_of_rows, 0.92))

        plt.close(fig)
        return fig

    def _calculate_seaborn_plot_properties(
        self, number_of_rows: int, number_of_cols: int, plot_type: str = "default"
    ) -> tuple:
        """Calculate seaborn plot height and aspect ratio."""
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

    def _calculate_efficiency_limits(self, data: pd.DataFrame) -> list:
        """Calculate efficiency axis limits from data."""
        eff_vals = (
            data.loc[data[self.color].str.contains("_efficiency"), self.y_header]
            .pipe(pd.to_numeric, errors="coerce")
            .dropna()
        )
        if len(eff_vals) == 0:
            return [0, 100]
        eff_min, eff_max = eff_vals.min(), eff_vals.max()
        return [eff_min - 0.05 * abs(eff_min), eff_max + 0.05 * abs(eff_max)]

    def _calculate_y_range(self, data: pd.DataFrame) -> list:
        """Calculate y-axis range from data."""
        y_vals = (
            data.loc[~data[self.color].str.contains("_efficiency"), self.y_header]
            .pipe(pd.to_numeric, errors="coerce")
            .dropna()
        )
        if len(y_vals) == 0:
            return [0, 1]
        min_value, max_value = y_vals.min(), y_vals.max()
        return [
            min_value - 0.05 * abs(min_value),
            max_value + 0.05 * abs(max_value),
        ]

    def _build_axis_info_dicts(
        self,
        y: str,
        config: Any,
        number_of_rows: int,
        x_range: tuple,
        y_range: list,
        eff_lim: Optional[list],
        xlim_formation: tuple,
        x_label: str,
        y_label: str,
        max_val_normalized_col: float,
        c: Any,
    ) -> list:
        """Build info dictionaries for axis configuration."""
        info_dicts = []
        is_efficiency_plot = y.endswith("_efficiency")
        is_fullcell_standard_plot = y.startswith("fullcell_standard_")
        is_split_constant_voltage_plot = y.endswith("_split_constant_voltage")

        _efficiency_label = r"Efficiency (%)"

        if is_efficiency_plot:
            info_dicts.extend(
                self._build_efficiency_plot_info_dicts(
                    config, x_range, y_range, eff_lim, xlim_formation, _efficiency_label
                )
            )
        elif is_split_constant_voltage_plot:
            info_dicts.extend(
                self._build_cv_split_info_dicts(
                    config,
                    number_of_rows,
                    x_range,
                    y_range,
                    config.cv_share_range,
                    xlim_formation,
                    y_label,
                )
            )
        elif is_fullcell_standard_plot:
            info_dicts.extend(
                self._build_fullcell_standard_info_dicts(
                    config,
                    y,
                    x_range,
                    y_range,
                    eff_lim,
                    config.cv_share_range,
                    config.norm_range,
                    max_val_normalized_col,
                    xlim_formation,
                    c,
                )
            )
        else:
            info_dicts.extend(
                self._build_standard_info_dicts(
                    config,
                    number_of_rows,
                    x_range,
                    y_range,
                    xlim_formation,
                    y_label,
                    top_row_ylabel=_seaborn_top_row_label(y),
                )
            )

        return info_dicts

    def _build_efficiency_plot_info_dicts(
        self,
        config: Any,
        x_range: tuple,
        y_range: list,
        eff_lim: Optional[list],
        xlim_formation: tuple,
        efficiency_label: str,
    ) -> list:
        """Build info dicts for efficiency plots."""
        info_dicts = []
        if config.show_formation:
            info_dicts.extend(
                [
                    dict(
                        ylabel=efficiency_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=eff_lim,
                        row=0,
                        col="formation",
                        yticks=None,
                        xticks=False,
                    ),
                    dict(
                        ylabel="",
                        title="",
                        xlim=x_range,
                        ylim=eff_lim,
                        row=0,
                        col="standard",
                        yticks=False,
                        xticks=False,
                    ),
                    dict(
                        ylabel="",
                        title="",
                        xlim=xlim_formation,
                        ylim=y_range,
                        row=1,
                        col="formation",
                        yticks=None,
                        xticks=None,
                    ),
                    dict(
                        ylabel="",
                        title="",
                        xlim=x_range,
                        ylim=y_range,
                        row=1,
                        col="standard",
                        yticks=False,
                        xticks=None,
                    ),
                ]
            )
        else:
            info_dicts.extend(
                [
                    dict(
                        ylabel=efficiency_label,
                        title="",
                        xlim=x_range,
                        ylim=eff_lim,
                        row=0,
                        col=None,
                        yticks=None,
                        xticks=False,
                    ),
                    dict(
                        ylabel="",
                        title="",
                        xlim=x_range,
                        ylim=y_range,
                        row=1,
                        col=None,
                        yticks=None,
                        xticks=None,
                    ),
                ]
            )
        return info_dicts

    def _build_cv_split_info_dicts(
        self,
        config: Any,
        number_of_rows: int,
        x_range: tuple,
        y_range: list,
        cv_share_range: Optional[list],
        xlim_formation: tuple,
        y_label: str,
    ) -> list:
        """Build info dicts for CV split plots."""
        info_dicts = []

        # Row names for CV split plots when split=True
        row_names = ["all", "without CV", "with CV"]

        # If split=False, we only have one row
        if number_of_rows == 1:
            _d = dict(
                ylabel=y_label,
                title="",
                xlim=x_range,
                ylim=cv_share_range or y_range,
                row=None,
                col=None,
                yticks=None,
                xticks=None,
            )
            if config.show_formation:
                _d["col"] = "standard"
                _d["yticks"] = False
                _d["ylabel"] = ""
                info_dicts.append(
                    dict(
                        ylabel=y_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=cv_share_range or y_range,
                        row=None,
                        col="formation",
                        yticks=None,
                        xticks=None,
                    )
                )
            info_dicts.append(_d)
        else:
            # Handle 3-row case (all, without CV, with CV)
            for row_name in row_names[:number_of_rows]:
                if config.show_formation:
                    # Standard column (second column) - no y-axis labels
                    info_dicts.append(
                        dict(
                            ylabel="",
                            title="",
                            xlim=x_range,
                            ylim=cv_share_range or y_range,
                            row=row_name,
                            col="standard",
                            yticks=False,
                            xticks=True if row_name == row_names[-1] else False,
                        )
                    )
                    # Formation column (first column) - with y-axis labels
                    info_dicts.append(
                        dict(
                            ylabel=y_label,
                            title="",
                            xlim=xlim_formation,
                            ylim=cv_share_range or y_range,
                            row=row_name,
                            col="formation",
                            yticks=True,
                            xticks=True if row_name == row_names[-1] else False,
                        )
                    )
                else:
                    # No formation column, single column plot
                    info_dicts.append(
                        dict(
                            ylabel=y_label if row_name == row_names[0] else "",
                            title="",
                            xlim=x_range,
                            ylim=cv_share_range or y_range,
                            row=row_name,
                            col=None,
                            yticks=True if row_name == row_names[0] else None,
                            xticks=True if row_name == row_names[-1] else False,
                        )
                    )

        return info_dicts

    def _build_fullcell_standard_info_dicts(
        self,
        config: Any,
        y: str,
        x_range: tuple,
        y_range: list,
        eff_lim: Optional[list],
        cv_share_range: Optional[list],
        norm_range: Optional[list],
        max_val_normalized_col: float,
        xlim_formation: tuple,
        c: Any,
    ) -> list:
        """Build info dicts for fullcell standard plots."""
        info_dicts = []
        capacity_unit = _capacity_unit(c, mode=y.split("_")[-1])
        ce_label = "Coulombic\nEfficiency (%)"
        capacity_label = f"Capacity\n({capacity_unit})"

        loss_label = f"Capacity\nRetention\n({capacity_unit})"
        if (
            config.fullcell_standard_normalization_type
            and config.fullcell_standard_normalization_factor is not None
        ):
            _norm_label = f"[{config.fullcell_standard_normalization_scaler:.1f}/{config.fullcell_standard_normalization_factor:.1f} {capacity_unit}]"
            loss_label = f"Capacity\nRetention (norm.)\n{_norm_label}"
        else:
            loss_label = f"Capacity\nRetention\n({capacity_unit})"

        cv_label = f"CV Capacity\n({capacity_unit})"

        if config.fullcell_standard_normalization_type is not False:
            cum_loss_info_range = norm_range or [
                0.0,
                max(
                    max_val_normalized_col,
                    config.fullcell_standard_normalization_scaler,
                ),
            ]
        else:
            cum_loss_info_range = norm_range or y_range

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

        if not config.show_formation:
            cv_info["ylabel"] = cv_label
            cum_loss_info["ylabel"] = loss_label
            capacity_info["ylabel"] = capacity_label
            ce_info["ylabel"] = ce_label
            cv_info["yticks"] = True
            cum_loss_info["yticks"] = True
            capacity_info["yticks"] = True
            ce_info["yticks"] = True

        info_dicts.extend([cv_info, cum_loss_info, capacity_info, ce_info])

        if config.show_formation:
            info_dicts.extend(
                [
                    dict(
                        ylabel=cv_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=cv_share_range or y_range,
                        row=3,
                        col="formation",
                        yticks=True,
                        xticks=True,
                    ),
                    dict(
                        ylabel=loss_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=cum_loss_info_range,
                        row=2,
                        col="formation",
                        yticks=True,
                        xticks=False,
                    ),
                    dict(
                        ylabel=capacity_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=y_range,
                        row=1,
                        col="formation",
                        yticks=True,
                        xticks=False,
                    ),
                    dict(
                        ylabel=ce_label,
                        title="",
                        xlim=xlim_formation,
                        ylim=eff_lim,
                        row=0,
                        col="formation",
                        yticks=True,
                        xticks=False,
                    ),
                ]
            )

        return info_dicts

    def _build_standard_info_dicts(
        self,
        config: Any,
        number_of_rows: int,
        x_range: tuple,
        y_range: list,
        xlim_formation: tuple,
        y_label: str,
        top_row_ylabel: Optional[str] = None,
    ) -> list:
        """Build info dicts for standard plots.

        ``top_row_ylabel`` (when given) overrides the y-axis label on row
        0 only; remaining rows keep ``y_label``. Used by ``*_with_rate``
        y-sets so the rate row shows "C-rate (1/h)" instead of the
        capacity label.
        """
        info_dicts = []
        is_multi_row = number_of_rows > 1

        if is_multi_row:
            last_row = number_of_rows - 1
            for i in range(number_of_rows):
                row_label = (
                    top_row_ylabel if (i == 0 and top_row_ylabel) else y_label
                )
                row_ylim = None if (i == 0 and top_row_ylabel) else y_range
                xticks = None if i == last_row else False
                info_dicts.append(
                    dict(
                        ylabel="" if config.show_formation else row_label,
                        title="",
                        xlim=x_range,
                        ylim=row_ylim,
                        row=i,
                        col="standard" if config.show_formation else None,
                        yticks=False if config.show_formation else None,
                        xticks=xticks,
                    )
                )
                if config.show_formation:
                    info_dicts.append(
                        dict(
                            ylabel=row_label,
                            title="",
                            xlim=xlim_formation,
                            ylim=row_ylim,
                            row=i,
                            col="formation",
                            yticks=None,
                            xticks=xticks,
                        )
                    )
        else:
            _r = 1 if config.split else None
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
            if config.show_formation:
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

        return info_dicts

    def _valid_number_or_none(self, x: float) -> Optional[float]:
        """Clean up a number (convert NaN and Inf to None)"""
        import numbers

        if isinstance(x, numbers.Number):
            if not (np.isnan(x) or np.isinf(x)):
                return x
        return None

    def _to_numbers_or_nones(self, x: list) -> list:
        """Clean up a list of numbers (convert NaN and Inf to None)"""
        return [self._valid_number_or_none(i) for i in x]

    def _clean_up_axis(self, fig, info_dicts=None, row_id="row", col_id="cycle_type"):
        """Clean up and configure axes based on info_dicts."""
        if info_dicts is None:
            return

        # Create a dictionary with keys the same as the axis titles
        info_dict = {}
        for info in info_dicts:
            if col_id is not None:
                if row_id is not None:
                    info_text = f"{row_id} = {info['row']} | {col_id} = {info['col']}"
                else:
                    info_text = f"{col_id} = {info['col']}"
            else:
                if row_id is not None:
                    info_text = f"{row_id} = {info['row']}"
                else:
                    info_text = "single axis"
            info_dict[info_text] = info

        # Iterate over the axes and set the properties
        for a in fig.get_axes():
            title_text = a.get_title()
            if row_id is None and col_id is None:
                axis_info = info_dict.get("single axis", None)
            else:
                axis_info = info_dict.get(title_text, None)
            if axis_info is None:
                continue

            if xlim := axis_info.get("xlim", None):
                a.set_xlim(self._to_numbers_or_nones(xlim))
            if ylim := axis_info.get("ylim", None):
                a.set_ylim(self._to_numbers_or_nones(ylim))

            if ylabel := axis_info.get("ylabel", None):
                a.set_ylabel(ylabel)
            a.set_title(axis_info.get("title", ""))
            xticks = axis_info.get("xticks", False)
            yticks = axis_info.get("yticks", False)

            if xticks is False:
                a.set_xticks([])
            if yticks is False:
                a.set_yticks([])

    def _convert_legend_labels(self, sns_fig):
        """Convert legend labels to nicer format."""
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


