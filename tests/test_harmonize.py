"""Declaration + harmonize() tests (#559).

The reset-granularity cases carry hand-computed expectations rather than
values read back from the implementation: a wrong granularity conversion does
not raise, it silently rescales every capacity in the dataset, so the test has
to know the right answer independently.
"""

from __future__ import annotations

import logging

import polars as pl
import pytest
from cellpycore.config import default_schema
from cellpycore.units import CellpyUnits

from cellpy import log
from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.declarations import (
    LoaderDeclarations,
    ResetGranularity,
)
from cellpy.readers.instruments.harmonize import (
    harmonize,
    normalize_reset_granularity,
)

log.setup_logging(default_level=logging.DEBUG, testing=True)

SCHEMA = default_schema().raw


# -- declarations validate at construction -------------------------------------


@pytest.mark.essential
def test_valid_declarations_construct():
    declarations = LoaderDeclarations(
        column_map={"Volts": SCHEMA.potential, "Amps": SCHEMA.current},
        raw_units=CellpyUnits(),
    )
    assert declarations.native_columns == (SCHEMA.potential, SCHEMA.current)


@pytest.mark.essential
def test_typo_in_a_native_column_name_fails_immediately():
    # The point of validating at construction: this is an import-time error in
    # the configuration module, not a surprise mid-load.
    with pytest.raises(LoaderError, match="not in the harmonized-raw schema"):
        LoaderDeclarations(
            column_map={"Volts": "potentail"},  # typo
            raw_units=CellpyUnits(),
        )


@pytest.mark.essential
def test_two_vendor_columns_mapped_onto_one_native_column_fails():
    with pytest.raises(LoaderError, match="more than one vendor column"):
        LoaderDeclarations(
            column_map={"Volts": SCHEMA.potential, "V2": SCHEMA.potential},
            raw_units=CellpyUnits(),
        )


@pytest.mark.essential
def test_granularity_for_a_column_that_is_never_produced_fails():
    # Otherwise the declaration looks meaningful but does nothing.
    with pytest.raises(LoaderError, match="which column_map never produces"):
        LoaderDeclarations(
            column_map={"Volts": SCHEMA.potential},
            raw_units=CellpyUnits(),
            reset_granularity={
                SCHEMA.cumulative_charge_capacity: ResetGranularity.PER_TEST
            },
        )


@pytest.mark.essential
def test_bad_aux_name_fails():
    with pytest.raises(LoaderError, match="aux_<quantity>_<name>"):
        LoaderDeclarations(
            column_map={"Volts": SCHEMA.potential},
            raw_units=CellpyUnits(),
            aux_map={"T1": "aux_temp_cell"},  # "temp" is not a known quantity
        )


# -- reset granularity ---------------------------------------------------------


def _frame(cycles, steps, values) -> pl.DataFrame:
    return pl.DataFrame(
        {
            SCHEMA.cycle_num: cycles,
            SCHEMA.step_num: steps,
            SCHEMA.cumulative_charge_capacity: [float(v) for v in values],
        }
    )


def _declarations(granularity) -> LoaderDeclarations:
    return LoaderDeclarations(
        column_map={
            "cyc": SCHEMA.cycle_num,
            "stp": SCHEMA.step_num,
            "cap": SCHEMA.cumulative_charge_capacity,
        },
        raw_units=CellpyUnits(),
        reset_granularity={SCHEMA.cumulative_charge_capacity: granularity},
    )


@pytest.mark.essential
def test_per_cycle_is_the_target_and_is_untouched():
    # Two cycles, each already restarting from zero.
    frame = _frame(
        cycles=[1, 1, 1, 2, 2, 2],
        steps=[1, 1, 2, 1, 1, 2],
        values=[0.0, 1.0, 3.0, 0.0, 2.0, 5.0],
    )
    out = normalize_reset_granularity(frame, _declarations(ResetGranularity.PER_CYCLE))
    assert out[SCHEMA.cumulative_charge_capacity].to_list() == [
        0.0,
        1.0,
        3.0,
        0.0,
        2.0,
        5.0,
    ]


@pytest.mark.essential
def test_per_test_is_rebased_at_each_cycle_boundary():
    # A never-resetting column: cycle 1 runs 0->3, cycle 2 continues 3->8.
    # Expected: cycle 2 rebased to start at zero, i.e. 0, 2, 5.
    frame = _frame(
        cycles=[1, 1, 1, 2, 2, 2],
        steps=[1, 1, 2, 1, 1, 2],
        values=[0.0, 1.0, 3.0, 3.0, 5.0, 8.0],
    )
    out = normalize_reset_granularity(frame, _declarations(ResetGranularity.PER_TEST))
    assert out[SCHEMA.cumulative_charge_capacity].to_list() == [
        0.0,
        1.0,
        3.0,
        0.0,
        2.0,
        5.0,
    ]


