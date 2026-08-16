"""Per-cell summary operations for the collect pipeline.

Polars-native ports of the meaty ``helpers.concat_summaries`` internals --
rate-based cycle selection, CV partitioning, and group averaging -- that
previously lived as pandas helpers keyed off the deprecated ``headers_summary``
/ ``headers_step_table`` singletons. These use the cell's own ``schema`` (the
2.1 native accessor) and operate on the tidy long frame produced by
:mod:`cellpy.batch.aggregate`.
"""

from __future__ import annotations

from typing import Any

import polars as pl

CYCLE = "cycle_num"
_NORM_CYCLE_OUT = "equivalent_cycle"


def schema_name(cell: Any, table: str, attr: str, default: str) -> str:
    """Resolve a column name from ``cell.schema.<table>.<attr>`` (native, 2.1).

    Falls back to ``default`` when the schema (or attribute) is unavailable so
    the pipeline still works on light-weight/fake cells in tests.
    """
    schema = getattr(cell, "schema", None)
    tbl = getattr(schema, table, None) if schema is not None else None
    return getattr(tbl, attr, default) or default


def to_polars(frame: Any) -> pl.DataFrame | None:
    """Best-effort conversion of a cell frame (pandas or polars) to polars."""
    if frame is None:
        return None
    if isinstance(frame, pl.DataFrame):
        return frame
    try:
        return pl.from_pandas(frame)
    except (TypeError, ValueError):
        return None


def rate_cycles(cell: Any, opts: Any) -> list[int]:
    """Cycle numbers whose ``rate_on`` step ran at ``opts.rate`` (± tolerance).

    Port of ``helpers.select_summary_based_on_rate`` -- the step-table mask --
    returning just the surviving cycle numbers (the summary filtering happens
    in :func:`extract_cell_summary`). ``rate_inverse`` negates the *step* mask;
    the caller handles ``rate_inverted`` (negating the *cycle* selection).
    """
    steps = to_polars(getattr(getattr(cell, "data", None), "steps", None))
    if steps is None or steps.height == 0:
        return []

    rate_col = opts.rate_column or schema_name(cell, "steps", "c_rate", "c_rate")
    type_col = schema_name(cell, "steps", "step_type", "step_type")
    cyc_col = schema_name(cell, "steps", "cycle_num", CYCLE)
    if rate_col not in steps.columns or cyc_col not in steps.columns:
        return []

    rate = opts.rate
    std = opts.rate_std if opts.rate_std is not None else 0.1 * rate

    on = opts.rate_on if opts.rate_on is not None else ("charge",)
    if isinstance(on, str):
        on = (on,)

    mask = (pl.col(rate_col) < (rate + std)) & (pl.col(rate_col) > (rate - std))
    if on and type_col in steps.columns:
        mask = mask & pl.col(type_col).cast(pl.Utf8).is_in(list(on))
    if opts.rate_inverse:
        mask = ~mask

    return steps.filter(mask)[cyc_col].unique().to_list()


def cv_partition(cell: Any) -> pl.DataFrame | None:
    """Split each numeric summary metric into ``*_non_cv`` / ``*_cv`` parts.

    ``*_non_cv`` comes from ``make_summary(exclude_step_types=["cv_"])``; ``*_cv``
    is ``full - non_cv`` clipped at zero (the CV-step contribution). Mirrors
    ``helpers._partition_summary_based_on_cv_steps`` but polars-native and keyed
    on the schema cycle column. Returns the full summary unchanged if the
    engine cannot produce a no-CV variant.
    """
    cyc = schema_name(cell, "summary", "cycle_num", CYCLE)
    full = to_polars(getattr(getattr(cell, "data", None), "summary", None))
    if full is None or full.height == 0 or cyc not in full.columns:
        return full

    try:
        no_cv = to_polars(
            cell.make_summary(exclude_step_types=["cv_"], create_copy=True).data.summary
        )
    except (TypeError, ValueError, AttributeError):
        return full
    if no_cv is None or cyc not in no_cv.columns:
        return full

    numeric = [
        c
        for c, dt in zip(full.columns, full.dtypes)
        if dt.is_numeric() and c != cyc and c in no_cv.columns
    ]
    if not numeric:
        return full

    renamed = no_cv.select([cyc, *numeric]).rename({c: f"{c}__nocv" for c in numeric})
    joined = full.join(renamed, on=cyc, how="left")

    additions: list[pl.Expr] = []
    for c in numeric:
        additions.append(pl.col(f"{c}__nocv").alias(f"{c}_non_cv"))
        additions.append(
            (pl.col(c) - pl.col(f"{c}__nocv")).clip(lower_bound=0).alias(f"{c}_cv")
        )
    return joined.with_columns(additions).drop([f"{c}__nocv" for c in numeric])


def extract_cell_summary(cell: Any, opts: Any) -> pl.DataFrame | None:
    """Per-cell summary frame with cycle-level options applied.

    Applies (in legacy order) CV partition, max-cycle drop, rate selection and
    ``remove_last``, then normalizes the cycle column to ``cycle_num`` and, when
    requested, exposes the normalized cycle index as ``equivalent_cycle``.
    """
    cyc = schema_name(cell, "summary", "cycle_num", CYCLE)

    if opts.partition_by_cv:
        frame = cv_partition(cell)
    else:
        frame = to_polars(getattr(getattr(cell, "data", None), "summary", None))
    if frame is None or frame.height == 0:
        return None

    if opts.max_cycle is not None and cyc in frame.columns:
        frame = frame.filter(pl.col(cyc) <= opts.max_cycle)

    if opts.rate is not None and cyc in frame.columns:
        allowed = rate_cycles(cell, opts)
        if opts.rate_inverted:
            frame = frame.filter(~pl.col(cyc).is_in(allowed))
        else:
            frame = frame.filter(pl.col(cyc).is_in(allowed))

    if opts.remove_last and frame.height > 0:
        frame = frame.head(frame.height - 1)

    if cyc != CYCLE and cyc in frame.columns:
        frame = frame.rename({cyc: CYCLE})

    if opts.normalize_cycles:
        norm = schema_name(cell, "summary", "normalized_cycle_index", "")
        if norm and norm in frame.columns:
            frame = frame.rename({norm: _NORM_CYCLE_OUT})

    return frame


