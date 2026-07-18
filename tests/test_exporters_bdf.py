"""Tests for cellpy.exporters.bdf.to_bdf."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pytest

from cellpy import log
from cellpy.exporters import to_bdf
from cellpy.exporters import bdf as bdf_module
from cellpy.parameters.internal_settings import CellpyUnits, get_headers_normal

log.setup_logging(default_level=logging.DEBUG, testing=True)


def _make_synthetic_cell(*, with_capacity: bool = True, with_datetime: bool = True):
    """Build a minimal CellpyCell with a fabricated ``data.raw`` frame.

    Avoids the heavy ``cell`` fixture so these tests stay fast and
    independent of the on-disk test data.
    """
    from cellpy import cellreader

    # Name the fabricated raw via the cell's own headers so the frame matches
    # the runtime schema (native after the flip; the shim resolves the legacy
    # *_txt attrs to the native column names).
    cell = cellreader.CellpyCell(initialize=True)
    headers = cell.headers_normal
    n = 6
    raw = pd.DataFrame(
        {
            headers.test_time_txt: [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            headers.voltage_txt: [3.0, 3.1, 3.2, 3.3, 3.4, 3.5],
            headers.current_txt: [0.1, 0.1, -0.1, -0.1, 0.0, 0.0],
            headers.cycle_index_txt: [1, 1, 2, 2, 3, 3],
            headers.step_index_txt: [1, 2, 1, 2, 1, 2],
        }
    )
    if with_capacity:
        raw[headers.charge_capacity_txt] = [0.0, 100.0, 100.0, 0.0, 0.0, 100.0]
        raw[headers.discharge_capacity_txt] = [0.0, 0.0, 0.0, 100.0, 0.0, 0.0]
    if with_datetime:
        raw[headers.datetime_txt] = pd.to_datetime(
            [
                "2024-01-01 00:00:00",
                "2024-01-01 00:00:01",
                "2024-01-01 00:00:02",
                "2024-01-01 00:00:03",
                "2024-01-01 00:00:04",
                "2024-01-01 00:00:05",
            ]
        )

    cell.cellpy_units = CellpyUnits()
    cell.data.raw = raw
    cell.cell_name = "synthetic"
    return cell


def test_preferred_headers_default(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "out.bdf.csv")
    df = pd.read_csv(out)

    assert "Test Time / s" in df.columns
    assert "Voltage / V" in df.columns
    assert "Current / A" in df.columns
    assert any("/" in col for col in df.columns)


def test_machine_headers(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")
    df = pd.read_csv(out)

    assert "test_time_second" in df.columns
    assert "voltage_volt" in df.columns
    assert "current_ampere" in df.columns
    assert not any("/" in col for col in df.columns)


def test_capacity_unit_mAh_to_Ah(tmp_path: Path) -> None:
    """Source unit comes from ``data.raw_units``: mAh -> Ah scales by 1e-3."""
    cell = _make_synthetic_cell()
    cell.data.raw_units.charge = "mAh"

    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")
    df = pd.read_csv(out)

    assert df["charging_capacity_ah"].max() == pytest.approx(0.1)
    assert df["discharging_capacity_ah"].max() == pytest.approx(0.1)


def test_capacity_unit_passes_through_when_raw_already_Ah(tmp_path: Path) -> None:
    """Regression: when the loader's ``raw_units.charge == "Ah"`` (as for
    instruments like ``batmo_bdf``) the raw column is already in Ah and
    must not be re-scaled by the ``cellpy_units`` charge default (mAh).
    """
    cell = _make_synthetic_cell()
    cell.data.raw_units.charge = "Ah"
    cell.cellpy_units.charge = "mAh"

    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")
    df = pd.read_csv(out)

    assert df["charging_capacity_ah"].max() == pytest.approx(100.0)
    assert df["discharging_capacity_ah"].max() == pytest.approx(100.0)


def test_non_default_current_unit_uses_pint(tmp_path: Path) -> None:
    """Override raw_units.current to mA and verify pint scales mA->A correctly.

    Locks in that unit conversion is delegated to cellpy.readers.data_structures.Q
    (pint) rather than a hand-rolled factor table.
    """
    cell = _make_synthetic_cell()
    cell.data.raw_units.current = "mA"

    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")
    df = pd.read_csv(out)

    assert df["current_ampere"].max() == pytest.approx(0.1 * 1e-3)
    assert df["current_ampere"].min() == pytest.approx(-0.1 * 1e-3)


def test_datetime_to_unix_seconds(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")
    df = pd.read_csv(out)

    expected_first = pd.Timestamp("2024-01-01 00:00:00", tz="UTC").timestamp()
    assert df["unix_time_second"].iloc[0] == pytest.approx(expected_first)
    assert df["unix_time_second"].iloc[-1] == pytest.approx(expected_first + 5.0)


def test_cycle_filter_passthrough(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "out.bdf.csv", cycles=[2], header_style="machine")
    df = pd.read_csv(out)

    assert set(df["cycle_count"]) == {2}
    assert len(df) == 2


def test_last_cycle_filter(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "out.bdf.csv", last_cycle=2, header_style="machine")
    df = pd.read_csv(out)

    assert set(df["cycle_count"]) == {1, 2}


def test_missing_required_raises(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    headers = cell.headers_normal
    cell.data.raw = cell.data.raw.drop(columns=[headers.voltage_txt])

    with pytest.raises(ValueError, match="Voltage / V"):
        cell.to_bdf(tmp_path / "out.bdf.csv")


def test_missing_recommended_warns_but_writes(tmp_path: Path, caplog) -> None:
    cell = _make_synthetic_cell(with_datetime=False)

    with caplog.at_level(logging.WARNING, logger="cellpy.exporters.bdf"):
        out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")

    df = pd.read_csv(out)
    assert "unix_time_second" not in df.columns
    assert any("Unix Time" in rec.message for rec in caplog.records)


def test_default_extension_is_bdf_csv(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "no_suffix")
    assert out.suffixes[-2:] == [".bdf", ".csv"]
    assert out.is_file()


def test_explicit_suffix_is_honoured(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "explicit.csv")
    assert out.name == "explicit.csv"
    assert out.is_file()


def test_parquet_round_trip(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    cell = _make_synthetic_cell()
    out = cell.to_bdf(tmp_path / "out", format="parquet", header_style="machine")
    assert out.suffix == ".parquet"
    df = pd.read_parquet(out)
    assert "voltage_volt" in df.columns
    assert len(df) == 6


def test_empty_raw_raises(tmp_path: Path) -> None:
    from cellpy import cellreader

    cell = cellreader.CellpyCell(initialize=True)
    cell.data.raw = pd.DataFrame()

    with pytest.raises(ValueError, match="empty"):
        cell.to_bdf(tmp_path / "out.bdf.csv")


def test_empty_cycle_filter_logs_warning(tmp_path: Path, caplog) -> None:
    cell = _make_synthetic_cell()
    with caplog.at_level(logging.WARNING, logger="cellpy.exporters.bdf"):
        out = cell.to_bdf(tmp_path / "out.bdf.csv", cycles=[999])
    df = pd.read_csv(out)
    assert df.empty or len(df) == 0
    assert any("empty DataFrame" in rec.message for rec in caplog.records)


def test_extras_default_excludes_unmapped_columns(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    cell.data.raw["aux_temperature"] = [20.0, 20.1, 20.2, 20.3, 20.4, 20.5]
    cell.data.raw["custom_flag"] = [0, 1, 0, 1, 0, 1]

    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine")
    df = pd.read_csv(out)

    assert "aux_temperature" not in df.columns
    assert "custom_flag" not in df.columns


def test_extras_true_appends_all_unmapped_columns(tmp_path: Path, caplog) -> None:
    cell = _make_synthetic_cell()
    cell.data.raw["aux_temperature"] = [20.0, 20.1, 20.2, 20.3, 20.4, 20.5]
    cell.data.raw["custom_flag"] = [0, 1, 0, 1, 0, 1]

    with caplog.at_level(logging.INFO, logger="cellpy.exporters.bdf"):
        out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine", extras=True)
    df = pd.read_csv(out)

    assert "aux_temperature" in df.columns
    assert "custom_flag" in df.columns
    assert df["aux_temperature"].iloc[0] == pytest.approx(20.0)
    assert any("non-BDF column" in rec.message for rec in caplog.records)


def test_extras_iterable_appends_only_listed_columns(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    cell.data.raw["aux_temperature"] = [20.0, 20.1, 20.2, 20.3, 20.4, 20.5]
    cell.data.raw["custom_flag"] = [0, 1, 0, 1, 0, 1]

    out = cell.to_bdf(
        tmp_path / "out.bdf.csv",
        header_style="machine",
        extras=["aux_temperature"],
    )
    df = pd.read_csv(out)

    assert "aux_temperature" in df.columns
    assert "custom_flag" not in df.columns


def test_extras_string_treated_as_single_column(tmp_path: Path) -> None:
    cell = _make_synthetic_cell()
    cell.data.raw["aux_temperature"] = [20.0, 20.1, 20.2, 20.3, 20.4, 20.5]

    out = cell.to_bdf(
        tmp_path / "out.bdf.csv",
        header_style="machine",
        extras="aux_temperature",
    )
    df = pd.read_csv(out)

    assert "aux_temperature" in df.columns


def test_extras_unknown_column_warns_and_skips(tmp_path: Path, caplog) -> None:
    cell = _make_synthetic_cell()

    with caplog.at_level(logging.WARNING, logger="cellpy.exporters.bdf"):
        out = cell.to_bdf(
            tmp_path / "out.bdf.csv",
            header_style="machine",
            extras=["does_not_exist"],
        )
    df = pd.read_csv(out)

    assert "does_not_exist" not in df.columns
    assert any("does_not_exist" in rec.message for rec in caplog.records)


def test_extras_skips_columns_already_in_bdf_map(tmp_path: Path) -> None:
    """Naming a mapped raw column under ``extras`` must not duplicate it."""
    cell = _make_synthetic_cell()
    headers = cell.headers_normal

    out = cell.to_bdf(
        tmp_path / "out.bdf.csv",
        header_style="machine",
        extras=[headers.voltage_txt],
    )
    df = pd.read_csv(out)

    assert headers.voltage_txt not in df.columns
    assert "voltage_volt" in df.columns
    assert (df.columns == "voltage_volt").sum() == 1


def test_extras_values_are_not_unit_converted(tmp_path: Path) -> None:
    """Charge in `mAh` would normally be scaled; as an extra it must stay raw."""
    cell = _make_synthetic_cell()
    cell.data.raw["raw_charge_mAh"] = [0.0, 50.0, 100.0, 50.0, 0.0, 25.0]

    out = cell.to_bdf(
        tmp_path / "out.bdf.csv",
        header_style="machine",
        extras=["raw_charge_mAh"],
    )
    df = pd.read_csv(out)

    assert df["raw_charge_mAh"].max() == pytest.approx(100.0)


def test_module_does_not_import_from_cellpy_utils() -> None:
    """Architectural rule: cellpy.exporters.bdf must not depend on cellpy.utils.

    Recorded in .issueflows/04-designs-and-guides/bdf-export.md.
    """
    src = Path(bdf_module.__file__).read_text(encoding="utf-8")
    offending = [
        line
        for line in src.splitlines()
        if line.strip().startswith(("import cellpy.utils", "from cellpy.utils"))
    ]
    assert offending == [], f"Unexpected cellpy.utils imports: {offending}"


# --- bdf_units= override (issue #365) -------------------------------------


def test_bdf_units_none_matches_default_path(tmp_path: Path) -> None:
    """Explicit ``bdf_units=None`` is byte-for-byte identical to the default path."""
    cell_a = _make_synthetic_cell()
    cell_b = _make_synthetic_cell()

    out_a = cell_a.to_bdf(tmp_path / "a.bdf.csv")
    out_b = cell_b.to_bdf(tmp_path / "b.bdf.csv", bdf_units=None)

    df_a = pd.read_csv(out_a)
    df_b = pd.read_csv(out_b)
    pd.testing.assert_frame_equal(df_a, df_b)


def test_bdf_units_overrides_charge_to_mAh(tmp_path: Path) -> None:
    """Override charge unit to mAh: label and values reflect the override."""
    cell = _make_synthetic_cell()
    cell.data.raw_units.charge = "mAh"  # source

    bdf_units = CellpyUnits(charge="mAh")
    out = cell.to_bdf(tmp_path / "out.bdf.csv", bdf_units=bdf_units)
    df = pd.read_csv(out)

    assert "Charging Capacity / mAh" in df.columns
    assert "Discharging Capacity / mAh" in df.columns
    assert "Charging Capacity / Ah" not in df.columns
    # source == target == mAh, so values stay raw (100, not 0.1).
    assert df["Charging Capacity / mAh"].max() == pytest.approx(100.0)
    assert df["Discharging Capacity / mAh"].max() == pytest.approx(100.0)


def test_bdf_units_overrides_charge_to_mAh_machine_style(tmp_path: Path) -> None:
    """Machine-style header is synthesized from the override unit."""
    cell = _make_synthetic_cell()
    bdf_units = CellpyUnits(charge="mAh")

    out = cell.to_bdf(tmp_path / "out.bdf.csv", header_style="machine", bdf_units=bdf_units)
    df = pd.read_csv(out)

    assert "charging_capacity_mah" in df.columns
    assert "discharging_capacity_mah" in df.columns
    assert "charging_capacity_ah" not in df.columns


def test_bdf_units_overrides_current_to_mA(tmp_path: Path) -> None:
    """Override current to mA: factor 1000 from the source A."""
    cell = _make_synthetic_cell()
    assert cell.data.raw_units.current == "A"

    bdf_units = CellpyUnits(current="mA")
    out = cell.to_bdf(tmp_path / "out.bdf.csv", bdf_units=bdf_units)
    df = pd.read_csv(out)

    assert "Current / mA" in df.columns
    assert "Current / A" not in df.columns
    assert df["Current / mA"].max() == pytest.approx(100.0)
    assert df["Current / mA"].min() == pytest.approx(-100.0)


def test_bdf_units_overrides_time_to_minutes(tmp_path: Path) -> None:
    """Override time to minutes: values divided by 60."""
    cell = _make_synthetic_cell()

    bdf_units = CellpyUnits(time="min")
    out = cell.to_bdf(tmp_path / "out.bdf.csv", bdf_units=bdf_units)
    df = pd.read_csv(out)

    assert "Test Time / min" in df.columns
    assert "Test Time / s" not in df.columns
    assert df["Test Time / min"].iloc[-1] == pytest.approx(5.0 / 60.0)


def test_bdf_units_partial_override_keeps_defaults(tmp_path: Path) -> None:
    """Unchanged kinds keep canonical BDF spec spelling and values.

    `sec` is pint-equivalent to `s` so the default ``CellpyUnits().time``
    must not flip the time column away from the BDF canonical label.
    """
    cell_default = _make_synthetic_cell()
    cell_override = _make_synthetic_cell()

    out_default = cell_default.to_bdf(tmp_path / "default.bdf.csv")
    out_override = cell_override.to_bdf(
        tmp_path / "override.bdf.csv",
        bdf_units=CellpyUnits(charge="mAh"),
    )
    df_default = pd.read_csv(out_default)
    df_override = pd.read_csv(out_override)

    # Untouched columns byte-for-byte identical to the no-override file.
    for col in ("Test Time / s", "Voltage / V", "Current / A", "Unix Time / s"):
        assert col in df_default.columns
        assert col in df_override.columns
        pd.testing.assert_series_equal(
            df_default[col], df_override[col], check_names=False
        )

    # Charge columns moved to mAh; old Ah labels gone.
    assert "Charging Capacity / mAh" in df_override.columns
    assert "Charging Capacity / Ah" not in df_override.columns


def test_bdf_units_does_not_mutate_inputs(tmp_path: Path) -> None:
    """`to_bdf` must not mutate `cell.cellpy_units` or the passed-in object."""
    cell = _make_synthetic_cell()
    cellpy_units_snapshot = {
        "charge": cell.cellpy_units.charge,
        "current": cell.cellpy_units.current,
        "time": cell.cellpy_units.time,
    }

    bdf_units = CellpyUnits(charge="mAh", current="mA")
    passed_snapshot = {"charge": bdf_units.charge, "current": bdf_units.current}

    cell.to_bdf(tmp_path / "out.bdf.csv", bdf_units=bdf_units)

    assert cell.cellpy_units.charge == cellpy_units_snapshot["charge"]
    assert cell.cellpy_units.current == cellpy_units_snapshot["current"]
    assert cell.cellpy_units.time == cellpy_units_snapshot["time"]
    assert bdf_units.charge == passed_snapshot["charge"]
    assert bdf_units.current == passed_snapshot["current"]


def test_bdf_units_incompatible_unit_raises(tmp_path: Path) -> None:
    """A unit pint cannot convert (e.g. `charge="kg"`) raises ValueError."""
    cell = _make_synthetic_cell()
    bdf_units = CellpyUnits(charge="kg")

    with pytest.raises(ValueError, match="charge|kg|mAh"):
        cell.to_bdf(tmp_path / "out.bdf.csv", bdf_units=bdf_units)


def test_bdf_units_pint_equivalent_keeps_canonical_label(tmp_path: Path) -> None:
    """`time="s"` (vs spec default `s`) keeps the BDF canonical label."""
    cell = _make_synthetic_cell()
    out = cell.to_bdf(
        tmp_path / "out.bdf.csv",
        bdf_units=CellpyUnits(time="s"),
    )
    df = pd.read_csv(out)
    assert "Test Time / s" in df.columns


def test_bdf_units_logs_non_strict_warning(tmp_path: Path, caplog) -> None:
    """One INFO line is emitted when the override is not strictly BDF."""
    cell = _make_synthetic_cell()
    with caplog.at_level(logging.INFO, logger="cellpy.exporters.bdf"):
        cell.to_bdf(
            tmp_path / "out.bdf.csv",
            bdf_units=CellpyUnits(charge="mAh"),
        )
    assert any(
        "not strictly BDF-compliant" in rec.message for rec in caplog.records
    )
