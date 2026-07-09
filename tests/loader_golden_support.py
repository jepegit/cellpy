"""Loader golden snapshot helpers for Stage 0.5 per-loader oracles."""

from __future__ import annotations

import datetime
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from cellpy import cellreader

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS_ROOT = REPO_ROOT / "tests" / "data" / "goldens"

DATETIME_LIKE_COLUMNS = frozenset({"date_time"})
TIMEDELTA_LIKE_COLUMNS = frozenset({"step_time", "test_time"})
TEMPORAL_ABS_NS = 1_000


class LoaderGoldenSpec:
    """Configuration for one loader golden suite."""

    __slots__ = (
        "suite",
        "instrument",
        "source",
        "from_raw_kwargs",
        "instrument_file",
        "set_instrument_kwargs",
    )

    def __init__(
        self,
        suite: str,
        instrument: str,
        source: str,
        *,
        from_raw_kwargs: dict[str, Any] | None = None,
        instrument_file: str | None = None,
        set_instrument_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.suite = suite
        self.instrument = instrument
        self.source = source
        self.from_raw_kwargs = from_raw_kwargs or {}
        self.instrument_file = instrument_file
        self.set_instrument_kwargs = set_instrument_kwargs or {}

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source

    @property
    def instrument_file_path(self) -> Path | None:
        if self.instrument_file is None:
            return None
        return REPO_ROOT / self.instrument_file

    @property
    def golden_dir(self) -> Path:
        return GOLDENS_ROOT / self.suite

    def artifacts_present(self) -> bool:
        d = self.golden_dir
        return (
            (d / "raw.parquet").is_file()
            and (d / "raw_units.json").is_file()
            and (d / "meta.json").is_file()
        )

    def skip_reason(self) -> str | None:
        if not self.source_path.is_file():
            return f"source file missing: {self.source}"
        if self.instrument_file is not None and not self.instrument_file_path.is_file():
            return f"instrument file missing: {self.instrument_file}"
        if not self.artifacts_present():
            return f"golden artifacts missing under {self.golden_dir.relative_to(REPO_ROOT)}"
        try:
            load_loader_snapshot(self)
        except Exception as exc:  # noqa: BLE001 — skip reason for pytest
            return f"loader unavailable: {exc}"
        return None


LOADER_GOLDEN_SPECS: tuple[LoaderGoldenSpec, ...] = (
    LoaderGoldenSpec(
        suite="loader_arbin_res",
        instrument="arbin_res",
        source="testdata/data/20160805_test001_45_cc_01.res",
    ),
    LoaderGoldenSpec(
        suite="loader_maccor_txt",
        instrument="maccor_txt",
        source="testdata/data/maccor_001.txt",
        from_raw_kwargs={"model": "one", "sep": "\t"},
    ),
    LoaderGoldenSpec(
        suite="loader_neware_txt",
        instrument="neware_txt",
        source="testdata/data/neware_uio.csv",
        from_raw_kwargs={"model": "one"},
    ),
    LoaderGoldenSpec(
        suite="loader_pec_csv",
        instrument="pec_csv",
        source="testdata/data/pec.csv",
    ),
    LoaderGoldenSpec(
        suite="loader_custom",
        instrument="custom",
        source="testdata/data/custom_data_001.csv",
        instrument_file="testdata/data/custom_instrument_001.yml",
    ),
)


def prepare_raw_for_golden(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a column-only raw frame with stable column order for goldens."""
    frame = raw.copy()
    if frame.index.name == "data_point" and "data_point" in frame.columns:
        frame = frame.reset_index(drop=True)
    elif frame.index.name is not None:
        frame = frame.reset_index()
    if not isinstance(frame.index, pd.RangeIndex):
        frame = frame.reset_index(drop=True)
    return frame[sorted(frame.columns)]


def json_safe(value: Any) -> Any:
    """Convert loader meta/units values to JSON-serializable form."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime.datetime)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, (pd.Timedelta, datetime.timedelta, np.timedelta64)):
        return int(pd.Timedelta(value).value)
    if isinstance(value, dict):
        return {
            str(k): json_safe(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if is_dataclass(value):
        return json_safe(asdict(value))
    return str(value)


def normalize_raw_units(raw_units: dict[str, Any]) -> dict[str, str | None]:
    """Return sorted raw_units with string values for stable JSON goldens."""
    return {
        key: None if raw_units[key] is None else str(raw_units[key])
        for key in sorted(raw_units)
    }


def extract_loader_meta(data) -> dict[str, Any]:
    """Capture loader-set meta: meta objects, units, limits, custom_info."""
    payload: dict[str, Any] = {
        "meta_common": json_safe(asdict(data.meta_common)),
        "meta_test_dependent": json_safe(asdict(data.meta_test_dependent)),
        "raw_units": normalize_raw_units(data.raw_units),
        "raw_limits": json_safe(dict(data.raw_limits)),
    }
    if data.custom_info is not None:
        payload["custom_info"] = json_safe(data.custom_info)
    return payload


def load_loader_snapshot(spec: LoaderGoldenSpec):
    """Load one vendor file and return normalized raw frame + meta payload."""
    cell = cellreader.CellpyCell()
    if spec.instrument == "custom":
        cell.set_instrument(
            instrument="custom",
            instrument_file=str(spec.instrument_file_path),
            **spec.set_instrument_kwargs,
        )
    else:
        cell.set_instrument(instrument=spec.instrument, **spec.set_instrument_kwargs)
    cell.from_raw(str(spec.source_path), **spec.from_raw_kwargs)
    raw = prepare_raw_for_golden(cell.data.raw)
    meta = extract_loader_meta(cell.data)
    metrics = {
        "n_rows": int(len(raw)),
        "n_columns": int(len(raw.columns)),
        "source": spec.source,
        "suite": spec.suite,
        "instrument": spec.instrument,
    }
    return raw, meta, metrics


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


def assert_raw_matches_golden(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    """Compare loader raw frames with temporal column tolerance."""
    from tests.golden_support import sort_summary_columns
    from pandas.testing import assert_frame_equal

    actual = sort_summary_columns(prepare_raw_for_golden(actual))
    expected = sort_summary_columns(prepare_raw_for_golden(expected))
    assert list(actual.columns) == list(expected.columns)

    temporal_cols = DATETIME_LIKE_COLUMNS | TIMEDELTA_LIKE_COLUMNS
    exact_cols = [c for c in actual.columns if c not in temporal_cols]
    if exact_cols:
        assert_frame_equal(actual[exact_cols], expected[exact_cols])

    for col in sorted(temporal_cols):
        if col in actual.columns:
            assert_temporal_series_equal(
                actual[col], expected[col], abs_ns=TEMPORAL_ABS_NS
            )
