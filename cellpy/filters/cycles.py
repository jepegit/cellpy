"""Cycle-based row filtering for cellpy raw / summary DataFrames.

This module is intentionally generic: it operates on a pandas DataFrame
plus a column name, so any exporter, plotter, or batch tool that needs
to subset by cycle can reuse it.

The default column resolves to ``HeadersNormal.cycle_index_txt`` (i.e.
``"cycle_index"``) when the caller does not provide one explicitly,
matching the column produced by the cellpy raw-data reader.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Optional, Union

import pandas as pd

from cellpy.parameters.internal_settings import get_headers_normal

logger = logging.getLogger(__name__)

CyclesArg = Optional[Union[int, Iterable[int]]]


def filter_cycles(
    df: pd.DataFrame,
    cycles: CyclesArg = None,
    last_cycle: Optional[int] = None,
    column: Optional[str] = None,
) -> pd.DataFrame:
    """Return rows of ``df`` matching the cycle filter.

    Args:
        df: The DataFrame to filter. Must contain ``column``.
        cycles: ``None`` keeps every cycle; an ``int`` keeps that single
            cycle; any iterable of ints keeps the listed cycles.
        last_cycle: When given, drop rows whose cycle number is greater
            than ``last_cycle``. Combines with ``cycles``: only rows that
            satisfy both constraints are kept.
        column: Name of the cycle-index column. Defaults to
            ``HeadersNormal.cycle_index_txt`` (``"cycle_index"``).

    Returns:
        A new DataFrame (a view-safe copy) containing only the matching
        rows. Original index is preserved.

    Raises:
        KeyError: If ``column`` is not in ``df.columns``.
    """
    if column is None:
        column = get_headers_normal().cycle_index_txt

    if column not in df.columns:
        msg = (
            f"filter_cycles: column {column!r} not in DataFrame "
            f"(columns: {list(df.columns)[:8]}...)."
        )
        raise KeyError(msg)

    if cycles is None and last_cycle is None:
        return df.copy()

    mask = pd.Series(True, index=df.index)

    if cycles is not None:
        wanted = _normalize_cycles(cycles)
        mask &= df[column].isin(wanted)
        logger.debug("filter_cycles: keeping %d cycle(s)", len(wanted))

    if last_cycle is not None:
        mask &= df[column] <= last_cycle
        logger.debug("filter_cycles: truncating at cycle %d", last_cycle)

    return df.loc[mask].copy()


def _normalize_cycles(cycles: Union[int, Iterable[int]]) -> list[int]:
    """Coerce ``cycles`` into a sorted, deduplicated list of ints."""
    if isinstance(cycles, int):
        return [int(cycles)]
    if isinstance(cycles, Iterable):
        return sorted({int(c) for c in cycles})
    msg = f"cycles must be int or Iterable[int], got {type(cycles).__name__}"
    raise TypeError(msg)
