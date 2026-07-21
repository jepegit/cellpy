"""The shared normalization stage: vendor frame → harmonized native raw (#559).

Every loader used to do its own renaming, casting, timestamp conversion and
capacity fiddling. ``harmonize()`` does it once, for all of them, driven by the
loader's :class:`~cellpy.readers.instruments.declarations.LoaderDeclarations`::

    vendor file ──parse()──► vendor frame + declarations ──harmonize()──► native raw

The order of operations matters and is fixed here:

1. post hooks (vendor quirks, on vendor column names)
2. rename vendor → native, dropping undeclared columns
3. timestamps → ``epoch_time_utc`` int64 ns UTC
4. elapsed-time strings → float seconds (``duration_columns``)
5. cast to the schema dtypes
6. **reset-granularity normalization** to cycle-cumulative
7. identity and provenance stamping
8. ``validate_raw_frame``

Step 6 is the one to be careful about; see :func:`normalize_reset_granularity`.
Step 4 must precede step 5: the schema dtype for those columns is numeric, so
casting a duration string first would null the column outright — see
:func:`_cast_to_schema`, which now refuses to do that quietly.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any

import polars as pl
from cellpycore.cell_core import validate_raw_frame
from cellpycore.config import default_schema

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.declarations import LoaderDeclarations, ResetGranularity

_NS_PER_SECOND = 1_000_000_000


def normalize_reset_granularity(
    raw: pl.DataFrame,
    declarations: LoaderDeclarations,
) -> pl.DataFrame:
    """Convert cumulative columns to the harmonized-raw convention.

    The target (harmonized-raw spec, *Capacity convention*) is **cumulative per
    cycle, per direction**: within a cycle the value accumulates across that
    cycle's steps, and resets to 0 at each cycle boundary. The summary path
    depends on this — per-cycle capacity is read from the cycle's *last*
    datapoint — so a wrong granularity here corrupts every capacity downstream
    without raising anything.

    Conversions:

    ``PER_CYCLE``
        Already the target. Left untouched.
    ``PER_TEST``
        Never resets, so the whole history is baked in. Subtract the value the
        column held entering each cycle.
    ``PER_STEP``
        Resets each step, so within a cycle we must re-accumulate: add the
        running total of the *completed* steps of that cycle.

    Args:
        raw: frame already renamed to native columns.
        declarations: carries ``reset_granularity`` per column.

    Returns:
        A new frame; the input is not mutated.
    """
    schema = default_schema().raw
    cycle_column = schema.cycle_num

    if not declarations.reset_granularity:
        return raw
    if cycle_column not in raw.columns:
        raise LoaderError(
            f"reset-granularity normalization needs {cycle_column!r}, which the "
            f"loader did not produce; declare it in column_map."
        )

    out = raw
    for column, granularity in declarations.reset_granularity.items():
        if column not in out.columns:
            # Declared but absent: the file simply did not carry it.
            continue

        if granularity is ResetGranularity.PER_CYCLE:
            continue

        if granularity is ResetGranularity.PER_TEST:
            # Value entering the cycle = the column's first value in the cycle.
            # Subtracting it rebases each cycle to start at zero.
            out = out.with_columns(
                (pl.col(column) - pl.col(column).first().over(cycle_column)).alias(
                    column
                )
            )
            continue

        if granularity is ResetGranularity.PER_STEP:
            step_column = schema.step_num
            if step_column not in out.columns:
                raise LoaderError(
                    f"per-step reset granularity for {column!r} needs "
                    f"{step_column!r}; declare it in column_map."
                )
            # Within a cycle: each step contributes its own final value to the
            # steps that follow it. Take each step's last value, shift it down
            # the step sequence, and accumulate.
            step_totals = (
                out.group_by([cycle_column, step_column], maintain_order=True)
                .agg(pl.col(column).last().alias("_step_total"))
                .with_columns(
                    pl.col("_step_total")
                    .shift(1, fill_value=0.0)
                    .cum_sum()
                    .over(cycle_column)
                    .alias("_offset")
                )
                .drop("_step_total")
            )
            out = (
                out.join(step_totals, on=[cycle_column, step_column], how="left")
                .with_columns((pl.col(column) + pl.col("_offset")).alias(column))
                .drop("_offset")
            )
            continue

        raise LoaderError(f"unknown reset granularity {granularity!r} for {column!r}")

    return out


#: Excel serials count days from 1899-12-30 (the Lotus-1900 epoch Excel uses).
_EXCEL_EPOCH = datetime(1899, 12, 30, tzinfo=dt_timezone.utc)


def _parse_datetime_column(series: pl.Series, kind: str) -> pl.Series:
    """A vendor ``date_time`` column, in whatever form, → a polars ``Datetime``.

    Parsing is per *kind* because the forms are genuinely different and
    ``harmonize()`` cannot sniff them safely: ``"12/11/2020"`` is December to
    Maccor (US) but a serial-looking string elsewhere, and Arbin's ``42587.68``
    is Excel *days*, not epoch seconds. The loader states which it is.
    """
    if kind == "datetime":
        return series

    if kind == "string":
        # pandas.to_datetime, to match the legacy convert_date_time_to_datetime
        # exactly (same US-first interpretation of MM/DD/YYYY, same inference).
        import pandas as pd

        parsed = pd.to_datetime(series.to_pandas(), errors="coerce")
        return pl.from_pandas(parsed).cast(pl.Datetime("us"))

    if kind == "epoch_seconds":
        return (series.cast(pl.Float64) * _NS_PER_SECOND).cast(pl.Int64).cast(
            pl.Datetime("ns")
        )

    if kind == "excel_serial":
        # Serial days (may be fractional) from the Excel epoch. Done exactly as
        # the legacy ``xldate_as_datetime``: ``datetime(1899,12,30) +
        # timedelta(days=serial)``. Reproduced element-wise rather than
        # vectorised because ``timedelta``'s own microsecond rounding does not
        # match a ``round(serial * ...)`` in float — the two disagree by 1 µs on
        # about half the rows, which is a real parity miss on ``epoch_time_utc``.
        base = datetime(1899, 12, 30)

        def _from_serial(value: float | None):
            if value is None:
                return None
            return base + timedelta(days=float(value))

        return series.cast(pl.Float64).map_elements(
            _from_serial, return_dtype=pl.Datetime("us")
        )

    raise LoaderError(f"unknown datetime_kind {kind!r}")


def _derive_epoch_time_utc(
    raw: pl.DataFrame, declarations: LoaderDeclarations
) -> pl.DataFrame:
    """Parse the ``date_time`` passthrough and derive ``epoch_time_utc``.

    ``epoch_time_utc`` is a **required** native column, but no vendor writes it;
    it is derived from the absolute wall-clock timestamp the file *does* carry.
    A loader declares that column's form with ``datetime_kind``; here it becomes
    a proper polars ``Datetime`` (so the ``date_time`` passthrough kept for the
    one-release window is a real datetime, not a raw string), and a copy is
    placed in ``epoch_time_utc`` for :func:`_convert_timestamps` to turn into
    int64 ns UTC — so the naive-timezone rule lives in one place, not two.
    """
    schema = default_schema().raw
    kind = declarations.datetime_kind
    if kind is None:
        return raw

    # The passthrough keeps the legacy header name for the datetime column.
    from cellpy.parameters.internal_settings import get_headers_normal

    date_time = get_headers_normal().datetime_txt
    if date_time not in raw.columns:
        # Declared but this file did not carry it; nothing to derive from.
        return raw

    parsed = _parse_datetime_column(raw[date_time], kind)
    return raw.with_columns(
        parsed.alias(date_time),
        parsed.alias(schema.epoch_time_utc),
    )


def _convert_timestamps(
    raw: pl.DataFrame, declarations: LoaderDeclarations
) -> pl.DataFrame:
    """Vendor datetimes → ``epoch_time_utc`` as int64 nanoseconds UTC."""
    schema = default_schema().raw
    column = schema.epoch_time_utc
    if column not in raw.columns:
        return raw

    dtype = raw[column].dtype
    if dtype == pl.Int64:
        return raw

    if dtype == pl.Datetime:
        series = raw[column]
        if series.dtype.time_zone is None:
            if declarations.timezone is None:
                # Decision (2026-07-21, #560): a naive timestamp is read as
                # **UTC**, not the host's local zone. This matches
                # ``cellpycore.timestamps`` (the canonical-timestamp authority)
                # and keeps the result reproducible wherever analysis runs —
                # interpreting naive time as the *analysis* host's zone would
                # give the same file different absolute times on a lab laptop
                # and a CI runner. Still a warning, because it is an assumption
                # about someone else's data; silence a loader that knows better
                # by declaring ``timezone``.
                logging.warning(
                    "naive timestamps interpreted as UTC; declare a timezone in "
                    "the loader declarations if the cycler's local zone is known"
                )
                series = series.dt.replace_time_zone("UTC")
            else:
                series = series.dt.replace_time_zone(declarations.timezone)
        return raw.with_columns(
            series.dt.convert_time_zone("UTC").dt.epoch("ns").alias(column)
        )

    if dtype in (pl.Float64, pl.Float32):
        # Seconds since the epoch.
        return raw.with_columns(
            (pl.col(column) * _NS_PER_SECOND).cast(pl.Int64).alias(column)
        )

    raise LoaderError(
        f"cannot interpret {column!r} of dtype {dtype} as a timestamp; expected "
        f"a datetime, epoch seconds, or int64 epoch nanoseconds"
    )


#: ``[[D d] HH:]MM:SS[.frac]`` — the elapsed-time spellings vendors use.
_DURATION = re.compile(
    r"^\s*(?:(?P<days>\d+)\s*d\s+)?"
    r"(?:(?P<hours>\d+):)?"
    r"(?P<minutes>\d+):(?P<seconds>\d+(?:\.\d+)?)\s*$"
)


def _duration_to_seconds(value: str | None) -> float | None:
    match = _DURATION.match(str(value)) if value is not None else None
    if match is None:
        return None
    return (
        int(match["days"] or 0) * 86_400
        + int(match["hours"] or 0) * 3_600
        + int(match["minutes"]) * 60
        + float(match["seconds"])
    )


def _convert_durations(
    raw: pl.DataFrame, declarations: LoaderDeclarations
) -> pl.DataFrame:
    """Elapsed-time strings → float seconds.

    Matches the legacy ``pd.to_timedelta(...).dt.total_seconds()`` semantics.
    Only string columns are touched; a vendor that already writes seconds needs
    no declaration and is left alone.
    """
    columns = [
        column
        for column in declarations.duration_columns
        if column in raw.columns and raw[column].dtype == pl.String
    ]
    if not columns:
        return raw

    out = raw.with_columns(
        pl.col(column)
        .map_elements(_duration_to_seconds, return_dtype=pl.Float64)
        .alias(column)
        for column in columns
    )
    for column in columns:
        failed = out[column].null_count() - raw[column].null_count()
        if failed:
            raise LoaderError(
                f"{column!r} is declared as a duration column but {failed} of "
                f"{raw.height} values could not be parsed as an elapsed time "
                f"(examples: {raw[column].head(3).to_list()})"
            )
    return out


def _cast_to_schema(raw: pl.DataFrame) -> pl.DataFrame:
    """Cast every recognised column to its schema dtype.

    Casts are non-strict, because real vendor files carry the occasional junk
    row and the legacy path tolerated it (``pd.to_numeric(errors="coerce")``);
    making those fatal would refuse files 1.x loaded happily.

    But a cast that empties a column **completely** is not a stray value, it is
    the wrong dtype assumption, and that raises. Observed while porting #560:
    neware writes ``Time`` as ``"00:01:00"``, and casting that to the schema's
    Float64 nulled all 9065 rows without a word — the same silent-data-loss
    shape as #580. Partial losses warn, so they are visible without being
    fatal.
    """
    dtype_map = default_schema().raw.dtype_map()
    casts = [
        pl.col(name).cast(dtype, strict=False).alias(name)
        for name, dtype in dtype_map.items()
        if name in raw.columns
    ]
    if not casts:
        return raw

    out = raw.with_columns(casts)

    def _describe(name: str, lost: int) -> str:
        return (
            f"{name} ({lost}/{raw.height} values, {raw[name].dtype} -> "
            f"{dtype_map[name]})"
        )

    emptied, damaged = [], []
    for name in dtype_map:
        if name not in raw.columns:
            continue
        lost = out[name].null_count() - raw[name].null_count()
        if lost <= 0:
            continue
        had_data = raw[name].null_count() < raw.height
        if had_data and out[name].null_count() == raw.height:
            emptied.append(_describe(name, lost))
        else:
            damaged.append(_describe(name, lost))

    if damaged:
        logging.warning(
            "casting to the schema dtypes produced nulls: %s; the affected "
            "values could not be read as the native dtype",
            ", ".join(sorted(damaged)),
        )
    if emptied:
        raise LoaderError(
            f"casting to the schema dtypes emptied column(s) entirely: "
            f"{', '.join(sorted(emptied))}. The vendor column is not what the "
            f"native column expects - declare a conversion (e.g. "
            f"duration_columns) or fix the column_map target."
        )
    return out


def _stamp_identity(raw: pl.DataFrame, *, test_id: int) -> pl.DataFrame:
    """Fill the framework-owned identity columns."""
    schema = default_schema().raw
    additions = []
    if schema.test_id not in raw.columns:
        additions.append(pl.lit(test_id, dtype=pl.Int64).alias(schema.test_id))
    if schema.mask not in raw.columns:
        additions.append(pl.lit(True, dtype=pl.Boolean).alias(schema.mask))
    if schema.datapoint_num not in raw.columns:
        additions.append(
            pl.int_range(0, pl.len(), dtype=pl.Int64).alias(schema.datapoint_num)
        )
    return raw.with_columns(additions) if additions else raw


def harmonize(
    vendor_frame: Any,
    declarations: LoaderDeclarations,
    *,
    test_id: int = 0,
    strict: bool = True,
) -> pl.DataFrame:
    """Normalize a parsed vendor frame into harmonized native raw.

    Args:
        vendor_frame: what the loader's ``parse()`` produced — a polars frame,
            or a pandas frame (converted here, so legacy parsers can be reused
            unchanged during the port).
        declarations: the loader's declarations.
        test_id: identity for the rows of this test.
        strict: run ``validate_raw_frame`` strictly. The two sanctioned
            warn-only escape hatches (``local_instrument`` and friends,
            conventions plan §4) pass ``strict=False``.

    Returns:
        A polars frame in the harmonized-raw schema.

    Raises:
        LoaderError: if the frame cannot be normalized or fails validation.
    """
    if not isinstance(vendor_frame, pl.DataFrame):
        try:
            vendor_frame = pl.from_pandas(vendor_frame)
        except Exception as exc:
            raise LoaderError(
                f"parse() must return a polars or pandas frame, got "
                f"{type(vendor_frame).__name__}"
            ) from exc

    raw = vendor_frame
    for hook in declarations.post_hooks:
        raw = hook(raw)

    # Passthrough columns are renamed alongside the native ones; they simply
    # keep a name the schema does not own (see LoaderDeclarations.passthrough).
    mapping = {
        **declarations.column_map,
        **declarations.aux_map,
        **declarations.passthrough,
    }
    missing = [vendor for vendor in mapping if vendor not in raw.columns]
    if missing:
        logging.debug("declared vendor columns absent from this file: %s", missing)

    # Unknown vendor columns are warn + drop (#560 decision, 2026-07-20):
    # dropping keeps the harmonized frame on-spec, warning keeps it honest.
    # Columns in `declarations.dropped` are known-and-discarded, so they do
    # not warn (e.g. a state flag a post hook has already consumed).
    unrecognised = [
        column
        for column in raw.columns
        if column not in mapping and column not in declarations.dropped
    ]
    if unrecognised:
        logging.warning(
            "dropping vendor column(s) the loader does not recognise: %s "
            "(declare them - or list them in LoaderDeclarations.dropped if "
            "they are deliberate discards - to silence this)",
            unrecognised,
        )

    present = {vendor: native for vendor, native in mapping.items() if vendor in raw.columns}
    raw = raw.select(list(present)).rename(present)

    raw = _derive_epoch_time_utc(raw, declarations)
    raw = _convert_timestamps(raw, declarations)
    raw = _convert_durations(raw, declarations)
    raw = _cast_to_schema(raw)
    raw = normalize_reset_granularity(raw, declarations)
    raw = _stamp_identity(raw, test_id=test_id)

    try:
        validate_raw_frame(raw, default_schema().raw)
    except Exception as exc:
        if strict:
            raise LoaderError(f"harmonized frame failed validation: {exc}") from exc
        logging.warning("harmonized frame failed validation (warn-only): %s", exc)

    return raw


def stamp_provenance(
    test_meta: Any,
    *,
    source: Any,
    source_type: str,
    source_uuid: str | None = None,
) -> Any:
    """Fill the provenance fields a loader is not allowed to fill itself.

    The loader knows what the file *says*; only the framework knows where the
    file came from and when it was read (architecture plan §5.4).
    """
    from pathlib import Path

    path = Path(source)
    for name, value in (
        ("source_kind", "FILE"),
        ("source_type", source_type),
        ("source_uri", str(path)),
        ("source_uuid", source_uuid),
        ("raw_file_names", [path.name]),
        ("loaded_datetime", datetime.now(dt_timezone.utc)),
    ):
        if value is not None and hasattr(test_meta, name):
            setattr(test_meta, name, value)
    return test_meta
