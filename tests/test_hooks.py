"""Vendor post hooks: state splitting and cycle numbering (#560).

Expectations here are **hand-computed from the legacy post-processors**, not
read back from the implementation. A splitter that is subtly wrong does not
raise; it produces a plausible capacity curve, which is the failure mode this
whole arc exists to prevent.

Several tests pin quirks rather than sensible behaviour — a rest between two
charge rows reading 0, cycles starting at 2 not being rebased. They are
deliberate: the port's contract is *no change to users' numbers*, so the
quirks come across intact and improving them is a separate, release-noted
decision.
"""

from __future__ import annotations

import polars as pl
import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.hooks import (
    cycle_number_not_zero,
    state_splitter,
)

STATES = dict(charge_keys=("C",), discharge_keys=("D",))

COMMON = dict(
    state_column="State",
    cycle_column="Cyc",
    datapoint_column="Rec",
    **STATES,
)


def _frame(states, values, cycles=None, datapoints=None):
    n = len(states)
    return pl.DataFrame(
        {
            "Rec": datapoints or list(range(1, n + 1)),
            "Cyc": cycles or [1] * n,
            "State": states,
            "Q": values,
        }
    )


def _split_capacity(frame):
    hook = state_splitter(
        base_column="Q",
        charge_output="q_charge",
        discharge_output="q_discharge",
        propagate=True,
        **COMMON,
    )
    return hook(frame)


@pytest.mark.essential
def test_each_direction_carries_its_own_rows():
    frame = _frame(["C", "C", "D", "D"], [1.0, 2.0, 0.5, 1.5])

    out = _split_capacity(frame)

    assert out["q_charge"].to_list() == [1.0, 2.0, 2.0, 2.0]
    assert out["q_discharge"].to_list() == [0.0, 0.0, 0.5, 1.5]


@pytest.mark.essential
def test_a_direction_reads_zero_before_it_first_appears():
    """Legacy initialises the column to 0.0, not to the first value."""
    frame = _frame(["R", "R", "C"], [0.0, 0.0, 3.0])

    out = _split_capacity(frame)

    assert out["q_charge"].to_list() == [0.0, 0.0, 3.0]


@pytest.mark.essential
def test_propagate_is_not_a_forward_fill():
    """The quirk, pinned deliberately.

    A rest *between* two charge rows reads 0 — not the preceding charge value,
    which a forward fill would give. Legacy only backfills rows *after* the
    direction's last row in the cycle. Physically odd, but it is what 1.x
    produced, and the port must not change numbers. Changing this is a separate
    decision with a release note.

        Rec  State  Q      -> q_charge
        1    C      1.0       1.0   own row
        2    R      1.5       0.0   between charges: NOT 1.0
        3    C      2.0       2.0   own row
        4    R      2.5       2.0   after last charge (Rec 3): propagated
        5    D      0.5       2.0   after last charge: propagated
    """
    frame = _frame(["C", "R", "C", "R", "D"], [1.0, 1.5, 2.0, 2.5, 0.5])

    out = _split_capacity(frame)

    assert out["q_charge"].to_list() == [1.0, 0.0, 2.0, 2.0, 2.0]
    assert out["q_discharge"].to_list() == [0.0, 0.0, 0.0, 0.0, 0.5]


@pytest.mark.essential
def test_propagation_does_not_leak_across_cycles():
    """Propagation is per cycle — cycle 2 starts from zero again."""
    frame = _frame(
        ["C", "R", "D", "R"],
        [1.0, 1.0, 2.0, 2.0],
        cycles=[1, 1, 2, 2],
    )

    out = _split_capacity(frame)

    # Cycle 1 has no discharge; cycle 2 has no charge. Neither borrows.
    assert out["q_charge"].to_list() == [1.0, 1.0, 0.0, 0.0]
    assert out["q_discharge"].to_list() == [0.0, 0.0, 2.0, 2.0]


