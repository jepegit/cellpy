"""Value parity between ``harmonize(parse(...))`` and the legacy path (#560).

``test_derived_declarations`` proves the derivation puts columns under the right
*names*. That is not enough to switch ingestion over: a wrong reset granularity
or an unparsed duration string produces a correctly-named column full of wrong
numbers, which no name check can see. This module compares the **values**.

How it works: each case is loaded twice — once through the two-stage entry
points (``parse()`` then ``declarations()``, fed to ``harmonize()``) and once
through ``cellpy.get()`` for the legacy frame that acts as the oracle. Because
``declarations()`` derives from the loader's live ``config_params`` after
parsing, the test exercises the configuration that actually shipped, and picks
up per-file corrections such as neware's units.

``tests/test_loader_two_stage.py`` checks that ``parse()`` agrees with what
``loader()`` parses, which is what stops this module from verifying a path
nothing uses.

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

from cellpy.readers.instruments.harmonize import harmonize

#: instrument, source file, loader kwargs.
PARITY_CASES = (
    ("maccor_txt", "testdata/data/maccor_001.txt", {"model": "one", "sep": "\t"}),
    ("neware_txt", "testdata/data/neware_uio.csv", {"model": "one"}),
    # Model two brings `remove_last_if_bad` into range — the only shipped
    # post-processor that changes the *row count*. maccor_002.txt was already in
    # testdata but no test loaded it.
    ("maccor_txt", "testdata/data/maccor_002.txt", {"model": "two"}),
    # `custom` needs no port: its configuration arrives from the user's YAML
    # instrument file at runtime, and the derivation reads a ModelParameters
    # instance as happily as a module. Covered here so that stays true.
    (
        "custom",
        "testdata/data/custom_data_001.csv",
        {"instrument_file": "testdata/data/custom_instrument_001.yml"},
    ),
    # pec_csv is not configuration-driven; its parse()/declarations() are
    # hand-written (canonical rename in parse, static column map). Plan §2.6a.
    ("pec_csv", "testdata/data/pec.csv", {}),
)

#: Legacy post-processor → native columns it changes, for the ones that have no
#: ``harmonize()`` equivalent yet. Each needs a vendor post hook (the #559 pilot
#: shows the shape for Maccor's capacity split). Remove an entry when its hook
#: lands; the parity assertions then cover those columns automatically.
UNPORTED_POST_PROCESSORS: dict[str, tuple[str, ...]] = {}

#: ``date_time`` survives as a passthrough string while the native schema has no
#: column for it; the legacy path parses it to datetime. Tracked on the metadata
#: arc (#562/#563), not a capacity-corrupting difference.
KNOWN_REPRESENTATION_GAPS = ("date_time",)

TOLERANCE = 1e-6


#: kwargs that belong to loader *construction* rather than to parsing.
_CREATE_KWARGS = ("model", "instrument_file")


def _parse_with_a_loader(instrument, source, kwargs):
    """Drive the vendor stage through the public two-stage entry points.

    This used to wrap ``query_file`` so one ``cellpy.get()`` yielded both
    frames. That worked until ``custom`` joined the cases: the registry imports
    loader modules under their **bare** name, so the class it instantiates
    (``custom.DataLoader``) is a *different class object* from
    ``cellpy.readers.instruments.custom.DataLoader``, and patching the latter
    silently did nothing — the capture came back empty rather than wrong.

    ``parse()``/``declarations()`` need no patching, do not depend on import
    order, and exercise the entry points the switchover will actually use.
    """
    from cellpy.readers import data_structures as ds

    create = {k: v for k, v in kwargs.items() if k in _CREATE_KWARGS}
    parse = {k: v for k, v in kwargs.items() if k != "instrument_file"}

    loader = ds.generate_default_factory().create(instrument, **create)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vendor = loader.parse(source, **parse)
    # config_params only exists on configuration-driven loaders; pec_csv has
    # none, and only the post-processor excusal (_excused) reads it.
    return vendor, loader.declarations(), getattr(loader, "config_params", None)


def _numeric(series: pl.Series) -> pl.Series | None:
    """A comparable numeric view, so a change of *representation* is not read as
    a change of *value*.

    The legacy frame spells elapsed times as timedelta, timestamps as datetime,
    and — for columns it never converted — numbers as **strings**: maccor model
    two leaves ``cumulative_charge_energy`` as ``'0.00000000'``. The native
    schema spells all of those numerically.

    A numeric-looking string column is coerced so the *values* can be compared.
    A string column that does not fully coerce returns ``None``, so the caller
    falls back to strict equality and reports the difference rather than
    papering over it.
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
    if dtype == pl.String:
        coerced = series.cast(pl.Float64, strict=False)
        if coerced.null_count() == series.null_count():
            return coerced
    return None


