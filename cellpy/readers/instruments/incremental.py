"""Shared pieces for loaders that implement `SupportsIncrementalLoad` (#780).

Why every ``load_since`` rewinds to a cycle start
--------------------------------------------------
``harmonize.normalize_reset_granularity`` re-accumulates per-step capacity
and rebases each cycle so it starts at 0. Both look at the *first row of the
cycle*. A chunk that begins mid-cycle would be rebased against the wrong row,
and the corruption would not raise anything. So a loader does not re-read
from the last row it saw; it re-reads from the first row of the last cycle it
saw. The marker points there. The trailing overlap is allowed by the
contract, and core ``update_data`` keeps the new rows for the overlapping
range, so the result equals a full load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import polars as pl

    from cellpy.readers.instruments.declarations import LoaderDeclarations


def vendor_column(declarations: "LoaderDeclarations", native_name: str) -> str | None:
    """The vendor column that ``declarations.column_map`` sends to ``native_name``."""
    for vendor, native in declarations.column_map.items():
        if native == native_name:
            return vendor
    return None


def last_cycle_start(frame: "pl.DataFrame", cycle_column: str | None) -> int:
    """Row index of the first row of the last cycle in ``frame``.

    Returns 0 when the frame is empty or has no ``cycle_column``, so a caller
    that cannot find cycle boundaries re-reads everything rather than
    guessing.
    """
    import polars as pl

    if cycle_column is None or frame.height == 0 or cycle_column not in frame.columns:
        return 0
    cycles = frame.get_column(cycle_column)
    last = cycles[-1]
    if last is None:
        return 0
    earlier = frame.with_row_index("_row").filter(pl.col(cycle_column) != last)
    if earlier.height == 0:
        return 0
    return int(earlier.get_column("_row").max()) + 1