@pytest.mark.essential
def test_per_step_accumulates_completed_steps_within_the_cycle():
    # Each step restarts at zero:
    #   cycle 1: step 1 -> 0,1,2 ; step 2 -> 0,3   (step 1 finished at 2)
    #   cycle 2: step 1 -> 0,4   ; step 2 -> 0,1   (step 1 finished at 4)
    # Expected cycle-cumulative:
    #   cycle 1: 0,1,2 then 2+0=2, 2+3=5
    #   cycle 2: 0,4   then 4+0=4, 4+1=5
    frame = _frame(
        cycles=[1, 1, 1, 1, 1, 2, 2, 2, 2],
        steps=[1, 1, 1, 2, 2, 1, 1, 2, 2],
        values=[0.0, 1.0, 2.0, 0.0, 3.0, 0.0, 4.0, 0.0, 1.0],
    )
    out = normalize_reset_granularity(frame, _declarations(ResetGranularity.PER_STEP))
    assert out[SCHEMA.cumulative_charge_capacity].to_list() == [
        0.0,
        1.0,
        2.0,
        2.0,
        5.0,
        0.0,
        4.0,
        4.0,
        5.0,
    ]


@pytest.mark.essential
def test_per_cycle_capacity_is_the_cycle_last_value():
    """The property the summary path depends on.

    Per the harmonized-raw spec, per-cycle capacity is read from the cycle's
    last datapoint. After normalization that must hold for every granularity.
    """
    expected = {1: 3.0, 2: 5.0}

    per_test = _frame(
        cycles=[1, 1, 1, 2, 2, 2],
        steps=[1, 1, 2, 1, 1, 2],
        values=[0.0, 1.0, 3.0, 3.0, 5.0, 8.0],
    )
    out = normalize_reset_granularity(per_test, _declarations(ResetGranularity.PER_TEST))
    last = (
        out.group_by(SCHEMA.cycle_num, maintain_order=True)
        .agg(pl.col(SCHEMA.cumulative_charge_capacity).last().alias("cap"))
        .to_dict(as_series=False)
    )
    assert dict(zip(last[SCHEMA.cycle_num], last["cap"])) == expected


@pytest.mark.essential
def test_per_step_without_a_step_column_fails_loudly():
    frame = pl.DataFrame(
        {
            SCHEMA.cycle_num: [1, 1],
            SCHEMA.cumulative_charge_capacity: [0.0, 1.0],
        }
    )
    with pytest.raises(LoaderError, match="needs"):
        normalize_reset_granularity(frame, _declarations(ResetGranularity.PER_STEP))


# -- harmonize -----------------------------------------------------------------


def _vendor_frame() -> pl.DataFrame:
    # Realistic: a loader must supply every column validate_raw_frame requires,
    # so the fixture does too — harmonize() deliberately does not invent them,
    # which would hide a loader that forgot to map its capacity column.
    return pl.DataFrame(
        {
            "Rec#": [1, 2, 3, 4],
            "Volts": [3.0, 3.1, 3.2, 3.3],
            "Amps": [0.1, 0.1, -0.1, -0.1],
            "Cyc#": [1, 1, 2, 2],
            "Step": [1, 1, 1, 1],
            "TestTime": [0.0, 1.0, 2.0, 3.0],
            "Stamp": [
                1_700_000_000_000_000_000,
                1_700_000_001_000_000_000,
                1_700_000_002_000_000_000,
                1_700_000_003_000_000_000,
            ],
            "ChgAh": [0.0, 0.5, 0.0, 0.0],
            "DchAh": [0.0, 0.0, 0.0, 0.5],
            "Ignored": ["a", "b", "c", "d"],
        }
    )


def _vendor_declarations() -> LoaderDeclarations:
    return LoaderDeclarations(
        column_map={
            "Rec#": SCHEMA.datapoint_num,
            "Volts": SCHEMA.potential,
            "Amps": SCHEMA.current,
            "Cyc#": SCHEMA.cycle_num,
            "Step": SCHEMA.step_num,
            "TestTime": SCHEMA.test_time,
            "Stamp": SCHEMA.epoch_time_utc,
            "ChgAh": SCHEMA.cumulative_charge_capacity,
            "DchAh": SCHEMA.cumulative_discharge_capacity,
        },
        raw_units=CellpyUnits(),
    )


