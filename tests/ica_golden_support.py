"""ICA golden snapshot helpers (#566 Phase 0).

These capture the **numeric** output of the pre-redesign ``cellpy.utils.ica``
entry points so the redesign can be verified as a move rather than a rewrite.
The interpolate → smooth → invert → diff → smooth → normalize recipe is
order-sensitive; shape assertions would not have caught a reordering, so these
oracles record values.

Every case deliberately goes through the *old* public entry points. After the
redesign those are deprecation shims over the new core, and

```shell
uv run python dev/regenerate_goldens.py --verify
```

then proves the shims still produce bit-identical numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from cellpy import cellreader

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS_ROOT = REPO_ROOT / "tests" / "data" / "goldens"
RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"


def load_golden_cell() -> cellreader.CellpyCell:
    """Load the canonical Arbin cell used for the ICA goldens."""
    if not RES_FILE.is_file():
        raise FileNotFoundError(f"Missing source file {RES_FILE}")
    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()
    return cell


def _flatten_wide(frame: pd.DataFrame) -> pd.DataFrame:
    """Flatten a wide MultiIndex ICA frame for parquet.

    ``dqdv(tidy=False)`` returns columns as ``(cycle, value)`` pairs, which
    parquet cannot express. Joining them with ``"::"`` keeps both levels
    visible in the committed artifact.
    """
    if not isinstance(frame.columns, pd.MultiIndex):
        raise TypeError(
            "expected MultiIndex columns; a flat frame would be flattened "
            "character-by-character"
        )
    out = frame.copy()
    out.columns = ["::".join(str(part) for part in col) for col in out.columns]
    return out.reset_index(drop=True)


# --- capture functions -------------------------------------------------------
# One per suite. Each returns a plain DataFrame of float columns.


def _capture_dqdv_np_c5(cell: cellreader.CellpyCell) -> pd.DataFrame:
    from cellpy.utils import ica

    capacity, voltage = cell.get_ccap(5, as_frame=False)
    v, dqdv = ica.dqdv_np(voltage, capacity)
    return pd.DataFrame({"voltage": np.asarray(v), "dqdv": np.asarray(dqdv)})


def _capture_dqdv_np_c5_no_smoothing(cell: cellreader.CellpyCell) -> pd.DataFrame:
    from cellpy.utils import ica

    capacity, voltage = cell.get_ccap(5, as_frame=False)
    v, dqdv = ica.dqdv_np(
        voltage,
        capacity,
        pre_smoothing=False,
        post_smoothing=False,
        post_normalization=False,
    )
    return pd.DataFrame({"voltage": np.asarray(v), "dqdv": np.asarray(dqdv)})


def _capture_dqdv_np_c5_resolution(cell: cellreader.CellpyCell) -> pd.DataFrame:
    """Exercises the voltage_resolution / diff_smoothing branches."""
    from cellpy.utils import ica

    capacity, voltage = cell.get_ccap(5, as_frame=False)
    v, dqdv = ica.dqdv_np(
        voltage,
        capacity,
        voltage_resolution=0.005,
        diff_smoothing=True,
        voltage_fwhm=0.02,
    )
    return pd.DataFrame({"voltage": np.asarray(v), "dqdv": np.asarray(dqdv)})


def _capture_dqdv_cycles_labeled(cell: cellreader.CellpyCell) -> pd.DataFrame:
    from cellpy.utils import ica

    cycles = cell.get_cap(
        method="forth-and-forth",
        categorical_column=True,
        label_cycle_number=True,
        insert_nan=False,
    )
    return ica.dqdv_cycles(cycles, label_direction=True).reset_index(drop=True)


def _capture_dqdv_combined(cell: cellreader.CellpyCell) -> pd.DataFrame:
    from cellpy.utils import ica

    return ica.dqdv(cell, label_direction=True).reset_index(drop=True)


def _capture_dqdv_split_charge(cell: cellreader.CellpyCell) -> pd.DataFrame:
    """The split path — note it reaches the curves through
    ``collect_capacity_curves``, not ``get_cap``, and interpolates onto a fixed
    100-point voltage range. Unifying those two extraction routes is the point
    of the redesign, so this oracle is what "unified" has to reproduce."""
    from cellpy.utils import ica

    charge, _ = ica.dqdv(cell, split=True)
    return charge.reset_index(drop=True)


def _capture_dqdv_split_discharge(cell: cellreader.CellpyCell) -> pd.DataFrame:
    from cellpy.utils import ica

    _, discharge = ica.dqdv(cell, split=True)
    return discharge.reset_index(drop=True)


def _capture_dqdv_wide(cell: cellreader.CellpyCell) -> pd.DataFrame:
    """The wide MultiIndex output of ``dqdv(tidy=False)``."""
    from cellpy.utils import ica

    return _flatten_wide(ica.dqdv(cell, tidy=False))


@dataclass(frozen=True)
class IcaGoldenCase:
    """One committed ICA oracle."""

    suite: str
    description: str
    capture: Callable[[cellreader.CellpyCell], pd.DataFrame]
    kwargs: dict[str, Any] = field(default_factory=dict)

    @property
    def golden_dir(self) -> Path:
        return GOLDENS_ROOT / self.suite

    def artifacts_present(self) -> bool:
        return (self.golden_dir / "ica.parquet").is_file() and (
            self.golden_dir / "metrics.json"
        ).is_file()

    def skip_reason(self) -> str | None:
        if not RES_FILE.is_file():
            return f"source file missing: {RES_FILE.relative_to(REPO_ROOT)}"
        if not self.artifacts_present():
            return (
                f"golden artifacts missing under "
                f"{self.golden_dir.relative_to(REPO_ROOT)}"
            )
        return None


ICA_GOLDEN_CASES: tuple[IcaGoldenCase, ...] = (
    IcaGoldenCase(
        suite="ica_dqdv_np_c5",
        description="dqdv_np on the cycle-5 charge curve with default options",
        capture=_capture_dqdv_np_c5,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_np_c5_raw",
        description="dqdv_np with every smoothing and the normalization off",
        capture=_capture_dqdv_np_c5_no_smoothing,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_np_c5_resolution",
        description="dqdv_np with voltage_resolution and diff smoothing",
        capture=_capture_dqdv_np_c5_resolution,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_cycles_labeled",
        description="dqdv_cycles over every cycle, with direction labels",
        capture=_capture_dqdv_cycles_labeled,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_combined",
        description="dqdv(cell) long frame over every cycle",
        capture=_capture_dqdv_combined,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_split_charge",
        description="dqdv(cell, split=True) charge frame (long)",
        capture=_capture_dqdv_split_charge,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_split_discharge",
        description="dqdv(cell, split=True) discharge frame (long)",
        capture=_capture_dqdv_split_discharge,
    ),
    IcaGoldenCase(
        suite="ica_dqdv_wide",
        description="dqdv(cell, tidy=False) wide MultiIndex frame (flattened)",
        capture=_capture_dqdv_wide,
    ),
)


def prepare_ica_for_golden(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a stable float-typed frame for golden parity."""
    out = frame.copy().reset_index(drop=True)
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].astype("float64")
    return out[sorted(out.columns)]


