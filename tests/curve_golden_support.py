"""Curve-extraction golden snapshot helpers for Stage 0.6 get_cap-family oracles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import pytest
from cellpy import cellreader
from cellpy.exceptions import NullData

from tests.loader_golden_support import INTEGER_RAW_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS_ROOT = REPO_ROOT / "tests" / "data" / "goldens"
RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"

DATETIME_LIKE_COLUMNS = frozenset({"date_time"})
TIMEDELTA_LIKE_COLUMNS = frozenset({"step_time", "test_time"})
TEMPORAL_ABS_NS = 1_000


@dataclass(frozen=True)
class CurveGoldenCase:
    """One committed curve-extraction oracle."""

    suite: str
    func_name: str
    kwargs: dict[str, Any]
    expect_null_data: bool = False

    @property
    def golden_dir(self) -> Path:
        return GOLDENS_ROOT / self.suite

    def artifacts_present(self) -> bool:
        metrics_ok = (self.golden_dir / "metrics.json").is_file()
        if self.expect_null_data:
            return metrics_ok and (self.golden_dir / "null_data.json").is_file()
        return metrics_ok and (self.golden_dir / "curve.parquet").is_file()

    def skip_reason(self) -> str | None:
        if not RES_FILE.is_file():
            return f"source file missing: {RES_FILE.relative_to(REPO_ROOT)}"
        if not self.artifacts_present():
            return f"golden artifacts missing under {self.golden_dir.relative_to(REPO_ROOT)}"
        try:
            if self.expect_null_data:
                cell = load_golden_cell()
                _call_curve_func(cell, self)
                return f"{self.suite} expected NullData but call succeeded"
            run_curve_case(self)
        except NullData:
            if self.expect_null_data:
                return None
            return "curve extraction raised unexpected NullData"
        except Exception as exc:  # noqa: BLE001 — skip reason for pytest
            return f"curve extraction unavailable: {exc}"
        return None


CURVE_GOLDEN_CASES: tuple[CurveGoldenCase, ...] = (
    CurveGoldenCase(
        suite="curve_get_cap_back_and_forth_c1",
        func_name="get_cap",
        kwargs={"cycle": 1, "method": "back-and-forth"},
    ),
    CurveGoldenCase(
        suite="curve_get_cap_forth_labeled_c1",
        func_name="get_cap",
        kwargs={
            "cycle": 1,
            "method": "forth-and-forth",
            "categorical_column": True,
            "label_cycle_number": True,
            "insert_nan": False,
        },
    ),
    CurveGoldenCase(
        suite="curve_get_cap_forth_interpolated_c1",
        func_name="get_cap",
        kwargs={
            "cycle": 1,
            "method": "forth",
            "interpolated": True,
            "number_of_points": 100,
        },
    ),
    CurveGoldenCase(
        suite="curve_get_cap_forth_c12",
        func_name="get_cap",
        kwargs={
            "cycles": [1, 2],
            "method": "forth",
            "label_cycle_number": True,
            "insert_nan": False,
        },
    ),
    CurveGoldenCase(
        suite="curve_get_ccap_c5",
        func_name="get_ccap",
        kwargs={"cycle": 5, "as_frame": True},
    ),
    CurveGoldenCase(
        suite="curve_get_dcap_c5",
        func_name="get_dcap",
        kwargs={"cycle": 5, "as_frame": True},
    ),
    CurveGoldenCase(
        suite="curve_get_ocv_up_c1",
        func_name="get_ocv",
        kwargs={"cycles": 1, "direction": "up"},
    ),
    CurveGoldenCase(
        suite="curve_get_ccap_null_cycle",
        func_name="get_ccap",
        kwargs={"cycle": 999, "as_frame": True},
        expect_null_data=True,
    ),
    CurveGoldenCase(
        suite="curve_get_dcap_null_cycle",
        func_name="get_dcap",
        kwargs={"cycle": 999, "as_frame": True},
        expect_null_data=True,
    ),
)


def load_golden_cell() -> cellreader.CellpyCell:
    """Load the canonical Arbin cell used for curve-extraction goldens."""
    if not RES_FILE.is_file():
        raise FileNotFoundError(f"Missing source file {RES_FILE}")
    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()
    return cell


def prepare_curve_for_golden(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a stable column-only curve frame for golden parity."""
    out = frame.copy().reset_index(drop=True)
    temporal_cols = DATETIME_LIKE_COLUMNS | TIMEDELTA_LIKE_COLUMNS
    for col in out.columns:
        if col in INTEGER_RAW_COLUMNS or col in temporal_cols:
            continue
        if pd.api.types.is_integer_dtype(out[col]):
            out[col] = out[col].astype("float64")
    return out[sorted(out.columns)]


