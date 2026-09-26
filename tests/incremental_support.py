"""Helpers for the incremental-update golden equality oracle (issue #778, L6).

The oracle: loading a *head* of a raw file and then appending the *tail* through
``update_core_data`` must produce the same ``raw`` / ``steps`` / ``summary`` as a
single full load.

``incremental_update`` feeds a tail frame through the same code path L3 (#164)
uses inside ``CellpyCell.update()`` (``CellpyCell._update_from_raw_rows``), so
these tests stay the oracle for the shipped implementation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandas.testing as pdt

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


def incremental_update(cell, new_raw: pd.DataFrame, find_ir: bool = True):
    """Append ``new_raw`` to ``cell`` in place through ``CellpyCell.update()``'s engine."""
    return cell._update_from_raw_rows(new_raw, find_ir=find_ir)


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
