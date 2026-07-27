"""Shared golden-test helper: load the canonical Arbin cell.

The ICA golden suite proper (``ICA_GOLDEN_CASES`` / ``test_ica_goldens.py``)
recorded the *pre-redesign* ``cellpy.utils.ica`` entry points. Those 1.x shims
were removed in 2.1 (E2, #714), so the suite and its ``tests/data/goldens/
ica_dqdv_*`` oracles went with them. The modern ``dqdv``/``dvdq`` numeric oracle
lives in ``test_ica_api.py``; the specced-frame checks in ``test_ica.py``.

This module now only hosts :func:`load_golden_cell`, the canonical cell loader
shared by the curve goldens and the figure-spec support.
"""

from __future__ import annotations

from pathlib import Path

from cellpy import cellreader

REPO_ROOT = Path(__file__).resolve().parents[1]
RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"


def load_golden_cell() -> cellreader.CellpyCell:
    """Load the canonical Arbin cell used for the goldens."""
    if not RES_FILE.is_file():
        raise FileNotFoundError(f"Missing source file {RES_FILE}")
    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()
    return cell
