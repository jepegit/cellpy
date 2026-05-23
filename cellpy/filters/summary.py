"""Generic row-filtering for cellpy summary DataFrames.

This module operates on plain pandas DataFrames so it can be reused by
plotters, exporters, and batch tools. It complements the cycle-based
:func:`cellpy.filters.cycles.filter_cycles` and the legacy summary helpers
in :mod:`cellpy.utils.helpers` (``remove_first_cycles_from_summary``,
``remove_last_cycles_from_summary``, ``remove_outliers_from_summary_*``,
``yank_before``, ``yank_after``).

The public entry point is :func:`filter_summary`. Filters are exposed
through a small registry (``_RANGE_FILTERS``) so additional value-range
filters (capacity, temperature, ...) can be added without changing the
public signature.

Range semantics
---------------

Both range forms use **exclusive lower / inclusive upper** bounds so the
two forms behave consistently:

- ``(low, high)`` -> keep rows where ``low < value <= high``.
- ``{"value": v, "delta": d}`` -> keep rows where ``v - d < value <= v + d``.
- ``None`` -> no filter applied.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Callable, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

RangeArg = Optional[Union[tuple, list, Mapping[str, float]]]
ColumnsArg = Union[str, Sequence[str]]


def _coerce_columns(columns: ColumnsArg) -> tuple[str, ...]:
    """Accept either a string or a sequence of strings; return a tuple."""
    if isinstance(columns, str):
        return (columns,)
    return tuple(columns)


def _range_bounds(range_arg: RangeArg) -> Optional[tuple[float, float]]:
    """Normalize a range argument to ``(low, high)`` with exclusive lower /
    inclusive upper semantics, or ``None`` if no filter should be applied.

    Raises:
        TypeError: if ``range_arg`` is neither None, a 2-element sequence,
            nor a mapping with ``value``/``delta``.
        ValueError: if the resulting low >= high.
    """
    if range_arg is None:
        return None

    if isinstance(range_arg, Mapping):
        missing = {"value", "delta"} - set(range_arg)
        if missing:
            msg = (
                f"range mapping must contain 'value' and 'delta', "
                f"missing: {sorted(missing)}"
            )
            raise ValueError(msg)
        v = float(range_arg["value"])
        d = float(range_arg["delta"])
        if d < 0:
            raise ValueError(f"delta must be non-negative, got {d}")
        low, high = v - d, v + d
    elif isinstance(range_arg, (tuple, list)) and len(range_arg) == 2:
        low, high = float(range_arg[0]), float(range_arg[1])
    else:
        msg = (
            f"range must be None, a 2-element (low, high) tuple/list, or a "
            f"mapping with 'value'/'delta'; got {type(range_arg).__name__}"
        )
        raise TypeError(msg)

    if low >= high:
        raise ValueError(
            f"range lower bound ({low}) must be < upper bound ({high})"
        )
    return low, high


def _apply_range_filter(
    df: pd.DataFrame,
    columns: tuple[str, ...],
    bounds: tuple[float, float],
) -> pd.Series:
    """Return a boolean mask: row is kept iff *every* listed column lies
    inside ``bounds`` (AND across columns). Missing columns raise
    ``KeyError`` so misconfiguration fails loudly."""
    low, high = bounds
    missing = [c for c in columns if c not in df.columns]
    if missing:
        msg = (
            f"filter_summary: missing column(s) {missing} "
            f"(available: {list(df.columns)[:8]}...)."
        )
        raise KeyError(msg)

    mask = pd.Series(True, index=df.index)
    for col in columns:
        col_vals = df[col]
        mask &= (col_vals > low) & (col_vals <= high)
    return mask


_FilterFn = Callable[[pd.DataFrame, Any, Any], pd.Series]


def _rate_filter(
    df: pd.DataFrame,
    range_arg: RangeArg,
    columns: ColumnsArg,
) -> pd.Series:
    bounds = _range_bounds(range_arg)
    if bounds is None:
        return pd.Series(True, index=df.index)
    cols = _coerce_columns(columns)
    return _apply_range_filter(df, cols, bounds)


_RANGE_FILTERS: dict[str, _FilterFn] = {
    "rate": _rate_filter,
}


def register_range_filter(name: str, fn: _FilterFn) -> None:
    """Register a new range-style filter on the module-level registry.

    A range filter has the signature ``fn(df, range_arg, columns) -> mask``.
    Useful for project-specific extensions (capacity windows, temperature
    windows, ...) without modifying this module.
    """
    if name in _RANGE_FILTERS:
        logger.warning("filter_summary: overwriting registered filter %r", name)
    _RANGE_FILTERS[name] = fn


def filter_summary(
    df: pd.DataFrame,
    *,
    rate: RangeArg = None,
    rate_columns: ColumnsArg = ("charge_c_rate", "discharge_c_rate"),
    **extra_filters: Any,
) -> pd.DataFrame:
    """Filter rows of a cellpy summary DataFrame.

    Args:
        df: The summary DataFrame. Filtered columns must be present;
            missing columns raise ``KeyError``.
        rate: Range filter applied to the configured ``rate_columns``.
            Accepts ``None`` (no filter), a 2-element ``(low, high)``
            tuple/list (keep rows with ``low < value <= high``), or a
            mapping ``{"value": v, "delta": d}`` (keep rows with
            ``v - d < value <= v + d``).
        rate_columns: Which column(s) the ``rate`` filter applies to.
            A single string is coerced to a one-element tuple. With more
            than one column the predicate is AND-ed across columns - a
            row is kept only if *every* listed column lies in range.
        **extra_filters: Reserved for additional range filters
            registered via :func:`register_range_filter`. Unknown filter
            names raise ``ValueError`` so typos fail loudly.

    Returns:
        A new DataFrame (copy) containing only the matching rows. The
        original index is preserved.

    Raises:
        KeyError: A filtered column is missing from ``df``.
        ValueError: An unknown filter name was passed, or a range
            argument is malformed.
        TypeError: A range argument has an unsupported type.
    """
    range_kwargs = {k: v for k, v in extra_filters.items() if not k.endswith("_columns")}
    column_kwargs = {k: v for k, v in extra_filters.items() if k.endswith("_columns")}

    unknown = set(range_kwargs) - set(_RANGE_FILTERS)
    if unknown:
        msg = (
            f"filter_summary: unknown filter name(s) {sorted(unknown)} "
            f"(known: {sorted(_RANGE_FILTERS)}). Use register_range_filter "
            f"to add new filters."
        )
        raise ValueError(msg)
    orphan_cols = {
        k for k in column_kwargs if k[: -len("_columns")] not in _RANGE_FILTERS
    }
    if orphan_cols:
        msg = (
            f"filter_summary: column override(s) {sorted(orphan_cols)} have no "
            f"matching registered filter."
        )
        raise ValueError(msg)

    if rate is None and not any(v is not None for v in range_kwargs.values()):
        return df.copy()

    mask = pd.Series(True, index=df.index)

    if rate is not None:
        mask &= _RANGE_FILTERS["rate"](df, rate, rate_columns)
        logger.debug(
            "filter_summary: rate filter applied to columns %s", rate_columns
        )

    for name, range_arg in range_kwargs.items():
        if range_arg is None:
            continue
        cols = column_kwargs.get(f"{name}_columns", (name,))
        mask &= _RANGE_FILTERS[name](df, range_arg, cols)
        logger.debug("filter_summary: %s filter applied to columns %s", name, cols)

    return df.loc[mask].copy()