def resolve_group_labels(
    frame: pl.DataFrame, group_labels: dict[Any, Any] | None
) -> dict[Any, Any] | None:
    """Key *group_labels* by the group values actually present in *frame*.

    Journal group ids are integers while a hand-written
    ``custom_group_labels={1: "first"}`` may arrive with either integer or
    string keys (JSON round-trips, spreadsheet imports). Matching on the raw
    key alone silently dropped those labels (#923), so look each present group
    up by value *and* by its string form.
    """
    if not group_labels or "group" not in frame.columns:
        return None
    lookup: dict[Any, Any] = {}
    for key, value in group_labels.items():
        if value is None:
            continue
        lookup.setdefault(key, value)
        lookup.setdefault(str(key), value)
    resolved: dict[Any, Any] = {}
    for group in frame["group"].unique().to_list():
        if group is None:
            continue
        if group in lookup:
            resolved[group] = lookup[group]
        elif str(group) in lookup:
            resolved[group] = lookup[str(group)]
    return resolved or None


def _with_group_label(
    out: pl.DataFrame, frame: pl.DataFrame, group_labels: dict[Any, Any] | None
) -> pl.DataFrame:
    """Add a ``group_label`` column from *group_labels* (no-op when unmapped)."""
    mapping = resolve_group_labels(frame, group_labels)
    if not mapping:
        return out
    return out.with_columns(
        pl.col("group")
        .replace_strict(
            {key: str(value) for key, value in mapping.items()},
            default=None,
            return_dtype=pl.Utf8,
        )
        .alias("group_label")
    )


def _numeric_value_columns(frame: pl.DataFrame, keys: tuple[str, ...]) -> list[str]:
    return [
        c
        for c, dt in zip(frame.columns, frame.dtypes)
        if dt.is_numeric() and c not in keys
    ]


def clean_extremes(
    frame: pl.DataFrame,
    columns: list[str],
    *,
    replace_inf: bool,
    replace_extremes: bool,
    low: float,
    high: float,
) -> pl.DataFrame:
    """Null out inf and out-of-range values in the given numeric columns."""
    if not columns:
        return frame
    exprs: list[pl.Expr] = []
    for c in columns:
        expr = pl.col(c)
        if replace_inf:
            expr = pl.when(expr.is_infinite()).then(None).otherwise(expr)
        if replace_extremes:
            expr = (
                pl.when((expr < low) | (expr > high)).then(None).otherwise(expr)
            )
        exprs.append(expr.alias(c))
    return frame.with_columns(exprs)


def group_average(
    frame: pl.DataFrame,
    opts: Any,
    *,
    keys: tuple[str, ...],
    group_labels: dict[Any, Any] | None = None,
) -> pl.DataFrame:
    """Average per journal group -> tidy long ``(group, cycle_num, variable, mean, std)``.

    Port of ``helpers._make_average`` + ``collect_frames`` grouping path. The
    aggregate column is named ``mean`` regardless of ``average_method`` (legacy
    backward-compat). ``std`` is the per-group standard deviation across cells.
    """
    if frame.height == 0 or "group" not in frame.columns:
        return frame

    id_cols = ["group"] + ([CYCLE] if CYCLE in frame.columns else [])
    value_cols = _numeric_value_columns(frame, keys)
    if not value_cols:
        return frame

    long = frame.unpivot(
        index=id_cols, on=value_cols, variable_name="variable", value_name="_v"
    )
    stat = "median" if opts.average_method == "median" else "mean"
    agg_expr = (
        pl.col("_v").median() if stat == "median" else pl.col("_v").mean()
    ).alias("mean")
    out = long.group_by([*id_cols, "variable"]).agg(
        agg_expr, pl.col("_v").std().alias("std")
    )

    out = _with_group_label(out, frame, group_labels)

    sort_cols = [c for c in ("group", CYCLE, "variable") if c in out.columns]
    return out.sort(sort_cols)


def singletons_as_long(
    frame: pl.DataFrame,
    *,
    keys: tuple[str, ...],
    group_labels: dict[Any, Any] | None = None,
) -> pl.DataFrame:
    """Unpivot singleton-group rows into the ``group_average`` long schema.

    ``mean`` is the cell value; ``std`` is null (no peers to spread). Used when
    ``group_it=True`` mixes multi-member and singleton groups (#816).
    """
    if frame.height == 0 or "group" not in frame.columns:
        return frame

    id_cols = ["group"] + ([CYCLE] if CYCLE in frame.columns else [])
    value_cols = _numeric_value_columns(frame, keys)
    if not value_cols:
        return frame

    out = frame.unpivot(
        index=id_cols, on=value_cols, variable_name="variable", value_name="mean"
    ).with_columns(pl.lit(None).cast(pl.Float64).alias("std"))

    out = _with_group_label(out, frame, group_labels)

    sort_cols = [c for c in ("group", CYCLE, "variable") if c in out.columns]
    return out.sort(sort_cols)
