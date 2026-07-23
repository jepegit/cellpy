"""Cycle-info prepare path: scaled raw+steps frame + FigureSpec (#647).

Public ``cycle_info_plot`` calls :func:`prepare` then hands ``(frame, FigureSpec)``
to a backend renderer (``spec.extras['kind'] == 'cycle_info'``).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

from cellpy.plotting.headers import LiveHeaders
from cellpy.plotting.labels import quantity_label
from cellpy.plotting.spec import AxisSpec, FigureSpec, PanelSpec


@dataclass
class CycleInfoPrepareConfig:
    """Input knobs for :func:`prepare` (mirrors public ``cycle_info_plot`` args)."""

    cycle: Optional[Any] = None
    get_axes: bool = False
    t_unit: str = "hours"
    v_unit: str = "V"
    i_unit: str = "mA"
    backend: str = "plotly"
    additional_kwargs: dict = field(default_factory=dict)


def prepare(
    ctx: Any,
    family: Any,
    config: CycleInfoPrepareConfig,
) -> tuple[pd.DataFrame, FigureSpec]:
    """Prepare scaled raw/steps data and :class:`FigureSpec` for ``cycle_info_plot``.

    Args:
        ctx: :class:`~cellpy.plotting.context.CellContext` (or compatible).
        family: registered family (``cycle_info``).
        config: :class:`CycleInfoPrepareConfig` built by the public entry point.

    Returns:
        ``(frame, spec)`` where ``spec.extras['kind'] == 'cycle_info'``.

        For plotly, *frame* is the merged scaled raw+steps table used for traces.
        For matplotlib, *frame* is the scaled raw subset; the step table lives in
        ``spec.extras['steps']``.
    """
    c = ctx.cell
    raw_hdr = LiveHeaders(c, "raw")
    step_hdr = LiveHeaders(c, "steps")

    t_scaler = c.unit_scaler_from_raw(config.t_unit, "time")
    v_scaler = c.unit_scaler_from_raw(config.v_unit, "voltage")
    i_scaler = c.unit_scaler_from_raw(config.i_unit, "current")

    cycle = config.cycle
    backend = config.backend

    # Matplotlib keeps the historical single-cycle asymmetry (epic #567).
    if backend == "matplotlib":
        if cycle is None:
            warnings.warn("Only one cycle at a time is supported for matplotlib")
            cycle = 1
        if isinstance(cycle, (list, tuple)):
            warnings.warn("Only one cycle at a time is supported for matplotlib")
            cycle = cycle[0]

    data = c.data.raw.copy()
    table = c.data.steps.copy()

    time_hdr = raw_hdr.test_time_txt
    cycle_hdr = raw_hdr.cycle_index_txt
    step_number_hdr = raw_hdr.step_index_txt
    current_hdr = raw_hdr.current_txt
    voltage_hdr = raw_hdr.voltage_txt

    if backend == "plotly":
        if cycle is None:
            cycle = list(data[cycle_hdr].unique())
        if not isinstance(cycle, (list, tuple)):
            cycle = [cycle]

        v_delta = step_hdr.stat("voltage", "delta")
        i_delta = step_hdr.stat("current", "delta")
        c_delta = step_hdr.stat("charge", "delta")
        dc_delta = step_hdr.stat("discharge", "delta")
        cycle_ = step_hdr.cycle
        step_ = step_hdr.step
        type_ = step_hdr.type

        data = data[
            [time_hdr, cycle_hdr, step_number_hdr, current_hdr, voltage_hdr]
        ]
        table = table[
            [cycle_, step_, type_, v_delta, i_delta, c_delta, dc_delta]
        ]
        data = data.loc[data[cycle_hdr].isin(cycle), :]
        data[time_hdr] = data[time_hdr] * t_scaler
        data[voltage_hdr] = data[voltage_hdr] * v_scaler
        data[current_hdr] = data[current_hdr] * i_scaler
        frame = data.merge(
            table,
            left_on=(cycle_hdr, step_number_hdr),
            right_on=(cycle_, step_),
        ).sort_values(by=[time_hdr])

        title = _plotly_title(c, cycle, config.additional_kwargs)
        family_name = getattr(family, "name", "cycle_info")
        spec = FigureSpec(
            panels=(
                PanelSpec(
                    columns=(voltage_hdr,),
                    kind="line",
                    y_axis=AxisSpec(label=quantity_label("Voltage", config.v_unit)),
                ),
            ),
            x_axis=AxisSpec(label=quantity_label("Time", config.t_unit)),
            title=title,
            supports_formation=False,
            extras={
                "kind": "cycle_info",
                "family": family_name,
                "cycle": list(cycle),
                "get_axes": config.get_axes,
                "t_unit": config.t_unit,
                "v_unit": config.v_unit,
                "i_unit": config.i_unit,
                "time_hdr": time_hdr,
                "cycle_hdr": cycle_hdr,
                "step_number_hdr": step_number_hdr,
                "current_hdr": current_hdr,
                "voltage_hdr": voltage_hdr,
                "type_hdr": type_,
                "v_delta": v_delta,
                "i_delta": i_delta,
                "c_delta": c_delta,
                "dc_delta": dc_delta,
                "backend": backend,
                "cell": c,
                "additional_kwargs": dict(config.additional_kwargs),
            },
        )
        return frame, spec

    # matplotlib path: scaled columns stay on the raw subset; steps for annotations.
    m_cycle_data = data[cycle_hdr] == cycle
    frame = data.loc[m_cycle_data].copy()
    frame[time_hdr] = frame[time_hdr] * t_scaler
    frame[voltage_hdr] = frame[voltage_hdr] * v_scaler
    frame[current_hdr] = frame[current_hdr] * i_scaler

    family_name = getattr(family, "name", "cycle_info")
    spec = FigureSpec(
        panels=(
            PanelSpec(
                columns=(voltage_hdr, current_hdr),
                kind="line",
                y_axis=AxisSpec(label=quantity_label("voltage", config.v_unit)),
            ),
        ),
        x_axis=AxisSpec(label=quantity_label("time", config.t_unit)),
        title=f"Cycle: {cycle}",
        supports_formation=False,
        extras={
            "kind": "cycle_info",
            "family": family_name,
            "cycle": cycle,
            "get_axes": config.get_axes,
            "t_unit": config.t_unit,
            "v_unit": config.v_unit,
            "i_unit": config.i_unit,
            "t_scaler": t_scaler,
            "v_scaler": v_scaler,
            "i_scaler": i_scaler,
            "time_hdr": time_hdr,
            "cycle_hdr": cycle_hdr,
            "step_number_hdr": step_number_hdr,
            "current_hdr": current_hdr,
            "voltage_hdr": voltage_hdr,
            "steps": table,
            "step_hdr": step_hdr,
            "backend": backend,
            "cell": c,
            "additional_kwargs": dict(config.additional_kwargs),
        },
    )
    return frame, spec


def _plotly_title(c: Any, cycle: list, kwargs: dict) -> str:
    cell_name = kwargs.get("title", c.cell_name)
    title_start = f"<b>{cell_name}</b> Cycle"
    if len(cycle) > 2:
        if cycle[-1] - cycle[0] == len(cycle) - 1:
            return f"{title_start}s {cycle[0]} - {cycle[-1]}"
        return f"{title_start}s {cycle}"
    if len(cycle) == 2:
        return f"{title_start}s {cycle[0]} and {cycle[1]}"
    return f"{title_start} {cycle[0]}"
