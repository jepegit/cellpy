"""Meta-table helpers for cellpy-file (HDF5) I/O."""

from __future__ import annotations

import warnings
from typing import Any

from cellpy.readers import externals
from cellpy.exceptions import WrongFileVersion
from cellpy.parameters import prms


def unwrap_meta_value(value: Any) -> Any:
    """Normalize a legacy meta value to a plain scalar (or ``None``).

    Cellpy-file loads leave 1-element lists in ``meta_test_dependent`` (the
    ``update(as_list=True)`` path). Older files can also carry double-nested
    values such as ``[['anode']]`` for ``cycle_mode``; the summarizer bridge
    needs a scalar string (issue #668).
    """
    if isinstance(value, (list, tuple)):
        if len(value) == 1:
            return unwrap_meta_value(value[0])
        return value
    if isinstance(value, externals.numpy.generic):
        value = value.item()
    if isinstance(value, float) and value != value:  # NaN -> absent
        return None
    return value


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
