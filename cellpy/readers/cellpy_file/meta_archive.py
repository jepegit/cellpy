"""Cellpy-owned metadata archive helpers (issue #510, V2-14).

``cellpycore.metadata.io.save_archive`` / ``load_archive`` stay deliberate
stubs — real persistence lives here. Use these helpers (or the v9 ``.cellpy``
path which embeds the same document as ``meta.json``).
"""

from __future__ import annotations

import enum
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from cellpycore.config import Cols, default_schema
from cellpycore.metadata.io import from_dict, to_dict
from cellpycore.metadata.models import CellMeta, TestMeta, TestMetaCollection
from cellpycore.units import CellpyUnits

from cellpy.exceptions import WrongFileVersion
from cellpy.parameters.internal_settings import CellpyLimits
from cellpy.readers import test_meta as test_meta_helpers
from cellpy.readers.cellpy_file.format import CELLPY_FILE_VERSION

if TYPE_CHECKING:
    from cellpy.readers.data_structures import Data

_module_logger = logging.getLogger(__name__)

PathLike = Union[str, Path]
MetaArchiveSource = Union["Data", TestMetaCollection, TestMeta]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return obj.as_posix()
    # OtherPath / path-like without being a pathlib.Path
    if hasattr(obj, "as_posix"):
        try:
            return obj.as_posix()
        except Exception:
            pass
    if hasattr(obj, "__fspath__"):
        return Path(obj).as_posix()
    if hasattr(obj, "item"):
        return obj.item()
    return str(obj)


def build_meta_document(
    data: "Data",
    *,
    cellpy_units: Optional[Mapping[str, Any]] = None,
    frames_had_test_id: Optional[Mapping[str, bool]] = None,
) -> dict:
    """Build the archive / v9 ``meta.json`` document from a ``Data`` object."""
    tests_doc: dict[str, dict] = {}
    cell_doc: Optional[dict] = None
    active_tester_id = test_meta_helpers._unwrap(
        getattr(data.meta_test_dependent, "test_ID", None)
    )
    for record in data.tests:
        payload = to_dict(record)
        if cell_doc is None and isinstance(payload.get("cell"), dict):
            cell_doc = payload["cell"]
        if int(record.test_id) == int(data.active_test_id):
            payload["tester_assigned_test_id"] = active_tester_id
        tests_doc[str(record.test_id)] = payload

    if cell_doc is None:
        cell_doc = to_dict(CellMeta())

    schema = default_schema()
    doc = {
        "cellpy_file_version": CELLPY_FILE_VERSION,
        "schema_version": Cols.__version__,
        "raw_schema_version": schema.raw.__version__,
        "step_schema_version": schema.step.__version__,
        "cycle_schema_version": schema.cycle.__version__,
        "cell": cell_doc,
        "tests": tests_doc,
        "raw_units": dict(data.raw_units),
        "cellpy_units": dict(cellpy_units) if cellpy_units else {},
        "limits": dict(data.raw_limits),
        "active_test_id": int(data.active_test_id),
        "loaded_from": getattr(data, "loaded_from", None),
    }
    if frames_had_test_id is not None:
        doc["frames_had_test_id"] = dict(frames_had_test_id)
    return doc


def build_meta_document_from_collection(
    collection: TestMetaCollection,
    *,
    cell: Optional[CellMeta] = None,
    active_test_id: Optional[int] = None,
) -> dict:
    """Build an archive document from a standalone ``TestMetaCollection``."""
    tests_doc = {str(record.test_id): to_dict(record) for record in collection}
    cell_doc = to_dict(cell) if cell is not None else to_dict(CellMeta())
    if active_test_id is None:
        active_test_id = (
            collection.test_ids[0] if collection.test_ids else 0
        )
    schema = default_schema()
    return {
        "cellpy_file_version": CELLPY_FILE_VERSION,
        "schema_version": Cols.__version__,
        "raw_schema_version": schema.raw.__version__,
        "step_schema_version": schema.step.__version__,
        "cycle_schema_version": schema.cycle.__version__,
        "cell": cell_doc,
        "tests": tests_doc,
        "raw_units": {},
        "cellpy_units": {},
        "limits": {},
        "active_test_id": int(active_test_id),
        "loaded_from": None,
    }