@pytest.mark.essential
def test_a_cycle_without_the_direction_is_all_zero_not_null():
    frame = _frame(["D", "D"], [1.0, 2.0])

    out = _split_capacity(frame)

    assert out["q_charge"].to_list() == [0.0, 0.0]
    assert out["q_charge"].null_count() == 0


@pytest.mark.essential
def test_combined_output_negates_discharge_and_zeroes_rest():
    """``split_current``: one column, charge positive, discharge negated.

    Rest rows become 0 — the legacy behaviour, and a real consequence: a
    resting cell's measured current is discarded rather than kept.
    """
    frame = _frame(["C", "D", "R"], [2.0, 3.0, 0.1])
    hook = state_splitter(
        base_column="Q",
        charge_output="I",
        discharge_output="I",
        n_charge=1.0,
        n_discharge=-1.0,
        propagate=False,
        **COMMON,
    )

    out = hook(frame)

    assert out["I"].to_list() == [2.0, -3.0, 0.0]


@pytest.mark.essential
def test_combined_output_does_not_propagate():
    frame = _frame(["C", "R", "R"], [2.0, 0.0, 0.0])
    hook = state_splitter(
        base_column="Q",
        charge_output="I",
        discharge_output="I",
        n_charge=1.0,
        n_discharge=-1.0,
        propagate=False,
        **COMMON,
    )

    out = hook(frame)

    assert out["I"].to_list() == [2.0, 0.0, 0.0]


@pytest.mark.essential
def test_a_missing_vendor_column_names_what_is_missing():
    frame = _frame(["C"], [1.0]).drop("State")

    with pytest.raises(LoaderError, match="State"):
        _split_capacity(frame)


@pytest.mark.essential
def test_the_hook_does_not_mutate_the_input_frame():
    frame = _frame(["C", "D"], [1.0, 2.0])
    before = frame.columns.copy()

    _split_capacity(frame)

    assert frame.columns == before


# -- cycle numbering (#560) ----------------------------------------------------


def _cycles(values):
    return pl.DataFrame({"Cyc": values})


@pytest.mark.essential
def test_zero_based_cycles_are_shifted_to_start_at_one():
    out = cycle_number_not_zero(cycle_column="Cyc")(_cycles([0, 0, 1, 2]))

    assert out["Cyc"].to_list() == [1, 1, 2, 3]


@pytest.mark.essential
def test_one_based_cycles_are_left_alone():
    out = cycle_number_not_zero(cycle_column="Cyc")(_cycles([1, 2, 3]))

    assert out["Cyc"].to_list() == [1, 2, 3]


@pytest.mark.essential
def test_cycles_starting_above_one_are_not_rebased():
    """The quirk: legacy shifts only when the minimum is exactly 0.

    A file whose cycles start at 2 keeps starting at 2 — it is not pulled down
    to 1. Reproduced rather than tidied, because tidying it would renumber
    someone's cycles.
    """
    out = cycle_number_not_zero(cycle_column="Cyc")(_cycles([2, 3, 4]))

    assert out["Cyc"].to_list() == [2, 3, 4]


@pytest.mark.essential
def test_a_non_numeric_cycle_column_raises_rather_than_doing_nothing():
    """Silence here would be an off-by-one with nothing to show for it."""
    frame = pl.DataFrame({"Cyc": ["0", "1"]})

    with pytest.raises(LoaderError, match="not numeric"):
        cycle_number_not_zero(cycle_column="Cyc")(frame)


@pytest.mark.essential
def test_a_missing_cycle_column_names_itself():
    with pytest.raises(LoaderError, match="Cyc"):
        cycle_number_not_zero(cycle_column="Cyc")(pl.DataFrame({"Other": [1]}))


@pytest.mark.essential
def test_an_empty_frame_is_returned_unchanged():
    frame = pl.DataFrame({"Cyc": []}, schema={"Cyc": pl.Int64})

    out = cycle_number_not_zero(cycle_column="Cyc")(frame)

    assert out.height == 0
