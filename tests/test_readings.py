"""cellpy.utils.readings: check-up readings with explicit units."""

from pathlib import Path

import pandas as pd
import pytest

import cellpy
from cellpy.utils.readings import Reading, checkup_readings

from . import fdv

PEC_DIR = Path(fdv.raw_data_dir) / "pec_multiple_tests"


@pytest.fixture(scope="module")
def cycled():
    """A cycled coin cell from a cellpy file (no mdbtools needed)."""
    return cellpy.get(Path(fdv.raw_data_dir) / "20231115_rate_cc.h5")


def _by_name(readings):
    return {r.name: r for r in readings}


@pytest.mark.parametrize(
    "name, volts",
    [("Test25195.csv", 3.568858), ("Test25205.csv", 0.063965), ("Test25209.csv", 3.753438)],
)
def test_pec_ocv_test_gives_only_the_rest_voltage(name, volts):
    c = cellpy.get(PEC_DIR / name, instrument="pec_csv")

    readings = checkup_readings(c)

    assert [r.name for r in readings] == ["ocv"]
    assert readings[0].unit == "V"
    assert readings[0].value == pytest.approx(volts, abs=1e-5)


def test_capacity_is_in_ah_from_the_last_complete_cycle(cycled):
    summary = cycled.data.summary
    readings = _by_name(checkup_readings(cycled))

    capacity = readings["capacity"]
    row = summary[summary["cycle_num"] == capacity.cycle].iloc[-1]
    # The base summary column is in the tester's unit, here Ah; the reading is in Ah
    # whatever the session's cellpy units are (mAh by default).
    assert cycled.data.raw_units.charge == "Ah"
    assert capacity.unit == "Ah"
    assert capacity.value == pytest.approx(row["discharge_capacity"])
    assert capacity.value * 1000 == pytest.approx(
        row["discharge_capacity"] * cycled.unit_scaler_from_raw("mAh", "charge")
    )
    assert readings["charge_capacity"].cycle == capacity.cycle
    steps = cycled.data.steps
    in_cycle = set(steps.loc[steps["cycle_num"] == capacity.cycle, "step_type"])
    assert {"charge", "discharge"} <= in_cycle


def test_resistance_is_in_milliohm(cycled):
    readings = _by_name(checkup_readings(cycled))
    summary = cycled.data.summary
    row = summary[summary["cycle_num"] == readings["dc_resistance"].cycle].iloc[-1]
    ohm_per_raw = cycled.unit_scaler_from_raw("ohm", "resistance")

    assert readings["dc_resistance"].unit == "mOhm"
    assert readings["dc_resistance"].value == pytest.approx(row["ir_discharge"] * ohm_per_raw * 1000)


def test_a_chosen_cycle_is_used(cycled):
    readings = _by_name(checkup_readings(cycled, cycle=3))
    assert readings["capacity"].cycle == 3


def test_without_a_step_table_the_current_decides_the_ocv():
    c = cellpy.get(PEC_DIR / "Test25209.csv", instrument="pec_csv")
    c.data.steps = pd.DataFrame()

    assert [r.name for r in checkup_readings(c)] == ["ocv"]
    c.data.raw.loc[c.data.raw.index[-1], "current"] = 0.5  # A, not at rest
    assert checkup_readings(c) == []


def test_reading_as_dict():
    reading = Reading("ocv", 3.6, "V", 1, "note")
    assert reading.as_dict() == {"name": "ocv", "value": 3.6, "unit": "V", "cycle": 1, "note": "note"}
