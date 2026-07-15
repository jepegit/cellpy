"""Pipeline helpers for value-parity tests (issue #434)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl
from cellpycore import Data, summarizers
from cellpycore.cell_core import _cycle_mode_to_test_mode
from cellpycore.config import default_schema
from cellpycore.legacy import mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"


def res_file_available() -> bool:
    return RES_FILE.is_file()


def run_legacy_pipeline(cell) -> None:
    """Load the canonical Arbin ``.res`` and run steps + summary on ``cell``."""
    cell.set_instrument("arbin_res")
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary(find_ir=True, find_end_voltage=True)


def _current_conversion_factor(cell) -> float:
    from cellpy.readers import data_structures as core

    data = cell.data
    return float(
        (
            core.Q(1.0, data.raw_units["current"])
            / core.Q(1.0, cell.cellpy_units["current"])
        )
        .to_reduced_units()
        .magnitude
    )


def _specific_converters(cell) -> dict[str, float]:
    modes = ("gravimetric", "areal", "absolute")
    return {
        mode: cell.get_converter_to_specific(
            dataset=cell.data, mode=mode, to_units=cell.cellpy_units
        )
        for mode in modes
    }


def _nom_cap_abs_for_c_rate(cell) -> float:
    """Resolve absolute nominal capacity the same way ``make_step_table`` does."""
    nom_cap = cell.data.nom_cap
    specifics = cell.nom_cap_specifics
    mass = cell.data.mass or 1.0
    if specifics == "gravimetric":
        return cell.nominal_capacity_as_absolute(nom_cap, mass, specifics)
    if specifics == "areal":
        return cell.nominal_capacity_as_absolute(
            nom_cap, cell.data.active_electrode_area, specifics
        )
    if specifics == "absolute":
        return cell.nominal_capacity_as_absolute(nom_cap, 1.0, specifics)
    return cell.nominal_capacity_as_absolute(nom_cap, mass, specifics)


def _nom_cap_abs(cell) -> float:
    return _nom_cap_abs_for_c_rate(cell)


def build_native_raw(cell) -> pd.DataFrame:
    """Native raw frame from the legacy bridge input."""
    rename = mapping.legacy_to_native_raw(cell.data.raw.columns)
    return cell.data.raw.rename(columns=rename).reset_index(drop=True)


def build_native_steps(cell) -> pd.DataFrame:
    """Native step table from the polars engine (pre-legacy rename)."""
    schema = default_schema()
    nom_cap_abs = _nom_cap_abs_for_c_rate(cell)
    native_raw = pl.from_pandas(build_native_raw(cell))
    tmp = Data()
    tmp.raw = native_raw
    summarizers.make_step_table(tmp, schema=schema, sort_rows=False)
    native_steps = tmp.steps.with_columns(
        summarizers._step_c_rate_expr(schema.step, nom_cap_abs)
    )
    return native_steps.to_pandas()


def build_native_summary(cell) -> pd.DataFrame:
    """Native summary from the polars engine (pre-legacy rename, incl. specific cols)."""
    schema = default_schema()
    native_raw = pl.from_pandas(build_native_raw(cell))
    native_steps = pl.from_pandas(
        cell.data.steps.rename(columns=mapping.legacy_to_native_step())
    )
    nd = Data()
    nd.raw = native_raw
    nd.steps = native_steps
    # Honor cycle_mode the same way the legacy bridge does (cellpycore #129).
    test_mode = _cycle_mode_to_test_mode(cell.core.cycle_mode)
    summarizers.make_summary(nd, schema, test_mode=test_mode)
    if schema.raw.internal_resistance in native_raw.columns:
        summarizers.ir_to_summary(nd, schema)
    summarizers.c_rates_to_summary(
        nd, schema, current_conversion_factor=_current_conversion_factor(cell)
    )

    step_txt = (
        schema.cycle.discharge_capacity
        if test_mode.name == "INVERTED"
        else schema.cycle.charge_capacity
    )
    summarizers.equivalent_cycles_to_summary(
        nd, schema, _nom_cap_abs(cell), None, step_txt
    )
    factors = summarizers._resolve_specific_conversion_factors(
        None, _specific_converters(cell)
    )
    for mode in ("gravimetric", "areal", "absolute"):
        factor = factors[mode]
        summarizers.generate_specific_summary_columns(
            nd, mode, schema.cycle.specific_columns, factor
        )
    return nd.summary.to_pandas()
