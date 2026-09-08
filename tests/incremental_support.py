"""Helpers for the incremental-update golden equality oracle (issue #778, L6).

The oracle: loading a *head* of a raw file and then appending the *tail* through
``update_core_data`` must produce the same ``raw`` / ``steps`` / ``summary`` as a
single full load.

``incremental_update`` is a test-side prototype of what L3 (#164) will expose as
``CellpyCell.update()``: it drives ``update_core_data`` with the cellpy-owned
by-value inputs (nominal capacity, current factor, instrument raw limits) and then
re-applies the cellpy-side summary extras and the scaled (mass/area) columns.
Replace this helper with the public API once L3 lands.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandas.testing as pdt
from cellpycore import units as core_units

from cellpy.readers.native_core import _add_summary_extras

REPO_ROOT = Path(__file__).resolve().parents[1]
NEWARE_UIO = REPO_ROOT / "testdata" / "data" / "neware_uio.csv"
NEWARE_KWARGS = {"instrument": "neware_txt", "model": "UIO"}


def truncate_text_file(src: Path, dst: Path, n_rows: int, header_lines: int = 1) -> Path:
    """Write the first ``n_rows`` data rows of ``src`` (plus header) to ``dst``."""
    with open(src, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    dst.write_text("".join(lines[: header_lines + n_rows]), encoding="utf-8")
    return dst


def tail_rows(raw: pd.DataFrame, datapoint_col: str, since: int, overlap: int = 0) -> pd.DataFrame:
    """Rows of ``raw`` after ``since``; ``overlap`` re-includes that many trailing rows."""
    return raw[raw[datapoint_col] > since - overlap]


def _to_pandas(frame):
    return frame.to_pandas() if hasattr(frame, "to_pandas") else frame


def incremental_update(cell, new_raw: pd.DataFrame, find_ir: bool = False):
    """Append ``new_raw`` to ``cell`` in place via ``update_core_data``.

    Mirrors the cellpy-side orchestration in ``make_step_table`` /
    ``make_summary`` so the result is comparable with a full ``cellpy.get``.
    """
    factor = core_units.calculate_current_conversion_factor(cell.data.raw_units["current"], to_units=cell.cellpy_units)
    nom_cap_abs = cell._resolve_nom_cap_abs(cell.data)
    out = cell.core.update_core_data(
        cell.data,
        new_raw,
        nom_cap_abs=nom_cap_abs,
        current_conversion_factor=factor,
        find_ir=find_ir,
        raw_limits=cell.raw_limits,
    )
    # ``update_core_data`` returns a bare cellpycore ``Data``; copy the frames back
    # so cellpy's metadata-bearing ``Data`` stays the owner.
    cell.data.raw = _to_pandas(out.raw)
    cell.data.steps = _to_pandas(out.steps)
    cell.data.summary = _add_summary_extras(_to_pandas(out.summary), cell.core.schema)
    cell._refresh_scaled_summary_columns()
    return cell


def _normalize(frame: pd.DataFrame, sort_by) -> pd.DataFrame:
    return frame.sort_values(sort_by).reset_index(drop=True)


def assert_frames_equal(left: pd.DataFrame, right: pd.DataFrame, sort_by, label: str) -> None:
    """Order-insensitive equality on the full column set; dtype differences allowed."""
    assert set(left.columns) == set(
        right.columns
    ), f"{label}: column mismatch: {set(left.columns) ^ set(right.columns)}"
    left = _normalize(left, sort_by)
    right = _normalize(right, sort_by)[left.columns]
    assert len(left) == len(right), f"{label}: {len(left)} rows vs {len(right)} rows"
    pdt.assert_frame_equal(left, right, check_dtype=False, rtol=1e-9, atol=1e-12, obj=label)


def assert_cell_frames_equal(updated, full) -> None:
    """``raw`` / ``steps`` / ``summary`` of ``updated`` must equal those of ``full``."""
    dp = full.schema.raw.datapoint_num
    st = full.schema.steps
    assert_frames_equal(updated.data.raw, full.data.raw, dp, "raw")
    assert_frames_equal(updated.data.steps, full.data.steps, [st.cycle_num, st.step_num], "steps")
    assert_frames_equal(updated.data.summary, full.data.summary, full.schema.summary.cycle_num, "summary")
