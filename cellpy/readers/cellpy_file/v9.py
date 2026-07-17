"""Cellpy-file format v9 — zip-of-parquet + sidecar ``meta.json``.

On-disk frames use **native** column names (``cellpycore`` schema). The current
runtime still speaks legacy names, so ``save`` translates legacy → native before
writing and ``load`` translates native → legacy after reading (I/O boundary
adapter; full native runtime is #511).
"""

from __future__ import annotations

import enum
import io
import json
import logging
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from cellpycore.config import Cols, default_schema
from cellpycore.metadata.io import from_dict, to_dict
from cellpycore.metadata.models import CellMeta, TestMeta
from cellpycore.units import CellpyUnits

from cellpy.exceptions import CorruptCellpyFile, WrongFileVersion
from cellpy.parameters.internal_settings import CellpyLimits
from cellpy.readers import data_structures as ds
from cellpy.readers import externals
from cellpy.readers import test_meta as test_meta_helpers
from cellpy.readers.cellpy_file import fids as cellpy_file_fids
from cellpy.readers.cellpy_file import translate as cellpy_file_translate
from cellpy.readers.cellpy_file.format import (
    CELLPY_FILE_VERSION,
    META_JSON_NAME,
    V9_EXTENSION,
    V9_FID_PARQUET,
    V9_RAW_PARQUET,
    V9_STEPS_PARQUET,
    V9_SUMMARY_PARQUET,
    ZIP_LOCAL_HEADER_MAGIC,
)
from cellpy.readers.cellpy_file.selectors import LoadLimits, LoadResult

if TYPE_CHECKING:
    from cellpy.readers.data_structures import Data

_module_logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


def is_zip_cellpy(path: PathLike) -> bool:
    """True if ``path`` looks like a zip archive (PK\\x03\\x04 local header)."""
    try:
        with open(path, "rb") as fh:
            return fh.read(4) == ZIP_LOCAL_HEADER_MAGIC
    except OSError:
        return False


def _json_default(obj: Any) -> Any:
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")


def build_meta_document(
    data: "Data",
    *,
    cellpy_units: Optional[Mapping[str, Any]] = None,
) -> dict:
    """Build the v9 ``meta.json`` document from a ``Data`` object."""
    tests_doc: dict[str, dict] = {}
    cell_doc: Optional[dict] = None
    # Compact ``test_id`` (grouping key) is not the tester-assigned ``test_ID``.
    # Preserve the latter so apply_test_meta_to_legacy does not clobber it.
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
    return {
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


def _frame_to_parquet_bytes(frame) -> bytes:
    buf = io.BytesIO()
    # Reset index so keys live in columns (native / polars convention).
    to_write = frame
    if getattr(frame, "index", None) is not None and frame.index.name is not None:
        name = frame.index.name
        if name in frame.columns:
            to_write = frame.reset_index(drop=True)
        else:
            to_write = frame.reset_index()
    to_write.to_parquet(buf, index=False, engine="pyarrow")
    return buf.getvalue()


def _normalize_frame_nulls(frame):
    """Align parquet nulls with pandas float-NaN convention used by HDF5 loads."""
    # pyarrow writes pandas NA/NaN in object columns as Python None on read.
    return frame.replace({None: externals.numpy.nan})


def _read_parquet_member(zf: zipfile.ZipFile, name: str):
    try:
        raw = zf.read(name)
    except KeyError as e:
        raise CorruptCellpyFile(f"missing zip member {name!r}") from e
    frame = externals.pandas.read_parquet(io.BytesIO(raw), engine="pyarrow")
    return _normalize_frame_nulls(frame)


def save(
    data: "Data",
    path: PathLike,
    *,
    cellpy_units: Optional[Mapping[str, Any]] = None,
) -> None:
    """Write ``Data`` as a v9 ``.cellpy`` zip (parquet tables + ``meta.json``).

    Frames are translated to native column names for storage. The in-memory
    ``data`` object is **not** mutated (work is done on copies).
    """
    path = Path(path)
    # Work on a shallow copy of frames so translate.to_native does not mutate caller.
    scratch = ds.Data()
    scratch.raw = data.raw.copy() if data.raw is not None else externals.pandas.DataFrame()
    scratch.steps = (
        data.steps.copy() if data.steps is not None else externals.pandas.DataFrame()
    )
    scratch.summary = (
        data.summary.copy()
        if data.summary is not None
        else externals.pandas.DataFrame()
    )
    scratch.meta_common = data.meta_common
    scratch.meta_test_dependent = data.meta_test_dependent
    scratch._extra_tests = dict(getattr(data, "_extra_tests", {}) or {})
    scratch._active_test_id = data.active_test_id
    scratch._provenance = dict(getattr(data, "_provenance", {}) or {})
    scratch.raw_units = dict(data.raw_units)
    scratch.raw_limits = dict(data.raw_limits)
    scratch.raw_data_files = list(data.raw_data_files or [])
    scratch.raw_data_files_length = list(data.raw_data_files_length or [])
    scratch.loaded_from = getattr(data, "loaded_from", None)

    cellpy_file_translate.to_native(scratch)

    meta_doc = build_meta_document(data, cellpy_units=cellpy_units)
    # Prefer native frames' test_id story from the scratch object for consistency.
    meta_doc["active_test_id"] = int(data.active_test_id)

    fid_table = cellpy_file_fids.convert2fid_table(data)
    fid_df = externals.pandas.DataFrame(fid_table)

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            META_JSON_NAME,
            json.dumps(meta_doc, indent=2, default=_json_default),
        )
        zf.writestr(V9_RAW_PARQUET, _frame_to_parquet_bytes(scratch.raw))
        zf.writestr(V9_STEPS_PARQUET, _frame_to_parquet_bytes(scratch.steps))
        zf.writestr(V9_SUMMARY_PARQUET, _frame_to_parquet_bytes(scratch.summary))
        if not fid_df.empty:
            zf.writestr(V9_FID_PARQUET, _frame_to_parquet_bytes(fid_df))

    _module_logger.debug("wrote v9 cellpy-file %s", path)


