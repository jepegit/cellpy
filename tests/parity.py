"""Value-parity oracle for legacy vs native column names (issue #434).

Compares pandas frames through ``cellpycore.legacy.mapping``: mapped columns must
have equal values (dtype-tolerant, column-order independent). Unmapped columns are
ignored; mismatches on mapped columns fail unless listed in ``exceptions``.
"""

from __future__ import annotations

from typing import Collection, Literal, Union

import numpy as np
import pandas as pd
from cellpycore.config import default_schema
from cellpycore.legacy import mapping

Family = Literal["raw", "steps", "summary"]

SPECIFIC_MODES = ("gravimetric", "areal", "absolute")

# (legacy_key, native_key) tuples used to sort rows before comparing values.
_ROW_KEYS: dict[Family, tuple[tuple[str, str], ...]] = {
    "raw": (("data_point", "datapoint_num"),),
    "steps": (
        ("cycle", "cycle_num"),
        ("step", "step_num"),
        ("sub_step", "sub_step_num"),
    ),
    "summary": (("cycle_index", "cycle_num"),),
}


def legacy_native_pairs(family: Family) -> list[tuple[str, str]]:
    """Return ``(legacy_name, native_name)`` pairs for mapped columns in ``family``.

    Args:
        family: Frame family — ``"raw"``, ``"steps"``, or ``"summary"``.

    Returns:
        Ordered list of legacy/native column-name pairs, including summary
        ``{col}_{mode}`` specific variants.
    """
    if family == "raw":
        return [(legacy, native) for native, legacy in mapping.RAW_PAIRS]

    if family == "steps":
        pairs = [(legacy, native) for native, legacy in mapping.STEP_SCALAR_PAIRS]
        for native_base, legacy_base in mapping.STEP_BASE_PAIRS:
            for native_stat, legacy_stat in mapping.STAT_SUFFIXES.items():
                pairs.append(
                    (f"{legacy_base}_{legacy_stat}", f"{native_base}_{native_stat}")
                )
        return pairs

    if family == "summary":
        pairs = [(legacy, native) for native, legacy in mapping.CYCLE_PAIRS]
        cycle = default_schema().cycle
        native_to_legacy = mapping.native_to_legacy_summary()
        for native_base in cycle.specific_columns:
            legacy_base = native_to_legacy[native_base]
            for mode in SPECIFIC_MODES:
                pairs.append((f"{legacy_base}_{mode}", f"{native_base}_{mode}"))
        return pairs

    raise ValueError(f"unknown family {family!r}; expected 'raw', 'steps', or 'summary'")


def _as_pandas(frame: Union[pd.DataFrame, object]) -> pd.DataFrame:
    """Coerce polars or pandas input to a pandas ``DataFrame``."""
    if isinstance(frame, pd.DataFrame):
        return frame
    to_pandas = getattr(frame, "to_pandas", None)
    if callable(to_pandas):
        return to_pandas()
    raise TypeError(f"expected pandas or polars DataFrame, got {type(frame).__name__}")


def _normalize_exceptions(
    exceptions: Collection[str], pairs: list[tuple[str, str]]
) -> frozenset[str]:
    """Map exception names to native column identifiers."""
    legacy_to_native = {legacy: native for legacy, native in pairs}
    native_names = {native for _, native in pairs}
    normalized: set[str] = set()
    for name in exceptions:
        if name in native_names:
            normalized.add(name)
        elif name in legacy_to_native:
            normalized.add(legacy_to_native[name])
        else:
            raise ValueError(
                f"exception {name!r} is not a mapped legacy or native column name"
            )
    return frozenset(normalized)


def _row_key_pairs(
    legacy: pd.DataFrame, native: pd.DataFrame, family: Family
) -> list[tuple[str, str]]:
    return [
        (legacy_key, native_key)
        for legacy_key, native_key in _ROW_KEYS[family]
        if legacy_key in legacy.columns and native_key in native.columns
    ]


