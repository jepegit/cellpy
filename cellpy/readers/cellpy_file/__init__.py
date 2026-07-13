"""Cellpy-file (HDF5) I/O package."""

from cellpy.readers.cellpy_file.format import (
    CELLPY_FILE_VERSION,
    MINIMUM_CELLPY_FILE_VERSION,
    FORMAT_V4,
    FORMAT_V5,
    FORMAT_V6,
    FORMAT_V7,
    FORMAT_V8,
    CellpyFileFormat,
    get_format,
)
from cellpy.readers.cellpy_file.selectors import LoadLimits, LoadResult, LoadSelector

__all__ = [
    "CELLPY_FILE_VERSION",
    "MINIMUM_CELLPY_FILE_VERSION",
    "CellpyFileFormat",
    "FORMAT_V4",
    "FORMAT_V5",
    "FORMAT_V6",
    "FORMAT_V7",
    "FORMAT_V8",
    "LoadLimits",
    "LoadResult",
    "LoadSelector",
    "get_format",
    "load",
    "read_fid_table",
    "read_table",
    "save",
]


def __getattr__(name: str):
    if name == "load":
        from cellpy.readers.cellpy_file.read import load

        return load
    if name == "save":
        from cellpy.readers.cellpy_file.write import save

        return save
    if name == "read_table":
        from cellpy.readers.cellpy_file.read import read_table

        return read_table
    if name == "read_fid_table":
        from cellpy.readers.cellpy_file.fids import read_fid_table

        return read_fid_table
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
