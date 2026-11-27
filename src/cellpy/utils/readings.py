"""Check-up readings: one named value per quantity for a loaded cell.

A check-up test (a slow capacity cycle, a resistance pulse, an OCV rest) is
usually reduced to a handful of numbers: the discharge capacity, the DC
resistance, the open-circuit voltage at the end. Databases store those
numbers per test and plot them over a cell's life. This module picks them out
of a loaded `CellpyCell` with explicit units, so every consumer does not have
to rediscover which summary column is in which unit::

    import cellpy
    from cellpy.utils.readings import checkup_readings

    c = cellpy.get("Test25205.csv", instrument="pec_csv")
    for r in checkup_readings(c):
        print(r.name, r.value, r.unit)

Rules (each reading is left out when its rule does not apply):

- ``capacity`` / ``charge_capacity``: the discharge / charge capacity of the
  chosen cycle, in Ah. A cycle counts only if its step table has a
  ``discharge`` / ``charge`` step, so the noise of a rest-only test is not
  reported as a capacity.
- ``dc_resistance``: the IR value recorded on discharge (``ir_discharge``) in
  the chosen cycle, in mOhm. Zero or missing means "not measured".
- ``ocv``: the voltage at the last point of the test, in V, if the test
  ends at rest: its last step is a rest or relaxation step in the step table
  (``rest``, ``ocvrlx_up``, ``ocvrlx_down``). Without a step table, the
  current at the last point must be below ``rest_current`` (A).

The chosen cycle is ``cycle`` if given, else the last complete cycle (one
with both a discharge and a charge step), else the last cycle with a
discharge step. A test that stops in the middle of a cycle then reports the
cycle before it. Values are read from the base summary columns, which are in
the tester's units (``c.data.raw_units``), and converted with
`CellpyCell.unit_scaler_from_raw` (see docs/reference/summary_columns.md).

Names and units follow the reading vocabulary that BatBase uses for
``ExperimentObservation`` (``capacity`` Ah, ``dc_resistance`` mOhm, ``ocv``
V), but nothing here depends on BatBase.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["Reading", "checkup_readings"]

# Units of the returned readings, per quantity.
CAPACITY_UNIT = "Ah"
RESISTANCE_UNIT = "mOhm"
VOLTAGE_UNIT = "V"
# pint spells milliohm out; the label above is what consumers see.
_PINT_RESISTANCE_UNIT = "milliohm"


@dataclass(frozen=True)
class Reading:
    """One named value with its unit.

    Attributes:
        name: what was measured, lower_snake_case (``capacity``).
        value: the number, in ``unit``.
        unit: the unit of ``value`` (``Ah``, ``mOhm``, ``V``).
        cycle: the cycle the value comes from; ``None`` for test-level values.
        note: how the value was picked, for provenance.
    """

    name: str
    value: float
    unit: str
    cycle: int | None = None
    note: str = ""

    def as_dict(self) -> dict:
        """Plain dict, e.g. for JSON."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "cycle": self.cycle,
            "note": self.note,
        }


def _finite(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _cycles_with_step(steps, step_type: str) -> list[int]:
    if steps is None or getattr(steps, "empty", True) or "step_type" not in steps:
        return []
    rows = steps[steps["step_type"] == step_type]
    return sorted(int(cycle) for cycle in rows["cycle_num"].unique())


REST_STEP_TYPES = frozenset({"rest", "ocvrlx_up", "ocvrlx_down"})


def _ends_at_rest(steps) -> bool | None:
    """True/False from the step table; None when there is no step table."""
    if steps is None or getattr(steps, "empty", True) or "step_type" not in steps:
        return None
    order = "datapoint_num_last" if "datapoint_num_last" in steps else None
    last = steps.sort_values(order).iloc[-1] if order else steps.iloc[-1]
    return str(last["step_type"]) in REST_STEP_TYPES


def _summary_row(summary, cycle: int):
    rows = summary[summary["cycle_num"] == cycle]
    return None if rows.empty else rows.iloc[-1]


def checkup_readings(
    c,
    *,
    cycle: int | None = None,
    rest_current: float = 1e-3,
) -> list[Reading]:
    """Pick check-up readings out of a loaded cell.

    Args:
        c: a loaded `CellpyCell` with raw data, steps and summary.
        cycle: the cycle to read capacity and resistance from. Default: the
            last cycle with a discharge step.
        rest_current: largest absolute current (A) at the last point for the
            final voltage to count as an OCV. Used only without a step table.

    Returns:
        The readings that apply, in the order capacity, charge_capacity,
        dc_resistance, ocv. An empty list when nothing applies.
    """
    data = c.data
    summary = getattr(data, "summary", None)
    steps = getattr(data, "steps", None)
    readings: list[Reading] = []

    discharge_cycles = _cycles_with_step(steps, "discharge")
    charge_cycles = _cycles_with_step(steps, "charge")
    complete = sorted(set(discharge_cycles) & set(charge_cycles))
    if cycle is not None:
        chosen = cycle
    elif complete:
        chosen = complete[-1]
    else:
        chosen = discharge_cycles[-1] if discharge_cycles else None

    row = None
    if chosen is not None and summary is not None and not summary.empty:
        row = _summary_row(summary, chosen)

    if row is not None:
        to_ah = c.unit_scaler_from_raw(CAPACITY_UNIT, "charge")
        if chosen in discharge_cycles:
            value = _finite(row.get("discharge_capacity"))
            if value is not None and value > 0:
                readings.append(
                    Reading("capacity", value * to_ah, CAPACITY_UNIT, chosen, "discharge_capacity of the cycle")
                )
        if chosen in charge_cycles:
            value = _finite(row.get("charge_capacity"))
            if value is not None and value > 0:
                readings.append(
                    Reading("charge_capacity", value * to_ah, CAPACITY_UNIT, chosen, "charge_capacity of the cycle")
                )
        value = _finite(row.get("ir_discharge"))
        if value is not None and value > 0:
            to_mohm = c.unit_scaler_from_raw(_PINT_RESISTANCE_UNIT, "resistance")
            readings.append(
                Reading("dc_resistance", value * to_mohm, RESISTANCE_UNIT, chosen, "ir_discharge of the cycle")
            )

    raw = getattr(data, "raw", None)
    if raw is not None and not raw.empty and {"potential", "current"} <= set(raw.columns):
        last = raw.iloc[-1]
        to_amp = c.unit_scaler_from_raw("A", "current")
        current = _finite(last["current"])
        voltage = _finite(last["potential"])
        at_rest = _ends_at_rest(steps)
        if at_rest is None:
            at_rest = current is not None and abs(current * to_amp) <= rest_current
        if voltage is not None and at_rest:
            to_volt = c.unit_scaler_from_raw(VOLTAGE_UNIT, "voltage")
            last_cycle = _finite(last.get("cycle_num"))
            readings.append(
                Reading(
                    "ocv",
                    voltage * to_volt,
                    VOLTAGE_UNIT,
                    int(last_cycle) if last_cycle is not None else None,
                    "voltage at the last point, at rest",
                )
            )
    return readings