def _merge_on_row_keys(
    legacy: pd.DataFrame,
    native: pd.DataFrame,
    family: Family,
    *,
    legacy_col: str,
    native_col: str,
) -> tuple[pd.Series, pd.Series]:
    key_pairs = _row_key_pairs(legacy, native, family)
    if not key_pairs:
        legacy_rows = legacy.reset_index(drop=True)
        native_rows = native.reset_index(drop=True)
        if len(legacy_rows) != len(native_rows):
            raise AssertionError(
                f"{family}: row count mismatch ({len(legacy_rows)} legacy vs "
                f"{len(native_rows)} native)"
            )
        return legacy_rows[legacy_col], native_rows[native_col]

    legacy_keys = [legacy_key for legacy_key, _ in key_pairs]
    native_keys = [native_key for _, native_key in key_pairs]
    rename_native_keys = dict(zip(native_keys, legacy_keys))

    legacy_for_merge = legacy[legacy_keys].copy()
    legacy_for_merge["__legacy_value__"] = legacy[legacy_col].to_numpy()

    native_for_merge = native[native_keys].rename(columns=rename_native_keys)
    native_for_merge["__native_value__"] = native[native_col].to_numpy()

    merged = legacy_for_merge.merge(native_for_merge, on=legacy_keys, how="inner")
    if len(merged) != len(legacy) or len(merged) != len(native):
        raise AssertionError(
            f"{family}: row-key merge matched {len(merged)} rows "
            f"({len(legacy)} legacy, {len(native)} native)"
        )
    return merged["__legacy_value__"], merged["__native_value__"]


def _compare_series(legacy: pd.Series, native: pd.Series, *, label: str) -> None:
    if len(legacy) != len(native):
        raise AssertionError(f"{label}: length {len(legacy)} != {len(native)}")

    if pd.api.types.is_bool_dtype(legacy) or pd.api.types.is_bool_dtype(native):
        pd.testing.assert_series_equal(
            legacy.astype("boolean"),
            native.astype("boolean"),
            check_names=False,
            check_dtype=False,
        )
        return

    if (
        pd.api.types.is_numeric_dtype(legacy)
        or pd.api.types.is_numeric_dtype(native)
        or pd.api.types.is_datetime64_any_dtype(legacy)
        or pd.api.types.is_datetime64_any_dtype(native)
    ):
        legacy_num = pd.to_numeric(legacy, errors="coerce")
        native_num = pd.to_numeric(native, errors="coerce")
        if legacy_num.isna().equals(native_num.isna()):
            pd.testing.assert_series_equal(
                legacy_num,
                native_num,
                check_names=False,
                check_dtype=False,
                rtol=1e-9,
                atol=1e-9,
            )
            return

    legacy_obj = legacy.astype(object).where(legacy.notna(), other=np.nan)
    native_obj = native.astype(object).where(native.notna(), other=np.nan)
    pd.testing.assert_series_equal(
        legacy_obj, native_obj, check_names=False, check_dtype=False
    )


def assert_value_parity(
    legacy: Union[pd.DataFrame, object],
    native: Union[pd.DataFrame, object],
    family: Family,
    *,
    exceptions: Collection[str] = (),
) -> None:
    """Assert mapped legacy and native columns carry equal values.

    Args:
        legacy: Frame with legacy ``Headers*`` column names.
        native: Frame with native ``config.Cols`` column names.
        family: ``"raw"``, ``"steps"``, or ``"summary"``.
        exceptions: Mapped columns allowed to differ. Names may be legacy or
            native; unlisted mismatches always fail.

    Raises:
        AssertionError: On row-count or value mismatch outside ``exceptions``.
        ValueError: If an exception name is not a mapped column.
    """
    legacy_df = _as_pandas(legacy)
    native_df = _as_pandas(native)
    pairs = legacy_native_pairs(family)
    skipped = _normalize_exceptions(exceptions, pairs)

    compared = 0
    for legacy_col, native_col in pairs:
        if native_col in skipped:
            continue
        if legacy_col not in legacy_df.columns or native_col not in native_df.columns:
            continue
        compared += 1
        label = f"{family} {legacy_col!r} <-> {native_col!r}"
        legacy_series, native_series = _merge_on_row_keys(
            legacy_df, native_df, family, legacy_col=legacy_col, native_col=native_col
        )
        _compare_series(legacy_series, native_series, label=label)

    if compared == 0:
        raise AssertionError(
            f"{family}: no mapped columns present on both frames to compare"
        )
