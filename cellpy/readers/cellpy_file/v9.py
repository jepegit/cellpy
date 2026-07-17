"""Cellpy-file format v9 — zip-of-parquet + sidecar ``meta.json``.

On-disk frames use **native** column names (``cellpycore`` schema). The current
runtime still speaks legacy names, so ``save`` translates legacy → native before
writing and ``load`` translates native → legacy after reading (I/O boundary
adapter; full native runtime is #511).

Metadata document shape is owned by ``meta_archive`` (cellpy policy; core
``save_archive`` / ``load_archive`` stubs stay stubs).
"""

from __future__ import annotations

import io
import json
import logging
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from cellpy.exceptions import CorruptCellpyFile, WrongFileVersion
from cellpy.readers import data_structures as ds
from cellpy.readers import externals
from cellpy.readers.cellpy_file import fids as cellpy_file_fids
from cellpy.readers.cellpy_file import meta_archive
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
_TEST_ID = "test_id"


def is_zip_cellpy(path: PathLike) -> bool:
    """True if ``path`` looks like a zip archive (PK\\x03\\x04 local header)."""
    try:
        with open(path, "rb") as fh:
            return fh.read(4) == ZIP_LOCAL_HEADER_MAGIC
    except OSError:
        return False


def _frames_had_test_id(data: "Data") -> dict[str, bool]:
    """Record which frames already carried ``test_id`` before native inject."""
    return {
        "raw": bool(
            getattr(data, "raw", None) is not None
            and len(data.raw.columns)
            and _TEST_ID in data.raw.columns
        ),
        "steps": bool(
            getattr(data, "steps", None) is not None
            and len(data.steps.columns)
            and _TEST_ID in data.steps.columns
        ),
        "summary": bool(
            getattr(data, "summary", None) is not None
            and len(data.summary.columns)
            and _TEST_ID in data.summary.columns
        ),
    }


def _strip_injected_test_id(data: "Data", had: Mapping[str, bool]) -> None:
    """Drop ``test_id`` from steps/summary when it was only injected at save."""
    if not had.get("steps") and getattr(data, "steps", None) is not None:
        if _TEST_ID in data.steps.columns:
            data.steps = data.steps.drop(columns=[_TEST_ID])
    if not had.get("summary") and getattr(data, "summary", None) is not None:
        if _TEST_ID in data.summary.columns:
            data.summary = data.summary.drop(columns=[_TEST_ID])


def _normalize_frame_nulls(frame):
    """Align parquet nulls with pandas float-NaN convention used by HDF5 loads."""
    return frame.replace({None: externals.numpy.nan})


def _frame_to_parquet_bytes(frame) -> bytes:
    buf = io.BytesIO()
    to_write = frame
    if getattr(frame, "index", None) is not None and frame.index.name is not None:
        name = frame.index.name
        if name in frame.columns:
            to_write = frame.reset_index(drop=True)
        else:
            to_write = frame.reset_index()
    to_write.to_parquet(buf, index=False, engine="pyarrow")
    return buf.getvalue()


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
    had_test_id = _frames_had_test_id(data)

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

    meta_doc = meta_archive.build_meta_document(
        data,
        cellpy_units=cellpy_units,
        frames_had_test_id=had_test_id,
    )
    meta_doc["active_test_id"] = int(data.active_test_id)

    fid_table = cellpy_file_fids.convert2fid_table(data)
    fid_df = externals.pandas.DataFrame(fid_table)

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            META_JSON_NAME,
            json.dumps(meta_doc, indent=2, default=meta_archive._json_default),
        )
        zf.writestr(V9_RAW_PARQUET, _frame_to_parquet_bytes(scratch.raw))
        zf.writestr(V9_STEPS_PARQUET, _frame_to_parquet_bytes(scratch.steps))
        zf.writestr(V9_SUMMARY_PARQUET, _frame_to_parquet_bytes(scratch.summary))
        if not fid_df.empty:
            zf.writestr(V9_FID_PARQUET, _frame_to_parquet_bytes(fid_df))

    _module_logger.debug("wrote v9 cellpy-file %s", path)


def load(filename: PathLike, *, selector=None) -> LoadResult:
    """Load a v9 ``.cellpy`` zip into a legacy-named ``Data`` object."""
    del selector  # max_cycle selection not implemented for v9 yet
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

    meta_archive.apply_meta_document(data, meta_doc)
    # Keep real campaign test_id columns; strip only injected ones.
    cellpy_file_translate.to_legacy(data, injected_test_id=False)
    had = meta_doc.get("frames_had_test_id") or {
        "raw": True,
        "steps": False,
        "summary": False,
    }
    _strip_injected_test_id(data, had)
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


# Re-export for callers that imported these from v9 during Milestone A.
build_meta_document = meta_archive.build_meta_document
apply_meta_document = meta_archive.apply_meta_document