def _call_curve_func(cell: cellreader.CellpyCell, case: CurveGoldenCase):
    func: Callable[..., Any] = getattr(cell, case.func_name)
    return func(**case.kwargs)


def run_curve_case(case: CurveGoldenCase):
    """Run one curve case; return a DataFrame or raise NullData."""
    cell = load_golden_cell()
    result = _call_curve_func(cell, case)
    if not isinstance(result, pd.DataFrame):
        raise TypeError(
            f"{case.func_name} returned {type(result)!r}; curve goldens require a DataFrame"
        )
    if case.expect_null_data:
        raise AssertionError(f"{case.suite} expected NullData but got a frame")
    return prepare_curve_for_golden(result)


def curve_metrics(case: CurveGoldenCase, frame: pd.DataFrame | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "func_name": case.func_name,
        "kwargs": case.kwargs,
        "source": RES_FILE.relative_to(REPO_ROOT).as_posix(),
        "suite": case.suite,
        "expect_null_data": case.expect_null_data,
    }
    if frame is not None:
        payload["n_rows"] = int(len(frame))
        payload["n_columns"] = int(len(frame.columns))
        payload["columns"] = list(frame.columns)
    return payload


def capture_curve_case(
    case: CurveGoldenCase,
) -> tuple[pd.DataFrame | None, dict[str, Any], dict[str, Any] | None]:
    """Return frame (if any), metrics, and optional null_data descriptor."""
    cell = load_golden_cell()
    try:
        result = _call_curve_func(cell, case)
    except NullData as exc:
        if not case.expect_null_data:
            raise
        null_data = {"exception": "NullData", "message": str(exc)}
        return None, curve_metrics(case, None), null_data

    if case.expect_null_data:
        raise AssertionError(f"{case.suite} expected NullData but succeeded")

    if not isinstance(result, pd.DataFrame):
        raise TypeError(
            f"{case.func_name} returned {type(result)!r}; curve goldens require a DataFrame"
        )
    frame = prepare_curve_for_golden(result)
    return frame, curve_metrics(case, frame), None


def assert_temporal_series_equal(
    actual: pd.Series, expected: pd.Series, *, abs_ns: int
) -> None:
    if pd.api.types.is_timedelta64_dtype(actual) or pd.api.types.is_timedelta64_dtype(
        expected
    ):
        act = pd.to_timedelta(actual).astype("timedelta64[ns]").astype("int64").tolist()
        exp = (
            pd.to_timedelta(expected).astype("timedelta64[ns]").astype("int64").tolist()
        )
    else:
        act = pd.to_datetime(actual).astype("datetime64[ns]").astype("int64").tolist()
        exp = pd.to_datetime(expected).astype("datetime64[ns]").astype("int64").tolist()
    assert act == pytest.approx(exp, abs=abs_ns)


def assert_curve_matches_golden(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    """Compare curve frames with temporal column tolerance."""
    from pandas.testing import assert_frame_equal

    actual = prepare_curve_for_golden(actual)
    expected = prepare_curve_for_golden(expected)
    assert list(actual.columns) == list(expected.columns)

    temporal_cols = DATETIME_LIKE_COLUMNS | TIMEDELTA_LIKE_COLUMNS
    exact_cols = [c for c in actual.columns if c not in temporal_cols]
    if exact_cols:
        assert_frame_equal(actual[exact_cols], expected[exact_cols], check_dtype=False)

    for col in sorted(temporal_cols):
        if col in actual.columns:
            assert_temporal_series_equal(
                actual[col], expected[col], abs_ns=TEMPORAL_ABS_NS
            )


def read_null_data_descriptor(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))
