"""Legacy cellpy-file (HDF5) readers — v3 through v7."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Union

from cellpy.exceptions import WrongFileVersion
from cellpy.parameters import prms
from cellpy.readers.cellpy_file.format import HDF5_FILE_VERSION
from cellpy.readers import data_structures as ds
from cellpy.readers import externals
from cellpy.readers.cellpy_file import keys as cellpy_file_keys
from cellpy.readers.cellpy_file.format import FORMAT_V4, FORMAT_V5, FORMAT_V6, FORMAT_V7
from cellpy.readers.cellpy_file.read import (
    _assign_fids_from_table,
    create_initial_data_set_from_cellpy_file,
    extract_fids_from_cellpy_file,
    extract_raw_from_cellpy_file,
    extract_steps_from_cellpy_file,
    extract_summary_from_cellpy_file,
)
from cellpy.readers.cellpy_file.selectors import LoadLimits

if TYPE_CHECKING:
    from cellpy.readers.data_structures import Data


def extract_meta_from_old_cellpy_file_max_v7(
    data: "Data",
    meta_table: "externals.pandas.DataFrame",
    filename: Union[Path, str],
    upgrade_from_to: tuple,
) -> None:
    old, new = upgrade_from_to
    logging.debug(f"upgrading meta from {old} to {new}")
    if old > 7:
        raise IOError("using this method for processing v>7 is not allowed!")

    meta_dict = meta_table.to_dict(orient="list")

    for key in data.raw_limits:
        h5_key = f"{prms._cellpyfile_raw_limit_pre_id}{key}"
        try:
            v = meta_dict.pop(h5_key)
            data.raw_units[key] = v[0]
        except KeyError:
            logging.debug(f"missing key in meta_table: {h5_key}")

    for key in data.raw_units:
        h5_key = f"{prms._cellpyfile_raw_unit_pre_id}{key}"
        try:
            v = meta_dict.pop(h5_key)
            v = v[0]
            if not isinstance(v, str):
                logging.debug(f"{v} is not of type string")
                v = ds.convert_from_simple_unit_label_to_string_unit_label(key, v)
            data.raw_units[key] = v
        except KeyError:
            logging.critical(f"missing key in meta_table: {h5_key}")

    meta_dict = data.meta_common.digest(as_list=False, **meta_dict)
    data.meta_test_dependent.update(as_list=True, **meta_dict)


def load_v7(filename, selector=None) -> tuple["Data", LoadLimits]:
    logging.debug("--- loading v7")
    fmt = FORMAT_V7
    parent_level = fmt.root
    limits = LoadLimits()

    with externals.pandas.HDFStore(filename) as store:
        data, meta_table = create_initial_data_set_from_cellpy_file(
            fmt.common_meta_dir, parent_level, store
        )
        cellpy_file_keys.check_keys_in_cellpy_file(
            fmt.common_meta_dir,
            parent_level,
            fmt.raw_dir,
            store,
            fmt.summary_dir,
        )
        limits = extract_summary_from_cellpy_file(
            data,
            parent_level,
            store,
            fmt.summary_dir,
            selector=selector,
            limits=limits,
        )
        extract_raw_from_cellpy_file(
            data, parent_level, fmt.raw_dir, store, limits=limits
        )
        extract_steps_from_cellpy_file(
            data, parent_level, fmt.step_dir, store, limits=limits
        )
        fid_table, fid_table_selected = extract_fids_from_cellpy_file(
            fmt.fid_dir, parent_level, store
        )

    extract_meta_from_old_cellpy_file_max_v7(
        data, meta_table, filename, upgrade_from_to=(7, HDF5_FILE_VERSION)
    )
    _assign_fids_from_table(data, fid_table, fid_table_selected)
    return data, limits


def load_v6(filename, selector=None) -> tuple["Data", LoadLimits]:
    logging.critical("--- loading v6")
    fmt = FORMAT_V6
    parent_level = fmt.root
    limits = LoadLimits()
    upgrade = (6, HDF5_FILE_VERSION)

    with externals.pandas.HDFStore(filename) as store:
        data, meta_table = create_initial_data_set_from_cellpy_file(
            fmt.common_meta_dir, parent_level, store
        )
        cellpy_file_keys.check_keys_in_cellpy_file(
            fmt.common_meta_dir,
            parent_level,
            fmt.raw_dir,
            store,
            fmt.summary_dir,
        )
        limits = extract_summary_from_cellpy_file(
            data,
            parent_level,
            store,
            fmt.summary_dir,
            selector=selector,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        extract_raw_from_cellpy_file(
            data,
            parent_level,
            fmt.raw_dir,
            store,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        extract_steps_from_cellpy_file(
            data, parent_level, fmt.step_dir, store, limits=limits
        )
        fid_table, fid_table_selected = extract_fids_from_cellpy_file(
            fmt.fid_dir, parent_level, store
        )

    extract_meta_from_old_cellpy_file_max_v7(
        data, meta_table, filename, upgrade_from_to=upgrade
    )
    _assign_fids_from_table(data, fid_table, fid_table_selected)
    logging.debug("loaded new test")
    return data, limits


def load_v5(filename, selector=None) -> tuple["Data", LoadLimits]:
    logging.critical("--- loading v5")
    fmt = FORMAT_V5
    parent_level = fmt.root
    limits = LoadLimits()
    upgrade = (5, HDF5_FILE_VERSION)

    with externals.pandas.HDFStore(filename) as store:
        data, meta_table = create_initial_data_set_from_cellpy_file(
            fmt.common_meta_dir, parent_level, store
        )
        cellpy_file_keys.check_keys_in_cellpy_file(
            fmt.common_meta_dir,
            parent_level,
            fmt.raw_dir,
            store,
            fmt.summary_dir,
        )
        limits = extract_summary_from_cellpy_file(
            data,
            parent_level,
            store,
            fmt.summary_dir,
            selector=selector,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        extract_raw_from_cellpy_file(
            data,
            parent_level,
            fmt.raw_dir,
            store,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        extract_steps_from_cellpy_file(
            data, parent_level, fmt.step_dir, store, limits=limits
        )
        fid_table, fid_table_selected = extract_fids_from_cellpy_file(
            fmt.fid_dir, parent_level, store
        )

    extract_meta_from_old_cellpy_file_max_v7(
        data, meta_table, filename, upgrade_from_to=upgrade
    )
    _assign_fids_from_table(data, fid_table, fid_table_selected)
    logging.debug("loaded new test")
    return data, limits


def load_v3_to_v4(filename, selector=None) -> tuple["Data", LoadLimits]:
    logging.critical("--- loading v < 5")
    fmt = FORMAT_V4
    parent_level = fmt.root
    limits = LoadLimits()
    upgrade = (4, HDF5_FILE_VERSION)

    with externals.pandas.HDFStore(filename) as store:
        data, meta_table = create_initial_data_set_from_cellpy_file(
            fmt.common_meta_dir, parent_level, store
        )
        cellpy_file_keys.check_keys_in_cellpy_file(
            fmt.common_meta_dir,
            parent_level,
            fmt.raw_dir,
            store,
            fmt.summary_dir,
        )
        limits = extract_summary_from_cellpy_file(
            data,
            parent_level,
            store,
            fmt.summary_dir,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        extract_raw_from_cellpy_file(
            data,
            parent_level,
            fmt.raw_dir,
            store,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        extract_steps_from_cellpy_file(
            data,
            parent_level,
            fmt.step_dir,
            store,
            limits=limits,
            upgrade_from_to=upgrade,
        )
        fid_table, fid_table_selected = extract_fids_from_cellpy_file(
            fmt.fid_dir, parent_level, store
        )

    extract_meta_from_old_cellpy_file_max_v7(
        data, meta_table, filename, upgrade_from_to=upgrade
    )
    warnings.warn("Loaded old cellpy-file version (<5). Please update and save again.")
    _assign_fids_from_table(data, fid_table, fid_table_selected)
    return data, limits


_LEGACY_READERS = {
    5: load_v5,
    6: load_v6,
    7: load_v7,
}


def load_legacy(
    filename, cellpy_file_version: int, selector=None
) -> tuple["Data", LoadLimits]:
    if cellpy_file_version < 5:
        return load_v3_to_v4(filename, selector=selector)
    if cellpy_file_version in _LEGACY_READERS:
        return _LEGACY_READERS[cellpy_file_version](filename, selector=selector)
    raise WrongFileVersion(f"version {cellpy_file_version} is not supported")