def _apply_meta_document(data: "Data", meta_doc: dict) -> None:
    version = int(meta_doc.get("cellpy_file_version", CELLPY_FILE_VERSION))
    if version != CELLPY_FILE_VERSION:
        raise WrongFileVersion(
            f"v9 reader expected cellpy_file_version={CELLPY_FILE_VERSION}, got {version}"
        )

    units_payload = dict(meta_doc.get("raw_units") or {})
    limits_payload = dict(meta_doc.get("limits") or {})
    data.raw_units = CellpyUnits(**{k: v for k, v in units_payload.items() if k in CellpyUnits()})
    # Overlay onto defaults so missing keys keep CellpyLimits defaults.
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
        if record.cell is None and cell_fallback:
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
        # apply maps TestMeta.test_id → legacy test_ID; restore tester-assigned.
        if active_id in tester_assigned:
            data.meta_test_dependent.test_ID = tester_assigned[active_id]
        # Core-only fields have no legacy home — keep them in _provenance.
        provenance = {}
        for key in test_meta_helpers._CORE_ONLY_TEST_FIELDS - {"cell", "comment"}:
            value = getattr(active_record, key, None)
            if value is not None:
                provenance[key] = value
        data._provenance = provenance


def load(filename: PathLike, *, selector=None) -> LoadResult:
    """Load a v9 ``.cellpy`` zip into a legacy-named ``Data`` object."""
    del selector  # max_cycle selection not implemented for v9 in Milestone A
    path = Path(filename)
    if not path.is_file():
        raise IOError(f"File does not exist: {filename}")

    with zipfile.ZipFile(path, mode="r") as zf:
        try:
            meta_raw = zf.read(META_JSON_NAME)
        except KeyError as e:
            raise CorruptCellpyFile(
                f"{path} is a zip but missing {META_JSON_NAME}"
            ) from e
        meta_doc = json.loads(meta_raw.decode("utf-8"))
        version = int(meta_doc.get("cellpy_file_version", 0))
        if version != CELLPY_FILE_VERSION:
            raise WrongFileVersion(
                f"Unsupported zip cellpy version {version} in {path}"
            )

        data = ds.Data()
        data.raw = _read_parquet_member(zf, V9_RAW_PARQUET)
        data.steps = _read_parquet_member(zf, V9_STEPS_PARQUET)
        data.summary = _read_parquet_member(zf, V9_SUMMARY_PARQUET)

        if V9_FID_PARQUET in zf.namelist():
            fid_table = _read_parquet_member(zf, V9_FID_PARQUET)
            data.raw_data_files, data.raw_data_files_length = (
                cellpy_file_fids.convert2fid_list(fid_table)
            )
        else:
            data.raw_data_files = []
            data.raw_data_files_length = []

    _apply_meta_document(data, meta_doc)
    # Runtime still expects legacy headers.
    cellpy_file_translate.to_legacy(data, injected_test_id=True)
    data.loaded_from = str(path)

    limits = LoadLimits()
    return LoadResult.from_limits(data, CELLPY_FILE_VERSION, limits)


def get_version_from_zip(path: PathLike) -> int:
    """Read ``cellpy_file_version`` from a v9 zip's ``meta.json``."""
    with zipfile.ZipFile(path, mode="r") as zf:
        meta_doc = json.loads(zf.read(META_JSON_NAME).decode("utf-8"))
    return int(meta_doc.get("cellpy_file_version", 0))


def suggest_extension() -> str:
    """Default filename extension for v9 (without the leading dot)."""
    return V9_EXTENSION.lstrip(".")
