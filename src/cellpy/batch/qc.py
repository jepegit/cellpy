"""Batch quality control.

The legacy ``_check_cell_*`` family (batch.py:367-456) as one function that
returns a tidy per-cell pass/fail frame, instead of ten methods feeding a
styled report. The facade's ``report()`` renders this frame.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl

#: Preferred charge-capacity column for the cap statistics (native first).
_CAP_COLS = ("charge_capacity_gravimetric", "charge_capacity")


def _frame_len(frame: Any) -> int | None:
    if frame is None:
        return None
    height = getattr(frame, "height", None)
    if height is not None:
        return int(height)
    try:
        return int(len(frame))
    except TypeError:
        return None


def _cap_col(summary: Any) -> str | None:
    columns = getattr(summary, "columns", [])
    for candidate in _CAP_COLS:
        if candidate in columns:
            return candidate
    return None


def _check_one(label: str, cell: Any) -> dict:
    row: dict[str, Any] = {
        "cell": label,
        "empty": None,
        "n_raw": None,
        "n_steps": None,
        "n_summary": None,
        "n_cycles": None,
        "max_cap": None,
        "min_cap": None,
        "avg_cap": None,
        "std_cap": None,
        "pass": False,
    }
    try:
        row["empty"] = bool(cell.empty)
    except Exception:  # noqa: BLE001 - QC never raises on a single cell
        pass

    data = getattr(cell, "data", None)
    row["n_raw"] = _frame_len(getattr(data, "raw", None))
    row["n_steps"] = _frame_len(getattr(data, "steps", None))
    summary = getattr(data, "summary", None)
    row["n_summary"] = _frame_len(summary)

    steps = getattr(data, "steps", None)
    if steps is not None and "cycle_num" in getattr(steps, "columns", []):
        try:
            row["n_cycles"] = int(steps["cycle_num"].max())
        except Exception:  # noqa: BLE001
            pass

    if summary is not None and _frame_len(summary):
        col = _cap_col(summary)
        if col is not None:
            series = summary[col]
            try:
                row["max_cap"] = float(series.max())
                row["min_cap"] = float(series.min())
                row["avg_cap"] = float(series.mean())
                row["std_cap"] = float(series.std())
            except Exception:  # noqa: BLE001
                pass

    row["pass"] = (row["empty"] is False) and bool(row["n_summary"])
    return row


def check(cells: Mapping[str, Any], journal: Any | None = None) -> pl.DataFrame:
    """Return a tidy per-cell QC frame (one row per cell)."""
    rows = [_check_one(label, cell) for label, cell in cells.items()]
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows)
