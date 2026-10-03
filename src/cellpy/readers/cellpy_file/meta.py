"""Meta-table helpers for cellpy-file (HDF5) I/O."""

from __future__ import annotations

import warnings

from cellpy.readers import externals
from cellpy.exceptions import WrongFileVersion
from cellpy.parameters import prms
from cellpy.readers.cellpy_file.format import require_hdf5_support


def extract_from_meta_dictionary(
    meta_dict, attribute, default_value=None, hard=False
):
    try:
        value = meta_dict[attribute][0]
        if not value:
            value = None
    except KeyError as e:
        if hard:
            raise KeyError from e
        value = default_value
    return value


def get_cellpy_file_version(filename, meta_dir=None, parent_level=None):
    require_hdf5_support(f"reading the HDF5 cellpy-file {filename}")
    if meta_dir is None:
        meta_dir = prms._cellpyfile_common_meta

    if parent_level is None:
        parent_level = prms._cellpyfile_root

    with externals.pandas.HDFStore(filename) as store:
        try:
            meta_table = store.select(parent_level + meta_dir)
        except KeyError:
            raise WrongFileVersion(
                "This file is VERY old - cannot read file version number"
            )
    try:
        meta_dict = meta_table.to_dict(orient="list")
        cellpy_file_version = extract_from_meta_dictionary(
            meta_dict, "cellpy_file_version"
        )
    except Exception as e:
        warnings.warn(f"Unhandled exception raised: {e}")
        return 0

    return cellpy_file_version
