"""Cellpy-file (HDF5) layout specification.

Single source of truth for table keys, meta dirs, compression, and pandas
store formats. Version-specific layouts for historical file versions v4–v8.

Canonical file-version integers remain in ``internal_settings``; the values
below are duplicated here to avoid an import cycle (``internal_settings`` imports
``prms``, and ``prms`` aliases onto this module).
"""

from __future__ import annotations

from dataclasses import dataclass

# Must match cellpy.parameters.internal_settings (canonical site).
CELLPY_FILE_VERSION = 8
MINIMUM_CELLPY_FILE_VERSION = 4


@dataclass(frozen=True)
class CellpyFileFormat:
    """Frozen layout spec for one cellpy-file format version."""

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
    """Return the layout spec for a cellpy-file version.

    Args:
        version: On-disk ``cellpy_file_version`` (4–8 supported here).

    Returns:
        The matching ``CellpyFileFormat`` instance.

    Raises:
        KeyError: If ``version`` has no registered layout.
    """
    return _FORMAT_BY_VERSION[version]
