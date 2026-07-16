"""Campaign merge: fold several tests into one multi-test ``Data`` object.

Implements the v2 "campaign" merge (issue #507, epic #402 themes V2-03/V2-07):
each source keeps its identity via a distinct compact ``test_id`` stamped on the
raw frame, and its metadata becomes a record in the per-test collection
(``Data.tests``, issue #506). Cycle numbers are renumbered to be globally
unique (v1 — the legacy summary format cannot represent duplicate cycle
numbers; keeping original per-test numbering is deferred to the native-schema
path). ``test_time`` / ``date_time`` are *not* shifted — campaign sources have
independent timelines (mirrors ``cellpycore.merge.merge_data``).

This intentionally mirrors the semantics of ``cellpycore.merge.merge_data`` +
``cellpycore.metadata.io.merge_test_meta``; those cannot be called directly at
the legacy seam (they read native schema attribute names that the legacy
header objects do not have), and the metadata helper does not return the
``test_id`` remap needed to keep frames and records consistent.

Note the compact-key policy: the raw ``test_id`` column is overwritten with
compact keys (0, 1, 2, ...) at merge time — tester-assigned ids (e.g. Arbin's
``Test_ID``) remain available as provenance in
``meta_test_dependent.test_ID`` / ``TestMeta.cell``-level metadata.
"""

import dataclasses
import logging
from typing import Dict

from cellpy.parameters.internal_settings import (
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
)

from . import externals as externals

logger = logging.getLogger(__name__)


def _next_free(used) -> int:
    candidate = 0
    while candidate in used:
        candidate += 1
    return candidate


def normalize_test_id_column(data) -> None:
    """Stamp the compact ``test_id`` key onto ``data.raw`` (in place).

    For a non-campaign object (no extra test records) the column is created or
    *overwritten* with ``data.active_test_id`` — tester-assigned ids that some
    loaders (e.g. arbin_res) put in this column are provenance, not the
    grouping key. Campaign objects already carry compact ids; left untouched.
    """
    hdr = get_headers_normal().test_id_txt
    if data._extra_tests:
        if hdr not in data.raw.columns:
            raise ValueError(
                "campaign object without a test_id column in raw - cannot merge"
            )
        return
    data.raw[hdr] = data.active_test_id


def fold_test_metadata(left, right) -> Dict[int, int]:
    """Fold ``right``'s per-test records into ``left`` and return the id map.

    Mirrors ``cellpycore.metadata.io.merge_test_meta`` priority semantics
    (earlier records keep their ids; colliding later ids get the next free
    one), but returns the ``{old_id: new_id}`` map so the raw frames can be
    remapped consistently. ``right`` is never mutated (records are copied via
    ``dataclasses.replace``).
    """
    used = set(left.tests.test_ids)
    id_map: Dict[int, int] = {}
    for record in right.tests:
        target = record.test_id if record.test_id not in used else _next_free(used)
        id_map[record.test_id] = target
        left.set_test_meta(dataclasses.replace(record, test_id=target))
        used.add(target)
    return id_map


