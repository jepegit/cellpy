"""Two-stage declarations for the four fixture-less Arbin variants (#560).

``arbin_sql`` and ``arbin_sql_7`` need a live SQL Server; ``arbin_sql_csv`` and
``arbin_sql_xlsx`` read exports for which there is no in-repo fixture. So unlike
``arbin_sql_h5`` (see ``test_arbin_sql_h5_two_stage.py``) these cannot be checked
against a golden frame end-to-end. What *is* checkable — and is the part most
likely to be wrong — is that ``declarations()`` maps the vendor columns to the
right native columns, drops ``Test_ID`` as provenance, and picks the correct
``datetime_kind``. That is what this module pins, no backend required.

The ``arbin_epoch`` decode itself (shared with ``arbin_sql_h5``) is checked
here directly and, end-to-end on a real fixture, in ``test_arbin_sql_h5``.
"""

from __future__ import annotations

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments import (
    arbin_sql,
    arbin_sql_7,
    arbin_sql_csv,
    arbin_sql_xlsx,
)

# module, bare-or-suffixed vendor names, expected datetime_kind.
_VARIANTS = {
    "arbin_sql": (arbin_sql, "Voltage", "Current", "Internal_Resistance",
                  "Charge_Capacity", "Discharge_Capacity", "arbin_epoch"),
    "arbin_sql_7": (arbin_sql_7, "Voltage", "Current", "Internal_Resistance",
                    "Charge_Capacity", "Discharge_Capacity", "arbin_epoch"),
    "arbin_sql_csv": (arbin_sql_csv, "Voltage(V)", "Current(A)",
                      "Internal_Resistance(Ohm)", "Charge_Capacity(Ah)",
                      "Discharge_Capacity(Ah)", "string"),
    "arbin_sql_xlsx": (arbin_sql_xlsx, "Voltage(V)", "Current(A)",
                       "Internal_Resistance(Ohm)", "Charge_Capacity(Ah)",
                       "Discharge_Capacity(Ah)", "datetime"),
}


def _declarations(module):
    """declarations() without a backend: the mapping needs no parsed data, only
    the loader's static renaming dict, so we set the parsed flag directly."""
    loader = module.DataLoader()
    loader._parsed = True
    return loader.declarations()


@pytest.mark.essential
@pytest.mark.parametrize("name", sorted(_VARIANTS))
def test_declarations_map_vendor_columns_to_native(name):
    module, voltage, current, ir, q_ch, q_dch, kind = _VARIANTS[name]
    column_map = _declarations(module).column_map

    assert column_map[voltage] == "potential"
    assert column_map[current] == "current"
    # The acr_txt/internal_resistance_txt collision must resolve to the real
    # header (internal_resistance), not the non-header alias that would drop it.
    assert column_map[ir] == "internal_resistance"
    assert column_map[q_ch] == "cumulative_charge_capacity"
    assert column_map[q_dch] == "cumulative_discharge_capacity"


@pytest.mark.essential
@pytest.mark.parametrize("name", sorted(_VARIANTS))
def test_test_id_is_dropped_as_provenance(name):
    column_map = _declarations(_VARIANTS[name][0]).column_map
    assert "Test_ID" not in column_map


@pytest.mark.essential
@pytest.mark.parametrize("name", sorted(_VARIANTS))
def test_datetime_kind_matches_the_vendor_form(name):
    assert _declarations(_VARIANTS[name][0]).datetime_kind == _VARIANTS[name][6]


@pytest.mark.essential
@pytest.mark.parametrize("name", sorted(_VARIANTS))
def test_declarations_before_parse_raises(name):
    loader = _VARIANTS[name][0].DataLoader()
    with pytest.raises(LoaderError, match="before parse"):
        loader.declarations()


@pytest.mark.essential
def test_arbin_epoch_decode_is_exact_hundred_ns_ticks():
    """``arbin_epoch`` turns integer 100 ns ticks into the right UTC instant.

    2020-06-24T09:45:33.4602Z is 1_593_596_733.4602 s -> 15_935_967_334_602_000
    ticks; harmonize must read that back as exactly that instant in ns UTC, with
    no float rounding (the reason the decode is integer ``x 100``, not ``/ 1e7``
    in float64).
    """
    from cellpy.readers.instruments.harmonize import _parse_datetime_column

    ticks = 15_935_967_334_602_000
    parsed = _parse_datetime_column(pl.Series([ticks]), "arbin_epoch")
    # naive Datetime carrying the UTC wall clock; epoch("ns") = ticks x 100.
    assert parsed.dt.replace_time_zone("UTC").dt.epoch("ns")[0] == ticks * 100
