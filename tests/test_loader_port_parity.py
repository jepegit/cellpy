"""Value parity between ``harmonize(parse(...))`` and the legacy path (#560).

``test_derived_declarations`` proves the derivation puts columns under the right
*names*. That is not enough to switch ingestion over: a wrong reset granularity
or an unparsed duration string produces a correctly-named column full of wrong
numbers, which no name check can see. This module compares the **values**.

How it works: one ``cellpy.get()`` per case, with ``query_file`` wrapped so the
same run yields both the vendor frame (what ``harmonize()`` would be handed) and
the legacy frame (the oracle). Deriving the declarations from the loader's live
``config_params`` means the test exercises the configuration that actually
shipped, not a transcription of it.

**The exception list is derived, not hardcoded.** Post-processors that
``harmonize()`` cannot yet express are listed in ``UNPORTED_POST_PROCESSORS``
together with the native columns they change; a case skips exactly those
columns, and only when its own configuration enables that post-processor. So
when a post hook lands, deleting its entry here tightens the test everywhere at
once — and no column is ever excused silently.
"""

from __future__ import annotations

import warnings

import polars as pl
import pytest

from cellpy.readers.instruments.base import AutoLoader, TxtLoader
from cellpy.readers.instruments.config_declarations import (
    declarations_from_configuration,
)
from cellpy.readers.instruments.harmonize import harmonize

#: instrument, source file, loader kwargs.
PARITY_CASES = (
    ("maccor_txt", "testdata/data/maccor_001.txt", {"model": "one", "sep": "\t"}),
    ("neware_txt", "testdata/data/neware_uio.csv", {"model": "one"}),
)

#: Legacy post-processor → native columns it changes, for the ones that have no
#: ``harmonize()`` equivalent yet. Each needs a vendor post hook (the #559 pilot
#: shows the shape for Maccor's capacity split). Remove an entry when its hook
#: lands; the parity assertions then cover those columns automatically.
UNPORTED_POST_PROCESSORS = {
    "split_capacity": (
        "cumulative_charge_capacity",
        "cumulative_discharge_capacity",
    ),
    "split_current": ("current",),
    "set_cycle_number_not_zero": ("cycle_num",),
}

#: ``date_time`` survives as a passthrough string while the native schema has no
#: column for it; the legacy path parses it to datetime. Tracked on the metadata
#: arc (#562/#563), not a capacity-corrupting difference.
KNOWN_REPRESENTATION_GAPS = ("date_time",)

TOLERANCE = 1e-6


@pytest.fixture
def captured_vendor_frame(monkeypatch):
    """Capture the vendor frame ``query_file`` produced during a load."""
    captured: dict = {}

    for cls in (AutoLoader, TxtLoader):
        original = cls.__dict__.get("query_file")
        if original is None:
            continue

        def wrapper(self, name, *args, _original=original, **kwargs):
            frame = _original(self, name, *args, **kwargs)
            captured["vendor"] = frame.copy()
            captured["config_params"] = self.config_params
            return frame

        monkeypatch.setattr(cls, "query_file", wrapper)

    return captured


def _numeric(series: pl.Series) -> pl.Series | None:
    """A comparable numeric view, so a change of *representation* is not read as
    a change of *value*.

    The legacy frame spells elapsed times as timedelta and timestamps as
    datetime; the native schema spells them float seconds and int64 epoch ns.
    """
    dtype = series.dtype
    if dtype.is_numeric():
        return series.cast(pl.Float64)
    if dtype == pl.Duration:
        return series.dt.total_nanoseconds().cast(pl.Float64) / 1e9
    if dtype == pl.Datetime:
        if dtype.time_zone is not None:
            series = series.dt.convert_time_zone("UTC")
        return series.dt.epoch("ns").cast(pl.Float64) / 1e9
    return None


def _excused(config_params) -> set[str]:
    """Columns this configuration's unported post-processors are allowed to move."""
    post_processors = getattr(config_params, "post_processors", None) or {}
    excused = set(KNOWN_REPRESENTATION_GAPS)
    for processor, columns in UNPORTED_POST_PROCESSORS.items():
        if post_processors.get(processor):
            excused.update(columns)
    return excused


