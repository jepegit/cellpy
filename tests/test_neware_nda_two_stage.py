"""neware_nda's two-stage declarations (#560).

The real fastnda-based Neware loader (the parked zombie is ``ext_nda_reader``).
It needs the ``fastnda`` backend and an ``.nda*`` file, neither of which is an
in-repo fixture, so — like the fixture-less Arbin variants — it is checked at
the declaration level: vendor→native mapping, ``Test_ID`` dropped as provenance,
and ``datetime_kind="epoch_seconds"`` for its ``unix_time_s`` column.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cellpy.exceptions import LoaderError
from cellpy.parameters.internal_settings import merge_raw_units
from cellpy.readers.instruments import neware_nda

_LOCAL_NDAX = (
    Path(__file__).resolve().parents[1] / "local" / "data" / "20261013_nor110_04_fcnmp_cyc_20261013151333.ndax"
)


def _declarations():
    """declarations() needs only the static renaming dict, not parsed data (which
    would require fastnda), so we set the parsed flag directly."""
    loader = neware_nda.DataLoader()
    loader._parsed = True
    return loader.declarations()


@pytest.mark.essential
def test_declarations_map_fastnda_columns_to_native():
    column_map = _declarations().column_map
    assert column_map["voltage_V"] == "potential"
    assert column_map["current_mA"] == "current"
    assert column_map["charge_capacity_mAh"] == "cumulative_charge_capacity"
    assert column_map["discharge_capacity_mAh"] == "cumulative_discharge_capacity"
    assert column_map["internal_resistance_mOhm"] == "internal_resistance"


@pytest.mark.essential
def test_test_id_is_dropped_as_provenance():
    assert "Test_ID" not in _declarations().column_map


@pytest.mark.essential
def test_unix_time_is_declared_epoch_seconds():
    declarations = _declarations()
    assert declarations.datetime_kind == "epoch_seconds"
    # unix_time_s is kept as the date_time passthrough for harmonize to parse.
    assert declarations.passthrough.get("unix_time_s") == "date_time"


@pytest.mark.essential
def test_declarations_before_parse_raises():
    loader = neware_nda.DataLoader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()


@pytest.mark.essential
def test_raw_units_follow_fastnda_column_suffixes():
    units = merge_raw_units(neware_nda.DataLoader.get_raw_units())
    assert units.current == "mA"
    assert units.charge == "mAh"
    assert units.energy == "mWh"
    assert units.resistance == "mohm"
    assert units.voltage == "V"
    assert units.mass == "g"
    assert units.nominal_capacity == "mAh/g"
    assert _declarations().raw_units.current == "mA"
    assert _declarations().raw_units.charge == "mAh"


@pytest.mark.essential
def test_charge_and_discharge_unit_suffixes_must_agree(monkeypatch):
    renaming = dict(neware_nda.normal_headers_renaming_dict)
    renaming["discharge_capacity_txt"] = "discharge_capacity_mWh"
    monkeypatch.setattr(neware_nda, "normal_headers_renaming_dict", renaming)
    with pytest.raises(ValueError, match="charge columns disagree"):
        neware_nda.DataLoader.get_raw_units()


@pytest.mark.skipif(not _LOCAL_NDAX.is_file(), reason="gitignored local ndax is absent")
def test_local_ndax_current_and_capacity_stay_in_milli_units():
    from cellpy import get

    cell = get(str(_LOCAL_NDAX), instrument="neware_nda", mass=1.0)
    raw = cell.data.raw
    assert cell.data.raw_units.current == "mA"
    assert cell.data.raw_units.charge == "mAh"
    assert abs(raw["current"]).max() == pytest.approx(65.7, abs=0.05)
    assert raw["cumulative_discharge_capacity"].max() == pytest.approx(933.6, rel=0.01)
