"""Per-test metadata helpers: legacy meta boxes <-> cellpycore TestMeta.

Pure translation helpers behind ``Data.tests`` (issue #506, epic #402 themes
V2-01/02/04). The legacy boxes (``Data.meta_common`` /
``Data.meta_test_dependent``) stay authoritative for the *active* test — the
core engine reads ``data.meta_test_dependent.cycle_mode`` live at compute time
— so the active ``TestMeta`` record is derived on access, and writes are
routed back onto the legacy boxes through the same importable pair tables.

Future direction: the metadata vocabulary and its export formats should align
with the BattINFO ontology (BIG-MAP initiative,
https://github.com/BIG-MAP/BattINFO) — prefer BattINFO-mappable terms when
extending fields or vocabularies here.
"""

import dataclasses
import logging
from typing import Any, Optional, Set, Tuple

from cellpycore.legacy import meta_mapping
from cellpycore.metadata.models import TestMeta

from . import externals as externals

logger = logging.getLogger(__name__)

# Core-model fields legacy has no home for; ``apply_test_meta_to_legacy`` must
# skip them instead of guessing a destination.
_CORE_ONLY_TEST_FIELDS = frozenset(meta_mapping.CORE_ONLY_TEST)
_CORE_ONLY_CELL_FIELDS = frozenset(meta_mapping.CORE_ONLY_CELL)


def _unwrap(value: Any) -> Any:
    """Normalize a legacy meta value to a plain scalar (or ``None``).

    Cellpy-file loads leave 1-element lists in ``meta_test_dependent`` (the
    ``update(as_list=True)`` path in ``cellpy_file.read``); HDF round-trips
    also produce numpy scalar types and ``NaN`` for absent values. ``TestMeta``
    fields are plain scalars with ``None`` meaning absent.
    """
    if isinstance(value, (list, tuple)):
        if len(value) == 1:
            return _unwrap(value[0])
        return value
    if isinstance(value, externals.numpy.generic):
        value = value.item()
    if isinstance(value, float) and value != value:  # NaN -> absent
        return None
    return value


def legacy_boxes_to_mappings(meta_common, meta_test_dependent) -> Tuple[dict, dict]:
    """Field mappings for the two legacy boxes, unwrapped to plain scalars.

    ``schedule_file_name`` is an un-annotated class attribute on
    ``CellpyMetaIndividualTest`` (``asdict`` drops it) but participates in the
    mapping — re-add it via ``getattr``.
    """
    common = {k: _unwrap(v) for k, v in dataclasses.asdict(meta_common).items()}
    individual = {
        k: _unwrap(v) for k, v in dataclasses.asdict(meta_test_dependent).items()
    }
    individual["schedule_file_name"] = _unwrap(
        getattr(meta_test_dependent, "schedule_file_name", None)
    )
    # A test_ID that cannot coerce to an int would make the core translation
    # raise on every access; degrade to None (-> test_id 0) with a warning.
    try:
        meta_mapping.coerce_test_id(individual.get("test_ID"))
    except ValueError:
        logger.warning(
            f"cannot interpret legacy test_ID {individual.get('test_ID')!r} "
            f"as an int; treating it as unset (test_id=0)"
        )
        individual["test_ID"] = None
    return common, individual


def build_active_test_meta(data) -> TestMeta:
    """Derive the active test's ``TestMeta`` (with linked ``CellMeta``) from
    the legacy meta boxes.

    ``test_id`` is set to ``data.active_test_id`` (the compact grouping key,
    0 for a single unmerged test) — the legacy ``test_ID`` is the
    tester-assigned id and remains in the legacy box as provenance.
    """
    common, individual = legacy_boxes_to_mappings(
        data.meta_common, data.meta_test_dependent
    )
    cell, test = meta_mapping.legacy_meta_to_core(common, individual)
    test.cell = cell
    test.test_id = data.active_test_id
    return test


def apply_test_meta_to_legacy(test_meta: TestMeta, meta_common, meta_test_dependent):
    """Write a ``TestMeta`` (and its linked ``CellMeta``) back onto the legacy
    boxes, inverting the mapping pair tables.

    ``None`` values and core-only fields (``uuid``, ``source_*``, ...) are
    skipped — this only routes fields that have a legacy home, so the legacy
    boxes (which the core engine reads live) never diverge from what was set.
    """
    for legacy_field, core_field in meta_mapping.INDIVIDUAL_TO_TEST_PAIRS:
        value = getattr(test_meta, core_field, None)
        if value is not None:
            setattr(meta_test_dependent, legacy_field, value)
    for legacy_field, core_field in meta_mapping.COMMON_TO_TEST_PAIRS:
        value = getattr(test_meta, core_field, None)
        if value is not None:
            setattr(meta_common, legacy_field, value)
    if test_meta.cell is not None:
        for legacy_field, core_field in meta_mapping.COMMON_TO_CELL_PAIRS:
            value = getattr(test_meta.cell, core_field, None)
            if value is not None:
                setattr(meta_common, legacy_field, value)


def cycle_modes_in_data(data) -> Set[str]:
    """Distinct non-None ``cycle_mode`` values among tests present in the data.

    When the raw frame carries a ``test_id`` column, only records for the ids
    actually present are considered; otherwise only the active test counts.
    Single-record collections short-circuit to the active mode.
    """
    tests = data.tests
    if len(tests) <= 1:
        mode = _unwrap(getattr(data.meta_test_dependent, "cycle_mode", None))
        return {mode} if mode is not None else set()

    # Extras without raw rows are dormant metadata: only the tests whose
    # ``test_id`` actually appears in the raw frame take part in compute. A raw
    # frame without the column carries the active test only.
    present_ids = {data.active_test_id}
    try:
        raw = data.raw
    except Exception:
        raw = None
    if raw is not None:
        from cellpy.parameters.internal_settings import get_headers_normal

        test_id_col = get_headers_normal().test_id_txt
        if hasattr(raw, "columns") and test_id_col in raw.columns:
            present_ids = {int(v) for v in raw[test_id_col].unique()}

    modes = set()
    for record in tests:
        if record.test_id not in present_ids:
            continue
        mode = _unwrap(record.cycle_mode)
        if mode is not None:
            modes.add(mode)
    return modes


def cycle_ranges_per_test(data) -> dict:
    """Per-test cycle ranges ``{test_id: (cycle_min, cycle_max)}``.

    Derived from the raw frame's ``test_id`` column (campaign-merged objects,
    issue #507), so it survives save/load of raw without extra state. A raw
    frame without the column reports the active test spanning all cycles.
    """
    from cellpy.parameters.internal_settings import get_headers_normal

    hn = get_headers_normal()
    raw = data.raw
    if raw.empty:
        return {}
    if hn.test_id_txt not in raw.columns:
        cycles = raw[hn.cycle_index_txt]
        return {data.active_test_id: (int(cycles.min()), int(cycles.max()))}
    grouped = raw.groupby(hn.test_id_txt)[hn.cycle_index_txt].agg(["min", "max"])
    return {
        int(test_id): (int(row["min"]), int(row["max"]))
        for test_id, row in grouped.iterrows()
    }
