"""Cellpy-file layout specification.

Single source of truth for table keys, meta dirs, compression, and pandas
store formats. Version-specific layouts for historical file versions v4–v8
(HDF5) and v9 (zip-of-parquet + ``meta.json``).

Canonical file-version integers are mirrored in ``internal_settings``; the
values below are duplicated here to avoid an import cycle
(``internal_settings`` imports ``prms``, and ``prms`` aliases onto this module).
"""

from __future__ import annotations

from dataclasses import dataclass

# Latest on-disk format written by default (v9 zip-of-parquet).
CELLPY_FILE_VERSION = 9
MINIMUM_CELLPY_FILE_VERSION = 4
# Last HDF5 layout version (still readable; written when format="hdf5"/".h5").
HDF5_FILE_VERSION = 8

# v9 zip members
META_JSON_NAME = "meta.json"
V9_RAW_PARQUET = "raw.parquet"
V9_STEPS_PARQUET = "steps.parquet"
V9_SUMMARY_PARQUET = "summary.parquet"
V9_FID_PARQUET = "fid.parquet"
V9_EXTENSION = ".cellpy"
ZIP_LOCAL_HEADER_MAGIC = b"PK\x03\x04"


@dataclass(frozen=True)
class CellpyFileFormat:
    """Frozen layout spec for one cellpy-file format version (HDF5 family)."""

    version: int
    root: str
    raw_dir: str
    step_dir: str
    summary_dir: str
    fid_dir: str
    common_meta_dir: str
    test_dependent_meta_dir: str
    raw_unit_prefix: str
    raw_limit_prefix: str
    complevel: int
    complib: str | None
    raw_format: str
    summary_format: str
    stepdata_format: str
    infotable_format: str
    fidtable_format: str


def _modern_format(version: int) -> CellpyFileFormat:
    return CellpyFileFormat(
        version=version,
        root="CellpyData",
        raw_dir="/raw",
        step_dir="/steps",
        summary_dir="/summary",
        fid_dir="/fid",
        common_meta_dir="/info",
        test_dependent_meta_dir="/info_test_dependent",
        raw_unit_prefix="raw_unit_",
        raw_limit_prefix="",
        complevel=1,
        complib=None,
        raw_format="table",
        summary_format="table",
        stepdata_format="table",
        infotable_format="fixed",
        fidtable_format="fixed",
    )


FORMAT_V8 = _modern_format(8)
FORMAT_V7 = _modern_format(7)
FORMAT_V6 = _modern_format(6)
FORMAT_V5 = _modern_format(5)

FORMAT_V4 = CellpyFileFormat(
    version=4,
    root="CellpyData",
    raw_dir="/dfdata",
    step_dir="/step_table",
    summary_dir="/dfsummary",
    fid_dir="/fidtable",
    common_meta_dir="/info",
    test_dependent_meta_dir="/info_test_dependent",
    raw_unit_prefix="raw_unit_",
    raw_limit_prefix="",
    complevel=1,
    complib=None,
    raw_format="table",
    summary_format="table",
    stepdata_format="table",
    infotable_format="fixed",
    fidtable_format="fixed",
)

_FORMAT_BY_VERSION: dict[int, CellpyFileFormat] = {
    4: FORMAT_V4,
    5: FORMAT_V5,
    6: FORMAT_V6,
    7: FORMAT_V7,
    8: FORMAT_V8,
}


def get_format(version: int) -> CellpyFileFormat:
    """Return the HDF5 layout spec for a cellpy-file version.

    Args:
        version: On-disk ``cellpy_file_version`` (4–8 supported here).

    Returns:
        The matching ``CellpyFileFormat`` instance.

    Raises:
        KeyError: If ``version`` has no registered HDF5 layout (e.g. v9).
    """
    return _FORMAT_BY_VERSION[version]


def require_hdf5_support(context: str) -> None:
    """Raise a typed error when PyTables is missing and *context* needs it.

    ``tables`` moved from a required dependency to the ``legacy-files`` extra
    in 2.0 (#570): the default on-disk format is v9 (zip-of-parquet), so a
    plain install no longer pays for the HDF5 stack. Without this guard, a
    v4-v8 file on such an install would die inside pandas with
    ``ImportError: Missing optional dependency 'tables'`` - accurate, but
    naming neither the file format nor the fix.

    Args:
        context: what the caller was trying to do, for the error message.

    Raises:
        OptionalDependencyError: naming the extra to install.
    """
    import importlib.util

    if importlib.util.find_spec("tables") is not None:
        return

    from cellpy.exceptions import OptionalDependencyError

    raise OptionalDependencyError(
        f"{context} needs the HDF5 stack (PyTables), which is not installed. "
        "cellpy-files in the v4-v8 HDF5 layout are a legacy format; install "
        "the extra with:  pip install cellpy[legacy-files]  - or convert the "
        "file once with `cellpy convert` on an environment that has it."
    )