def _harmonized_and_legacy(instrument, source, kwargs, captured):
    import cellpy

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cell = cellpy.get(
            source, instrument=instrument, mass=1.0, testing=True, **kwargs
        )

    assert "vendor" in captured, f"query_file was never called for {instrument}"
    declarations = declarations_from_configuration(captured["config_params"])
    harmonized = harmonize(captured["vendor"], declarations, strict=False)
    legacy = pl.from_pandas(cell.data.raw.reset_index(drop=True))
    return harmonized, legacy, captured["config_params"]


@pytest.mark.essential
@pytest.mark.parametrize("instrument, source, kwargs", PARITY_CASES)
def test_harmonized_values_match_the_legacy_frame(
    instrument, source, kwargs, captured_vendor_frame
):
    """Every shared column agrees in value, bar the named exceptions.

    This is the assertion the flag day rests on. A failure here means routing
    ``load()`` through ``harmonize()`` would change users' numbers.
    """
    harmonized, legacy, config_params = _harmonized_and_legacy(
        instrument, source, kwargs, captured_vendor_frame
    )
    excused = _excused(config_params)

    shared = [c for c in harmonized.columns if c in legacy.columns]
    assert shared, f"{instrument}: harmonize produced no column the legacy path has"

    checked, mismatched = [], []
    for column in shared:
        if column in excused:
            continue
        left, right = harmonized[column], legacy[column]
        assert left.len() == right.len(), (
            f"{instrument}: {column} has {left.len()} rows, legacy has {right.len()}"
        )
        left_n, right_n = _numeric(left), _numeric(right)
        if left_n is None or right_n is None:
            assert (left == right).all(), f"{instrument}: {column} differs"
            checked.append(column)
            continue
        worst = (left_n - right_n).abs().max()
        if worst is None or worst > TOLERANCE:
            mismatched.append(f"{column} (max abs diff {worst})")
        checked.append(column)

    assert not mismatched, (
        f"{instrument}: harmonize() disagrees with the legacy path on "
        f"{mismatched}. Either the derived declarations are wrong, or this is a "
        f"deliberate change that belongs in the release notes."
    )
    assert checked, f"{instrument}: every shared column was excused - test is vacuous"


@pytest.mark.essential
@pytest.mark.parametrize("instrument, source, kwargs", PARITY_CASES)
def test_no_column_is_silently_emptied(
    instrument, source, kwargs, captured_vendor_frame
):
    """No harmonized column is all-null when the legacy path filled it.

    The failure this guards against is specific and was real: neware writes
    ``Time`` as ``"00:01:00"``, and casting a string column to the schema's
    Float64 nulled all 9065 rows without raising. Same shape as #580 — the data
    is gone and nothing says so.
    """
    harmonized, legacy, _ = _harmonized_and_legacy(
        instrument, source, kwargs, captured_vendor_frame
    )
    emptied = [
        column
        for column in harmonized.columns
        if column in legacy.columns
        and harmonized[column].null_count() == harmonized.height
        and legacy[column].null_count() < legacy.height
    ]
    assert not emptied, (
        f"{instrument}: {emptied} came out entirely null while the legacy path "
        f"populated them"
    )


@pytest.mark.essential
@pytest.mark.parametrize("instrument, source, kwargs", PARITY_CASES)
def test_elapsed_times_are_seconds_not_nulls(
    instrument, source, kwargs, captured_vendor_frame
):
    """``test_time``/``step_time`` arrive as real float seconds.

    Pinned separately from the parity sweep because both vendors write these as
    duration strings, and the schema dtype is numeric — the combination that
    produced the silent null column.
    """
    harmonized, _, _ = _harmonized_and_legacy(
        instrument, source, kwargs, captured_vendor_frame
    )
    for column in ("test_time", "step_time"):
        if column not in harmonized.columns:
            continue
        series = harmonized[column]
        assert series.dtype.is_numeric(), f"{column} is {series.dtype}, not numeric"
        assert series.null_count() < series.len(), f"{column} is entirely null"
        assert series.max() > 0, f"{column} never advances"