def collection_from_meta_document(meta_doc: Mapping[str, Any]) -> TestMetaCollection:
    """Rebuild a ``TestMetaCollection`` from an archive document."""
    collection = TestMetaCollection()
    cell_fallback = meta_doc.get("cell") or {}
    for payload in (meta_doc.get("tests") or {}).values():
        if not isinstance(payload, dict):
            continue
        record = from_dict(TestMeta, payload)
        # Only fill shared cell when the record omitted ``cell`` entirely —
        # explicit ``null`` means no linked CellMeta.
        if record.cell is None and cell_fallback and "cell" not in payload:
            record.cell = from_dict(CellMeta, cell_fallback)
        collection.add(record)
    return collection


def apply_meta_document(data: "Data", meta_doc: Mapping[str, Any]) -> None:
    """Apply an archive / v9 ``meta.json`` document onto a ``Data`` object."""
    version = int(meta_doc.get("cellpy_file_version", CELLPY_FILE_VERSION))
    if version != CELLPY_FILE_VERSION:
        raise WrongFileVersion(
            f"meta archive expected cellpy_file_version={CELLPY_FILE_VERSION}, "
            f"got {version}"
        )

    units_payload = dict(meta_doc.get("raw_units") or {})
    limits_payload = dict(meta_doc.get("limits") or {})
    data.raw_units = CellpyUnits(
        **{k: v for k, v in units_payload.items() if k in CellpyUnits()}
    )
    limits = CellpyLimits()
    for key, value in limits_payload.items():
        if key in limits:
            limits[key] = value
    data.raw_limits = limits
    if meta_doc.get("loaded_from") is not None:
        data.loaded_from = meta_doc["loaded_from"]
    data.meta_common.cellpy_file_version = version

    active_id = int(meta_doc.get("active_test_id", 0))
    data._active_test_id = active_id

    tests_doc = meta_doc.get("tests") or {}
    cell_fallback = meta_doc.get("cell") or {}

    records: dict[int, TestMeta] = {}
    tester_assigned: dict[int, Any] = {}
    for payload in tests_doc.values():
        if not isinstance(payload, dict):
            continue
        tid_key = int(payload.get("test_id", 0))
        if "tester_assigned_test_id" in payload:
            tester_assigned[tid_key] = payload.get("tester_assigned_test_id")
        record = from_dict(TestMeta, payload)
        if record.cell is None and cell_fallback and "cell" not in payload:
            record.cell = from_dict(CellMeta, cell_fallback)
        records[int(record.test_id)] = record

    if active_id not in records and records:
        active_id = next(iter(records))
        data._active_test_id = active_id

    active_record = records.get(active_id)
    data._extra_tests = {tid: rec for tid, rec in records.items() if tid != active_id}

    if active_record is not None:
        test_meta_helpers.apply_test_meta_to_legacy(
            active_record, data.meta_common, data.meta_test_dependent
        )
        if active_id in tester_assigned:
            data.meta_test_dependent.test_ID = tester_assigned[active_id]
        provenance = {}
        for key in test_meta_helpers._CORE_ONLY_TEST_FIELDS - {"cell", "comment"}:
            value = getattr(active_record, key, None)
            if value is not None:
                provenance[key] = value
        data._provenance = provenance


def save_meta_archive(
    source: MetaArchiveSource,
    path: PathLike,
    *,
    cellpy_units: Optional[Mapping[str, Any]] = None,
    cell: Optional[CellMeta] = None,
    active_test_id: Optional[int] = None,
) -> None:
    """Save a metadata archive JSON file (cellpy-owned; core stubs stay stubs).

    Args:
        source: A ``Data`` object, ``TestMetaCollection``, or single ``TestMeta``.
        path: Destination path (typically ``*.meta.json``).
        cellpy_units: Optional units mapping when ``source`` is ``Data``.
        cell: Optional shared ``CellMeta`` when saving a collection alone.
        active_test_id: Active test when saving a collection alone.
    """
    if isinstance(source, TestMeta):
        collection = TestMetaCollection()
        collection.add(source)
        doc = build_meta_document_from_collection(
            collection, cell=cell, active_test_id=active_test_id
        )
    elif isinstance(source, TestMetaCollection):
        doc = build_meta_document_from_collection(
            source, cell=cell, active_test_id=active_test_id
        )
    else:
        doc = build_meta_document(source, cellpy_units=cellpy_units)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, default=_json_default), encoding="utf-8")
    _module_logger.debug("wrote meta archive %s", path)


def load_meta_archive(path: PathLike) -> dict:
    """Load a metadata archive JSON document.

    Returns:
        The archive document (same shape as v9 ``meta.json``).
    """
    path = Path(path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    version = int(doc.get("cellpy_file_version", 0))
    if version != CELLPY_FILE_VERSION:
        raise WrongFileVersion(
            f"Unsupported meta archive version {version} in {path}"
        )
    return doc
