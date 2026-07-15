"""Dormant native ⇄ legacy frame translation for the cellpy-file boundary.

Native-headers plan Phase 1 (issue #458, Stage 1.15): the translation layer
that the cellpy 2 flip will run **once at I/O** instead of today's per-call
rename sandwich. On the v1.x line this module is *dormant* — nothing in the
runtime calls it yet; the round-trip and totality tests keep it honest until
the flip (native-headers plan Phase 3) wires it into ``cellpy_file.load``.

All header knowledge comes from ``cellpycore.legacy.mapping`` (the authoritative
lossless/total mapping, extended in core #116 with ``expand_specific_columns``);
no column names are declared here.

Import policies implemented (native-headers plan D3):

- **Mapped columns** are renamed (both directions; summary includes the
  ``{col}_{gravimetric|areal|absolute}`` specific variants).
- **Legacy-only columns** pass through unchanged (the native schema tolerates
  extras). Deriving ``epoch_time_utc`` from ``date_time`` and the
  drop-and-recompute policy for summary cruft belong to the Phase-3 importer,
  not this dormant layer — round trips here are lossless by construction.
- **``test_id``** is injected (``= 0``) on the native side when absent
  (native group keys are composite) and stripped again on the legacy side for
  frames that never carried it (steps/summary), so v8 → native → v8 is exact.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cellpycore.config import default_schema
from cellpycore.legacy import mapping

if TYPE_CHECKING:
    import pandas as pd

    from cellpy.readers.data_structures import Data

SPECIFIC_MODES = ("gravimetric", "areal", "absolute")

_TEST_ID = "test_id"


def _summary_native_to_legacy_rename() -> dict:
    """Native → legacy summary rename incl. the specific-column variants."""
    schema = default_schema()
    return mapping.expand_specific_columns(
        mapping.native_to_legacy_summary(),
        schema.cycle.specific_columns,
        SPECIFIC_MODES,
    )


def _rename_present(frame: "pd.DataFrame", rename: dict) -> "pd.DataFrame":
    """Rename only the columns present; never touch anything else."""
    present = {old: new for old, new in rename.items() if old in frame.columns}
    return frame.rename(columns=present)


# --- frame-level translation ---------------------------------------------------
def raw_to_native(frame: "pd.DataFrame") -> "pd.DataFrame":
    """Legacy raw frame → native ``RawCols`` names (extras pass through)."""
    return _rename_present(frame, mapping.legacy_to_native_raw())


def raw_to_legacy(frame: "pd.DataFrame") -> "pd.DataFrame":
    """Native raw frame → legacy ``HeadersNormal`` names."""
    rename = {native: legacy for native, legacy in mapping.RAW_PAIRS}
    return _rename_present(frame, rename)


def steps_to_native(frame: "pd.DataFrame") -> "pd.DataFrame":
    """Legacy step table → native ``StepCols`` names (extras pass through)."""
    return _rename_present(frame, mapping.legacy_to_native_step())


def steps_to_legacy(frame: "pd.DataFrame") -> "pd.DataFrame":
    """Native step table → legacy ``HeadersStepTable`` names."""
    return _rename_present(frame, mapping.native_to_legacy_step())


def summary_to_native(frame: "pd.DataFrame") -> "pd.DataFrame":
    """Legacy summary → native ``CycleCols`` names incl. specific variants."""
    rename = {v: k for k, v in _summary_native_to_legacy_rename().items()}
    return _rename_present(frame, rename)


def summary_to_legacy(frame: "pd.DataFrame") -> "pd.DataFrame":
    """Native summary → legacy ``HeadersSummary`` names incl. specific variants."""
    return _rename_present(frame, _summary_native_to_legacy_rename())


# --- column classification (the totality guard) --------------------------------
def classify_legacy_columns(columns, family: str) -> dict:
    """Classify legacy columns as ``mapped`` / ``legacy-only`` / ``unknown``.

    The importer's totality guard (native-headers plan Phase 1 tests): every
    column in a v8 file must be classified — an ``unknown`` column fails the
    round-trip test until it is deliberately categorized in the core mapping.

    Args:
        columns: Iterable of legacy column names.
        family: ``"raw"``, ``"steps"``, or ``"summary"``.

    Returns:
        dict: ``{column_name: classification}``.
    """
    if family == "raw":
        mapped = set(mapping.legacy_to_native_raw())
        legacy_only = set(mapping.LEGACY_ONLY_RAW)
    elif family == "steps":
        mapped = set(mapping.legacy_to_native_step())
        legacy_only = set(mapping.LEGACY_ONLY_STEP)
    elif family == "summary":
        mapped = set(_summary_native_to_legacy_rename().values())
        legacy_only = set(mapping.LEGACY_ONLY_CYCLE)
    else:
        raise ValueError(
            f"unknown family {family!r}; expected 'raw', 'steps', or 'summary'"
        )

    out = {}
    for col in columns:
        if col in mapped:
            out[col] = "mapped"
        elif col in legacy_only:
            out[col] = "legacy-only"
        elif family == "summary" and col.startswith("aux_"):
            # the legacy aux_ prefix marker covers a family of columns
            out[col] = "legacy-only"
        elif family == "summary" and _is_legacy_only_specific_variant(col):
            # legacy specific_columns included the shifted_* capacities, so
            # old files carry e.g. shifted_charge_capacity_gravimetric —
            # legacy-only base, legacy-only variant
            out[col] = "legacy-only"
        elif family == "steps" and col == "index":
            # the bridge's index-column sort quirk (native-headers plan D4)
            out[col] = "legacy-only"
        elif col == _TEST_ID:
            out[col] = "legacy-only"
        else:
            out[col] = "unknown"
    return out


def _is_legacy_only_specific_variant(col: str) -> bool:
    """True for ``{legacy-only col}_{mode}`` summary variants in old files."""
    for mode in SPECIFIC_MODES:
        suffix = f"_{mode}"
        if col.endswith(suffix):
            return col.removesuffix(suffix) in mapping.LEGACY_ONLY_CYCLE
    return False


# --- Data-level translation -----------------------------------------------------
def to_native(data: "Data") -> "Data":
    """Translate a legacy-named ``Data`` object's frames to native names.

    Renames in place on the passed object (frames are replaced, not mutated),
    and injects ``test_id = 0`` where absent — native group keys are composite
    ``(test_id, cycle_num, …)`` (native-headers plan D3).
    """
    if getattr(data, "raw", None) is not None and len(data.raw.columns):
        raw = raw_to_native(data.raw)
        if _TEST_ID not in raw.columns:
            raw = raw.assign(**{_TEST_ID: 0})
        data.raw = raw
    if getattr(data, "steps", None) is not None and len(data.steps.columns):
        steps = steps_to_native(data.steps)
        if _TEST_ID not in steps.columns:
            steps = steps.assign(**{_TEST_ID: 0})
        data.steps = steps
    if getattr(data, "summary", None) is not None and len(data.summary.columns):
        summary = summary_to_native(data.summary)
        if _TEST_ID not in summary.columns:
            summary = summary.assign(**{_TEST_ID: 0})
        data.summary = summary
    return data


def to_legacy(data: "Data", *, injected_test_id: bool = True) -> "Data":
    """Translate a native-named ``Data`` object's frames back to legacy names.

    Args:
        data: The object whose frames get renamed (replaced, not mutated).
        injected_test_id: Strip the ``test_id`` column from steps/summary
            (legacy never carried it there; raw keeps its own legacy
            ``test_id``). Set False to keep it.
    """
    if getattr(data, "raw", None) is not None and len(data.raw.columns):
        data.raw = raw_to_legacy(data.raw)
    if getattr(data, "steps", None) is not None and len(data.steps.columns):
        steps = steps_to_legacy(data.steps)
        if injected_test_id and _TEST_ID in steps.columns:
            steps = steps.drop(columns=[_TEST_ID])
        data.steps = steps
    if getattr(data, "summary", None) is not None and len(data.summary.columns):
        summary = summary_to_legacy(data.summary)
        if injected_test_id and _TEST_ID in summary.columns:
            summary = summary.drop(columns=[_TEST_ID])
        data.summary = summary
    return data