@pytest.mark.essential
def test_harmonize_renames_and_drops_undeclared_columns():
    out = harmonize(_vendor_frame(), _vendor_declarations())
    assert SCHEMA.potential in out.columns
    assert "Volts" not in out.columns
    assert "Ignored" not in out.columns, "undeclared vendor columns must not survive"


@pytest.mark.essential
def test_harmonize_casts_to_schema_dtypes():
    out = harmonize(_vendor_frame(), _vendor_declarations())
    dtype_map = SCHEMA.dtype_map()
    for column in out.columns:
        if column in dtype_map:
            assert out[column].dtype == dtype_map[column], column


@pytest.mark.essential
def test_harmonize_stamps_identity():
    out = harmonize(_vendor_frame(), _vendor_declarations(), test_id=7)
    assert out[SCHEMA.test_id].to_list() == [7, 7, 7, 7]
    assert out[SCHEMA.mask].to_list() == [True] * 4


@pytest.mark.essential
def test_harmonize_accepts_a_pandas_frame():
    # Legacy parsers return pandas; the port should not require rewriting them
    # before harmonize() can be used.
    import pandas as pd

    out = harmonize(_vendor_frame().to_pandas(), _vendor_declarations())
    assert isinstance(out, pl.DataFrame)
    assert out.height == 4


@pytest.mark.essential
def test_harmonize_runs_post_hooks_before_renaming():
    def double_volts(frame: pl.DataFrame) -> pl.DataFrame:
        # Hooks see vendor names, since they fix vendor quirks.
        assert "Volts" in frame.columns
        return frame.with_columns((pl.col("Volts") * 2).alias("Volts"))

    declarations = LoaderDeclarations(
        column_map=dict(_vendor_declarations().column_map),
        raw_units=CellpyUnits(),
        post_hooks=(double_volts,),
    )
    out = harmonize(_vendor_frame(), declarations)
    assert out[SCHEMA.potential].to_list() == [6.0, 6.2, 6.4, 6.6]


@pytest.mark.essential
def test_harmonize_keeps_datapoint_num_a_column_not_an_index():
    out = harmonize(_vendor_frame(), _vendor_declarations())
    assert SCHEMA.datapoint_num in out.columns


# -- the property test that catches a wrong granularity declaration ------------


@pytest.mark.essential
def test_harmonized_per_cycle_capacities_match_the_legacy_pipeline():
    """The correctness landmine of the whole loader port (loader plan §5).

    A wrong ``reset_granularity`` declaration does not raise — it silently
    rescales every capacity. The only thing that catches it is recomputing
    per-cycle capacities from the harmonized raw and comparing them against an
    independent pipeline on the same file.

    Note the legacy path shifts cycle numbers so they start at 1
    (``set_cycle_number_not_zero``), which the native pilot does not; compare
    by position, not by cycle number.
    """
    import warnings

    import cellpy
    import cellpy.utils.example_data as ed
    from cellpy.readers.instruments.maccor_txt_native import MaccorTxtLoader

    source = ed.maccor_file_path()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        legacy = cellpy.get(
            source, instrument="maccor_txt", model="THREE", mass=1.0, testing=True
        )
    legacy_summary = legacy.data.summary
    legacy_charge = legacy_summary[legacy.schema.summary.charge_capacity].tolist()
    legacy_discharge = legacy_summary[
        legacy.schema.summary.discharge_capacity
    ].tolist()

    raw = MaccorTxtLoader().load(source)[0].raw
    per_cycle = raw.group_by(SCHEMA.cycle_num, maintain_order=True).agg(
        pl.col(SCHEMA.cumulative_charge_capacity).last().alias("charge"),
        pl.col(SCHEMA.cumulative_discharge_capacity).last().alias("discharge"),
    )
    native_charge = per_cycle["charge"].to_list()
    native_discharge = per_cycle["discharge"].to_list()

    assert len(native_charge) == len(legacy_charge)
    for cycle, (native, legacy_value) in enumerate(
        zip(native_charge, legacy_charge), start=1
    ):
        assert native == pytest.approx(legacy_value, rel=1e-9), (
            f"charge capacity disagrees at cycle {cycle}: harmonized {native} "
            f"vs legacy {legacy_value} — check the reset_granularity declaration"
        )
    for cycle, (native, legacy_value) in enumerate(
        zip(native_discharge, legacy_discharge), start=1
    ):
        assert native == pytest.approx(legacy_value, rel=1e-9), (
            f"discharge capacity disagrees at cycle {cycle}: harmonized {native} "
            f"vs legacy {legacy_value} — check the reset_granularity declaration"
        )


