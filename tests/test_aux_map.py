"""Legacy Arbin aux column names → harmonized ``aux_<quantity>_<name>`` (#560)."""

from __future__ import annotations

from cellpy.readers.instruments._aux_map import (
    aux_map_from_columns,
    map_one_aux_column,
)


def test_wide_aux_temperature_and_potential():
    assert map_one_aux_column("aux_0_u_C") == "aux_temperature_0"
    assert map_one_aux_column("aux_3_u_V") == "aux_potential_3"


def test_wide_aux_derivative():
    assert map_one_aux_column("aux_d_0_dt_u_dC_dt") == "aux_temperature_d0_dt"


def test_sql_export_aux_columns():
    assert map_one_aux_column("Aux_Voltage_1") == "aux_potential_1"
    assert map_one_aux_column("Aux_Temperature_2") == "aux_temperature_2"


def test_unknown_unit_or_plain_column_is_none():
    assert map_one_aux_column("aux_0_u_weird") is None
    assert map_one_aux_column("Data_Point") is None


def test_aux_map_skips_already_declared_columns():
    columns = ["aux_0_u_C", "Aux_Voltage_1", "Data_Point"]
    # Aux_Voltage_1 already claimed as reference_voltage passthrough on h5.
    mapping = aux_map_from_columns(columns, already_declared=("Aux_Voltage_1",))
    assert mapping == {"aux_0_u_C": "aux_temperature_0"}