def _excused(config_params) -> set[str]:
    """Columns this configuration's unported post-processors are allowed to move."""
    post_processors = getattr(config_params, "post_processors", None) or {}
    excused = set(KNOWN_REPRESENTATION_GAPS)
    for processor, columns in UNPORTED_POST_PROCESSORS.items():
        if post_processors.get(processor):
            excused.update(columns)
    return excused


def _harmonized_and_legacy(instrument, source, kwargs):
    import cellpy

    vendor, declarations, config_params = _parse_with_a_loader(
        instrument, source, kwargs
    )
    harmonized = harmonize(vendor, declarations, strict=False)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cell = cellpy.get(
            source, instrument=instrument, mass=1.0, testing=True, **kwargs
        )
    legacy = pl.from_pandas(cell.data.raw.reset_index(drop=True))
    return harmonized, legacy, config_params


@pytest.mark.essential
@pytest.mark.parametrize("instrument, source, kwargs", PARITY_CASES)
def test_harmonized_values_match_the_legacy_frame(
    instrument, source, kwargs
):
    """Every shared column agrees in value, bar the named exceptions.

    This is the assertion the flag day rests on. A failure here means routing
    ``load()`` through ``harmonize()`` would change users' numbers.
    """
    harmonized, legacy, config_params = _harmonized_and_legacy(
        instrument, source, kwargs
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
            if left.dtype != right.dtype:
                mismatched.append(
                    f"{column} (not comparable: {right.dtype} -> {left.dtype})"
                )
            elif not (left == right).all():
                mismatched.append(f"{column} (values differ)")
            checked.append(column)
            continue
        # Compare the null masks first: a difference in *which* rows are
        # populated is a real disagreement that the numeric diff would hide,
        # because subtraction yields null wherever either side is null. A
        # column that is all-null on both sides (pec carries several — sparse
        # per-measurement columns) then agrees, rather than reading as a
        # spurious ``max abs diff None``.
        if not (left_n.is_null() == right_n.is_null()).all():
            mismatched.append(f"{column} (different null positions)")
            checked.append(column)
            continue
        worst = (left_n - right_n).abs().max()
        if worst is not None and worst > TOLERANCE:
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
    instrument, source, kwargs
):
    """No harmonized column is all-null when the legacy path filled it.

    The failure this guards against is specific and was real: neware writes
    ``Time`` as ``"00:01:00"``, and casting a string column to the schema's
    Float64 nulled all 9065 rows without raising. Same shape as #580 — the data
    is gone and nothing says so.
    """
    harmonized, legacy, _ = _harmonized_and_legacy(
        instrument, source, kwargs
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
    instrument, source, kwargs
):
    """``test_time``/``step_time`` arrive as real float seconds.

    Pinned separately from the parity sweep because both vendors write these as
    duration strings, and the schema dtype is numeric — the combination that
    produced the silent null column.
    """
    harmonized, _, _ = _harmonized_and_legacy(
        instrument, source, kwargs
    )
    for column in ("test_time", "step_time"):
        if column not in harmonized.columns:
            continue
        series = harmonized[column]
        assert series.dtype.is_numeric(), f"{column} is {series.dtype}, not numeric"
        assert series.null_count() < series.len(), f"{column} is entirely null"
        assert series.max() > 0, f"{column} never advances"