@pytest.mark.essential
def test_a_wrong_granularity_declaration_would_be_caught():
    """Prove the property test above has teeth.

    Re-run the same comparison with the declaration deliberately wrong; the
    per-cycle values must then disagree. A property test that cannot fail is
    not protecting anything.
    """
    import warnings

    import cellpy.utils.example_data as ed
    from cellpy.readers.instruments import maccor_txt_native as pilot

    source = ed.maccor_file_path()

    correct = pilot.MaccorTxtLoader().load(source)[0].raw
    correct_per_cycle = (
        correct.group_by(SCHEMA.cycle_num, maintain_order=True)
        .agg(pl.col(SCHEMA.cumulative_charge_capacity).last().alias("charge"))["charge"]
        .to_list()
    )

    wrong_declarations = LoaderDeclarations(
        column_map=dict(pilot.MACCOR_THREE.column_map),
        raw_units=pilot.MACCOR_THREE.raw_units,
        reset_granularity={
            SCHEMA.cumulative_charge_capacity: ResetGranularity.PER_TEST,
            SCHEMA.cumulative_discharge_capacity: ResetGranularity.PER_TEST,
        },
        post_hooks=pilot.MACCOR_THREE.post_hooks,
    )

    class WrongLoader(pilot.MaccorTxtLoader):
        declarations = wrong_declarations

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wrong = WrongLoader().load(source)[0].raw
    wrong_per_cycle = (
        wrong.group_by(SCHEMA.cycle_num, maintain_order=True)
        .agg(pl.col(SCHEMA.cumulative_charge_capacity).last().alias("charge"))["charge"]
        .to_list()
    )

    assert wrong_per_cycle != correct_per_cycle, (
        "a deliberately wrong reset_granularity produced identical capacities; "
        "the property test would not catch a real mis-declaration"
    )


# --- unknown vendor columns: warn + drop (#560 decision, 2026-07-20) ----------


def _minimal_declarations(**overrides):
    from cellpycore.config import default_schema
    from cellpycore.units import CellpyUnits

    from cellpy.readers.instruments.declarations import LoaderDeclarations

    schema = default_schema().raw
    settings = dict(
        column_map={
            "Rec": schema.datapoint_num,
            "Cyc": schema.cycle_num,
            "Step": schema.step_num,
            "T": schema.test_time,
            "Epoch": schema.epoch_time_utc,
            "I": schema.current,
            "V": schema.potential,
            "QC": schema.cumulative_charge_capacity,
            "QD": schema.cumulative_discharge_capacity,
        },
        raw_units=CellpyUnits(),
    )
    settings.update(overrides)
    return LoaderDeclarations(**settings)


def _minimal_vendor_frame(**extra_columns):
    import polars as pl

    base = {
        "Rec": [1, 2],
        "Cyc": [1, 1],
        "Step": [1, 1],
        "T": [0.0, 1.0],
        "Epoch": [1.6e9, 1.6e9 + 1],
        "I": [0.1, 0.1],
        "V": [3.0, 3.1],
        "QC": [0.0, 0.1],
        "QD": [0.0, 0.0],
    }
    base.update(extra_columns)
    return pl.DataFrame(base)


@pytest.mark.essential
def test_unknown_vendor_column_warns_and_is_dropped(caplog):
    from cellpy.readers.instruments.harmonize import harmonize

    frame = _minimal_vendor_frame(Junk=[9, 9])
    with caplog.at_level(logging.WARNING):
        raw = harmonize(frame, _minimal_declarations(), test_id=1)

    assert "Junk" in caplog.text, "no warning named the unrecognised column"
    assert "Junk" not in raw.columns, "the unrecognised column leaked through"


@pytest.mark.essential
def test_declared_discards_are_dropped_silently(caplog):
    """Columns in `dropped` are known — a warning would just be noise."""
    from cellpy.readers.instruments.harmonize import harmonize

    frame = _minimal_vendor_frame(StateFlag=["C", "D"])
    declarations = _minimal_declarations(dropped=("StateFlag",))
    with caplog.at_level(logging.WARNING):
        raw = harmonize(frame, declarations, test_id=1)

    assert "StateFlag" not in caplog.text
    assert "StateFlag" not in raw.columns


@pytest.mark.essential
def test_a_column_cannot_be_both_declared_and_dropped():
    from cellpy.exceptions import LoaderError

    with pytest.raises(LoaderError, match="both declared and dropped"):
        _minimal_declarations(dropped=("V",))