def campaign_fold(left, right, *, merge_steps=True, merge_summary=True) -> None:
    """Fold ``right`` (a ``Data`` object) into ``left`` as a distinct test.

    Mutates ``left`` in place; never mutates ``right``. See the module
    docstring for the semantics (compact test_id stamping, global cycle
    renumbering, no time shifting, per-test metadata records).
    """
    hn = get_headers_normal()
    hs = get_headers_summary()
    hst = get_headers_step_table()
    test_id_hdr = hn.test_id_txt

    if right.raw.empty:
        logger.warning("campaign merge: skipping a source with empty raw data")
        return
    if left.raw.empty:
        raise ValueError("campaign merge: the target object has empty raw data")

    if dict(left.raw_units) != dict(right.raw_units):
        raise ValueError(
            f"campaign merge: raw_units differ between sources "
            f"({left.raw_units} vs {right.raw_units}); convert first"
        )
    if dict(left.raw_limits) != dict(right.raw_limits):
        logger.warning(
            "campaign merge: raw_limits differ between sources; keeping the "
            "target's limits"
        )

    normalize_test_id_column(left)
    id_map = fold_test_metadata(left, right)

    right_raw = right.raw.copy()
    if right._extra_tests:
        if test_id_hdr not in right_raw.columns:
            raise ValueError(
                "campaign source without a test_id column in raw - cannot merge"
            )
        right_raw[test_id_hdr] = right_raw[test_id_hdr].map(
            lambda v: id_map[int(v)]
        )
    else:
        right_raw[test_id_hdr] = id_map[right.active_test_id]

    dp_hdr = hn.data_point_txt
    cyc_raw_hdr = hn.cycle_index_txt
    dp_offset = int(left.raw[dp_hdr].max())
    cycle_offset = int(left.raw[cyc_raw_hdr].max())
    right_raw[dp_hdr] = right_raw[dp_hdr] + dp_offset
    right_raw[cyc_raw_hdr] = right_raw[cyc_raw_hdr] + cycle_offset

    left.raw = externals.pandas.concat([left.raw, right_raw], ignore_index=True)

    # steps: offset + stamp test_id when both sides carry a step table,
    # else clear so the user re-runs make_step_table on the merged object.
    if merge_steps and not left.steps.empty and not right.steps.empty:
        point_first = f"{hst.point}_first"
        point_last = f"{hst.point}_last"
        left_steps = left.steps
        if test_id_hdr not in left_steps.columns:
            left_steps = left_steps.copy()
            left_steps[test_id_hdr] = _steps_test_id_from_raw(
                left, left_steps, point_first
            )
        right_steps = right.steps.copy()
        right_steps[hst.cycle] = right_steps[hst.cycle] + cycle_offset
        for col in (point_first, point_last):
            if col in right_steps.columns:
                right_steps[col] = right_steps[col] + dp_offset
        right_steps[test_id_hdr] = _steps_test_id_from_raw(
            left, right_steps, point_first
        )
        left.steps = externals.pandas.concat(
            [left_steps, right_steps], ignore_index=True
        )
    else:
        if merge_steps and not (left.steps.empty and right.steps.empty):
            logger.info(
                "campaign merge: step tables incomplete - run make_step_table()"
            )
        left.steps = externals.pandas.DataFrame()

    # summary: offset cycle/data_point; deliberately NO cumulative
    # carry-forward - per-test resets are the correct campaign semantics.
    summary_ok = (
        merge_summary
        and not left.summary.empty
        and not right.summary.empty
        and hs.cycle_index in left.summary.columns
        and hs.cycle_index in right.summary.columns  # arbin stats-frame guard
    )
    if summary_ok:
        right_summary = right.summary.copy()
        right_summary[hs.cycle_index] = right_summary[hs.cycle_index] + cycle_offset
        if hs.data_point in right_summary.columns:
            right_summary[hs.data_point] = right_summary[hs.data_point] + dp_offset
        left.summary = externals.pandas.concat(
            [left.summary, right_summary], ignore_index=True
        )
    else:
        if merge_summary and not (left.summary.empty and right.summary.empty):
            logger.info(
                "campaign merge: summaries incomplete - run make_summary()"
            )
        left.summary = externals.pandas.DataFrame()

    # provenance bookkeeping
    left.raw_data_files.extend(right.raw_data_files)
    left.raw_data_files_length.extend(right.raw_data_files_length)
    if not isinstance(left.loaded_from, list):
        left.loaded_from = [left.loaded_from]
    left.loaded_from.append(right.loaded_from)


def _steps_test_id_from_raw(data, steps, point_first_col):
    """Look up each step row's ``test_id`` from the (merged) raw frame via the
    step's first data point."""
    hn = get_headers_normal()
    mapping = (
        data.raw[[hn.data_point_txt, hn.test_id_txt]]
        .drop_duplicates(subset=hn.data_point_txt)
        .set_index(hn.data_point_txt)[hn.test_id_txt]
    )
    return steps[point_first_col].map(mapping)
