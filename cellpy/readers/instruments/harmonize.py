"""The shared normalization stage: vendor frame → harmonized native raw (#559).

Every loader used to do its own renaming, casting, timestamp conversion and
capacity fiddling. ``harmonize()`` does it once, for all of them, driven by the
loader's :class:`~cellpy.readers.instruments.declarations.LoaderDeclarations`::

    vendor file ──parse()──► vendor frame + declarations ──harmonize()──► native raw

The order of operations matters and is fixed here:

1. post hooks (vendor quirks, on vendor column names)
2. rename vendor → native, dropping undeclared columns
3. timestamps → ``epoch_time_utc`` int64 ns UTC
4. cast to the schema dtypes
5. **reset-granularity normalization** to cycle-cumulative
6. identity and provenance stamping
7. ``validate_raw_frame``

Step 5 is the one to be careful about; see :func:`normalize_reset_granularity`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_timezone
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
                # The shared D3 rule: naive means local. Say so, because it is
                # an assumption about someone else's data.
                logging.warning(
                    "naive timestamps interpreted as local time; declare a "
                    "timezone in the loader declarations to be explicit"
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


def _cast_to_schema(raw: pl.DataFrame) -> pl.DataFrame:
    """Cast every recognised column to its schema dtype."""
    dtype_map = default_schema().raw.dtype_map()
    casts = [
        pl.col(name).cast(dtype, strict=False).alias(name)
        for name, dtype in dtype_map.items()
        if name in raw.columns
    ]
    return raw.with_columns(casts) if casts else raw


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

    mapping = {**declarations.column_map, **declarations.aux_map}
    missing = [vendor for vendor in mapping if vendor not in raw.columns]
    if missing:
        logging.debug("declared vendor columns absent from this file: %s", missing)

    present = {vendor: native for vendor, native in mapping.items() if vendor in raw.columns}
    raw = raw.select(list(present)).rename(present)

    raw = _convert_timestamps(raw, declarations)
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
