"""Write a ``.cfz`` bundle from the prepare path.

The translator lives here, next to prepare, so cellpy-figure never imports
cellpy. ``save_bundle`` calls the same prepare functions as ``cycles_plot``,
``summary_plot``, ``ica_plot``, and ``dva_plot``, then stores one panel (or a
facet row) with ``cellpy_figure.Figure.write``.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import pandas as pd

from cellpy.plotting.cycle_legend import pop_cycle_legend_options, resolve_cycle_legend_mode
from cellpy.plotting.spec import FigureSpec

_KINDS = ("cycles", "summary", "ica", "dva")
_TAG = re.compile(r"<[^>]+>")


def save_bundle(cell: Any, *, kind: str, path: str, **kwargs: Any) -> str:
    """Write a portable ``.cfz`` bundle for one plot kind.

    Args:
        cell: cellpy cell, the same object the matching ``*_plot`` function takes.
        kind: ``cycles``, ``summary``, ``ica``, or ``dva``.
        path: Destination path. An existing file is replaced.
        **kwargs: Arguments of the matching plot function. ``backend`` and
            ``return_data`` are ignored because this function does not draw.

    Returns:
        The path that was written.

    Raises:
        ValueError: ``kind`` is not one of the four, or the prepared table is empty.
        ImportError: ``cellpy-figure`` is not installed. Install ``cellpy[batch]``
            or ``cellpy[plotting-mpl]``.
    """
    kind = _require_kind(kind)
    frame, spec, family, note = _prepare(cell, kind, kwargs)
    figure = _to_figure(frame, spec, family=family, note=note)
    figure.write(str(path))
    return str(path)


def _require_kind(kind: str) -> str:
    text = str(kind).strip().lower()
    if text not in _KINDS:
        known = ", ".join(_KINDS)
        raise ValueError(f"kind {kind!r} is not one of {known}.")
    return text


def _prepare(cell: Any, kind: str, kwargs: dict[str, Any]) -> tuple[pd.DataFrame, FigureSpec, str, Optional[str]]:
    kwargs = dict(kwargs)
    kwargs.pop("backend", None)
    kwargs.pop("return_data", None)
    kwargs.pop("return_figure", None)
    if kind == "cycles":
        return _prepare_cycles(cell, kwargs)
    if kind == "summary":
        return _prepare_summary(cell, kwargs)
    return _prepare_ica(cell, kind, kwargs)


def _prepare_cycles(cell: Any, kwargs: dict[str, Any]) -> tuple[pd.DataFrame, FigureSpec, str, Optional[str]]:
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.curves import CyclesPrepareConfig, prepare as prepare_curves
    from cellpy.plotting.registry import get as get_family

    interpolated = kwargs.get("interpolated", True)
    number_of_points = kwargs.get("number_of_points", 200)
    config = CyclesPrepareConfig(
        cycles=kwargs.pop("cycles", None),
        inter_cycle_shift=kwargs.pop("inter_cycle_shift", True),
        cycle_mode=kwargs.pop("cycle_mode", None),
        formation_cycles=kwargs.pop("formation_cycles", 3),
        show_formation=kwargs.pop("show_formation", True),
        mode=kwargs.pop("mode", "gravimetric"),
        method=kwargs.pop("method", "forth-and-forth"),
        interpolated=kwargs.pop("interpolated", True),
        number_of_points=kwargs.pop("number_of_points", 200),
        colormap=kwargs.pop("colormap", "Blues_r"),
        formation_colormap=kwargs.pop("formation_colormap", "autumn"),
        cut_colorbar=kwargs.pop("cut_colorbar", True),
        title=kwargs.pop("title", None),
        figsize=kwargs.pop("figsize", (6, 4)),
        x_range=kwargs.pop("x_range", None),
        y_range=kwargs.pop("y_range", None),
        width=kwargs.pop("width", 800),
        height=kwargs.pop("height", 600),
        marker_size=kwargs.pop("marker_size", 5),
        formation_line_color=kwargs.pop("formation_line_color", "rgba(152, 0, 0, .8)"),
        force_colorbar=kwargs.pop("force_colorbar", False),
        force_nonbar=kwargs.pop("force_nonbar", False),
        plotly_template=kwargs.pop("plotly_template", None),
        seaborn_palette=kwargs.pop("seaborn_palette", "deep"),
        seaborn_style=kwargs.pop("seaborn_style", "dark"),
        seaborn_context=kwargs.pop("seaborn_context", "notebook"),
        seaborn_facecolor=kwargs.pop("seaborn_facecolor", "#EAEAF2"),
        seaborn_edgecolor=kwargs.pop("seaborn_edgecolor", "black"),
        seaborn_style_dict=kwargs.pop("seaborn_style_dict", None),
        backend="matplotlib",
        additional_kwargs=kwargs,
    )
    family = get_family("cycles")
    frame, spec = prepare_curves(from_source(cell), family, config)
    note = f"interpolated ({number_of_points} points)" if interpolated else None
    return frame, spec, getattr(family, "name", "cycles"), note


def _prepare_summary(cell: Any, kwargs: dict[str, Any]) -> tuple[pd.DataFrame, FigureSpec, str, Optional[str]]:
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.summary import prepare as prepare_summary
    from cellpy.plotting.registry import get as get_family
    from cellpy.utils.plotutils import (
        SummaryPlotConfig,
        SummaryPlotInfo,
        _resolve_summary_column,
        _resolve_summary_columns,
    )

    config = SummaryPlotConfig.from_kwargs(**kwargs)
    config.x = _resolve_summary_column(cell, config.x)
    config.hover_columns = _resolve_summary_columns(cell, config.hover_columns)
    config.backend = "matplotlib"
    config.return_data = False
    family = get_family(config.y)
    frame, spec = prepare_summary(from_source(cell), family, config, plot_info=SummaryPlotInfo(cell))
    note = "filtered" if config.filters else None
    return frame, spec, getattr(family, "name", config.y), note


def _prepare_ica(cell: Any, kind: str, kwargs: dict[str, Any]) -> tuple[pd.DataFrame, FigureSpec, str, Optional[str]]:
    from cellpy.plotting.context import from_source
    from cellpy.plotting.prepare.ica import IcaPrepareConfig, prepare as prepare_ica
    from cellpy.plotting.registry import get as get_family

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
    option_overrides = {key: kwargs.pop(key) for key in list(kwargs) if key in option_keys}
    number_of_points = kwargs.pop("number_of_points", None)
    family_name = "dva" if kind == "dva" else "ica"
    config = IcaPrepareConfig(
        derivative="dvdq" if kind == "dva" else "dqdv",
        cycles=kwargs.pop("cycles", None),
        direction=kwargs.pop("direction", "both"),
        options=kwargs.pop("options", None),
        strict=kwargs.pop("strict", False),
        cycle_mode=kwargs.pop("cycle_mode", None),
        number_of_points=number_of_points,
        title=kwargs.pop("title", None),
        colormap=kwargs.pop("colormap", "viridis"),
        width=kwargs.pop("width", 800),
        height=kwargs.pop("height", 600),
        figsize=kwargs.pop("figsize", (6, 4)),
        x_range=kwargs.pop("x_range", None),
        y_range=kwargs.pop("y_range", None),
        plotly_template=kwargs.pop("plotly_template", None),
        backend="matplotlib",
        option_overrides=option_overrides,
        additional_kwargs=kwargs,
    )
    family = get_family(family_name)
    frame, spec = prepare_ica(from_source(cell), family, config)
    note = f"thinned to {number_of_points} points" if number_of_points else None
    return frame, spec, getattr(family, "name", family_name), note


def _to_figure(frame: pd.DataFrame, spec: FigureSpec, *, family: str, note: Optional[str]) -> Any:
    try:
        from cellpy_figure import Encoding, Figure, Panel, Provenance
    except ImportError as exc:
        raise ImportError(
            "Writing a .cfz bundle needs cellpy-figure. "
            'Install it with pip install "cellpy[plotting-mpl]" or pip install "cellpy[batch]".'
        ) from exc

    import cellpy

    kind = spec.extras.get("kind")
    if kind in {"cycles", "ica", "dva"}:
        panel, plotted = _curve_panel(frame, spec, Encoding, Panel)
    else:
        panel, plotted = _summary_panel(frame, spec, Encoding, Panel)

    extensions: dict[str, Any] = {}
    if family:
        extensions["cellpy"] = {"family": family}

    return Figure(
        data=plotted,
        panels=[panel],
        title=_plain_title(spec.title),
        provenance=Provenance(
            producer="cellpy",
            producer_version=cellpy.__version__,
            note=note,
        ),
        extensions=extensions,
    )


def _curve_panel(frame: pd.DataFrame, spec: FigureSpec, encoding: Any, panel_cls: Any) -> tuple[Any, pd.DataFrame]:
    from cellpycore.config import CurveCols

    extras = spec.extras
    if extras.get("kind") == "cycles":
        ccols = CurveCols()
        x_field = "capacity"
        y_field = ccols.potential
        color_field = ccols.cycle_num
        x_label, x_unit = _split_label(extras.get("capacity_label") or spec.x_axis.label or "Capacity")
        y_label, y_unit = _split_label(extras.get("voltage_label") or "Voltage")
    else:
        x_field = extras["x"]
        y_field = extras["y"]
        color_field = extras.get("color")
        x_label, x_unit = _split_label(extras.get("x_label") or spec.x_axis.label or x_field)
        y_label, y_unit = _split_label(extras.get("y_label") or y_field)

    plotted = _spell_direction(_rows(frame, [x_field, y_field, color_field, "direction"]), spec)
    stroke = _stroke(plotted, encoding)
    color = _cycle_color(plotted, spec, color_field, encoding)
    panel = panel_cls(
        x=encoding(field=x_field, label=x_label, unit=x_unit),
        y=encoding(field=y_field, label=y_label, unit=y_unit),
        color=color,
        stroke=stroke,
    )
    return panel, plotted


def _summary_panel(frame: pd.DataFrame, spec: FigureSpec, encoding: Any, panel_cls: Any) -> tuple[Any, pd.DataFrame]:
    extras = spec.extras
    x_field = extras.get("x") or "cycle_index"
    y_field = extras.get("y_header") or "value"
    facet_field = extras.get("color") or "variable"
    keep = [x_field, y_field, facet_field]
    plotted = _rows(frame, keep)
    x_label, x_unit = _split_label(spec.x_axis.label or x_field)
    y_text = extras.get("y_label") or y_field
    y_label, y_unit = _split_label(y_text if isinstance(y_text, str) else y_field)
    facet = None
    if facet_field in plotted.columns and plotted[facet_field].nunique(dropna=True) > 1:
        facet = encoding(field=facet_field, label=facet_field)
    panel = panel_cls(
        x=encoding(field=x_field, label=x_label, unit=x_unit),
        y=encoding(field=y_field, label=y_label, unit=y_unit),
        facet=facet,
    )
    return panel, plotted


def _rows(frame: pd.DataFrame, fields: list[Optional[str]]) -> pd.DataFrame:
    needed = [field for field in fields if field and field in frame.columns]
    if not needed:
        raise ValueError("prepared frame has none of the columns this bundle draws.")
    plotted = frame.loc[:, needed].copy()
    subset = [field for field in needed if field != "direction"]
    plotted = plotted.dropna(subset=subset)
    if plotted.empty:
        raise ValueError("prepared frame has no rows to store in the bundle.")
    plotted.attrs = {}
    return plotted.reset_index(drop=True)


def _spell_direction(frame: pd.DataFrame, spec: FigureSpec) -> pd.DataFrame:
    """Store direction as charge/discharge.

    Capacity curves keep the raw ``get_cap`` codes (-1 / 1). ICA and DVA
    frames already spell the words. The bundle uses the words so the stroke
    scale is readable without cellpy.
    """
    if "direction" not in frame.columns:
        return frame
    sample = frame["direction"].dropna()
    if sample.empty:
        return frame
    words = {"charge", "discharge", "both"}
    if set(sample.astype(str)) <= words:
        frame["direction"] = sample.astype(str).reindex(frame.index)
        return frame
    from cellpy.ica import _direction_labels

    cell = spec.extras.get("cell")
    labels = _direction_labels(getattr(cell, "cycle_mode", None))

    def one(value: Any) -> Any:
        try:
            return labels[int(value)]
        except (TypeError, ValueError, KeyError):
            return value

    frame["direction"] = frame["direction"].map(one)
    return frame


def _stroke(frame: pd.DataFrame, encoding: Any) -> Any:
    if "direction" not in frame.columns:
        return None
    present = {str(value) for value in frame["direction"].dropna().unique()}
    if not {"charge", "discharge"} <= present:
        return None
    scale = {"charge": "solid", "discharge": "dashed"}
    for extra in sorted(present - set(scale)):
        scale[extra] = "dotted"
    return encoding(field="direction", label="direction", scale=scale)


def _cycle_color(frame: pd.DataFrame, spec: FigureSpec, field: Optional[str], encoding: Any) -> Any:
    if not field or field not in frame.columns:
        return None
    options = pop_cycle_legend_options(spec.extras, dict(spec.extras.get("additional_kwargs") or {}))
    n_cycles = int(frame[field].nunique(dropna=True))
    mode = resolve_cycle_legend_mode(n_cycles, **options)
    color_type = "quantitative" if mode == "colorbar" else "nominal"
    return encoding(field=field, label="cycle", type=color_type, legend_title="cycle")


def _split_label(text: Optional[str]) -> tuple[str, Optional[str]]:
    if not text:
        return "", None
    plain = _plain_title(text) or ""
    if plain.endswith(")") and " (" in plain:
        name, unit = plain.rsplit(" (", 1)
        return name, unit[:-1] or None
    return plain, None


def _plain_title(title: Optional[str]) -> Optional[str]:
    if title is None:
        return None
    text = _TAG.sub("", str(title))
    text = text.replace("\n", " ").strip()
    return text or None