def ica_metrics(case: IcaGoldenCase, frame: pd.DataFrame) -> dict[str, Any]:
    """Scalar summary alongside the frame, so a diff says *what* moved."""
    numeric = frame.select_dtypes("number")
    return {
        "columns": list(frame.columns),
        "description": case.description,
        "n_columns": int(len(frame.columns)),
        "n_rows": int(len(frame)),
        # Rounded so that platform-level last-bit noise does not churn the
        # metrics file; the parquet frame carries the exact values.
        "sums": {
            col: round(float(np.nansum(numeric[col].to_numpy())), 6)
            for col in numeric.columns
        },
        "source": RES_FILE.relative_to(REPO_ROOT).as_posix(),
        "suite": case.suite,
    }


def capture_ica_case(case: IcaGoldenCase) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run one ICA case and return (frame, metrics)."""
    cell = load_golden_cell()
    result = case.capture(cell)
    if not isinstance(result, pd.DataFrame):
        raise TypeError(
            f"{case.suite} produced {type(result)!r}; ICA goldens require a DataFrame"
        )
    frame = prepare_ica_for_golden(result)
    return frame, ica_metrics(case, frame)


def assert_ica_matches_golden(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    """Compare ICA frames value-for-value."""
    from pandas.testing import assert_frame_equal

    actual = prepare_ica_for_golden(actual)
    expected = prepare_ica_for_golden(expected)
    assert list(actual.columns) == list(expected.columns)
    assert_frame_equal(actual, expected, check_dtype=False)
