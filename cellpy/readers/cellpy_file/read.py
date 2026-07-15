"""Cellpy-file (HDF5) read path — version gate, v8 reader, shared extractors."""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Union

from cellpy.exceptions import WrongFileVersion
from cellpy.parameters import prms
from cellpy.parameters.internal_settings import PICKLE_PROTOCOL
from cellpy.readers.cellpy_file.format import (
    CELLPY_FILE_VERSION,
    FORMAT_V8,
    MINIMUM_CELLPY_FILE_VERSION,
    CellpyFileFormat,
    get_format,
)
from cellpy.parameters.legacy.update_headers import (
    rename_fid_columns,
    rename_raw_columns,
    rename_step_columns,
    rename_summary_columns,
)
from cellpy.readers import data_structures as ds
from cellpy.readers import externals
from cellpy.readers.cellpy_file import fids as cellpy_file_fids
from cellpy.readers.cellpy_file import keys as cellpy_file_keys
from cellpy.readers.cellpy_file import meta as cellpy_file_meta
from cellpy.readers.cellpy_file.format import CellpyFileFormat
from cellpy.readers.cellpy_file.selectors import LoadLimits, LoadResult

if TYPE_CHECKING:
    from cellpy.readers.data_structures import Data

_module_logger = logging.getLogger(__name__)


def resolve_hdf5_path(path) -> str | Path:
    """Return a local path suitable for ``pd.HDFStore``, copying external files once."""
    import cellpy.internals.connections as internals

    other = path if isinstance(path, internals.OtherPath) else internals.OtherPath(path)
    if other.is_external:
        other = other.copy()
    return other


def _resolve_table_dir(table_name: str, fmt: CellpyFileFormat) -> str:
    """Map a v8-style table dir (e.g. ``prms._cellpyfile_step``) to ``fmt``'s layout."""
    mapping = {
        FORMAT_V8.step_dir: fmt.step_dir,
        FORMAT_V8.summary_dir: fmt.summary_dir,
        FORMAT_V8.raw_dir: fmt.raw_dir,
        FORMAT_V8.fid_dir: fmt.fid_dir,
        FORMAT_V8.common_meta_dir: fmt.common_meta_dir,
        FORMAT_V8.test_dependent_meta_dir: fmt.test_dependent_meta_dir,
    }
    return mapping.get(table_name, table_name)


def read_table(path, table_name: str, *, max_cycle: int | None = None):
    """Read a single table from a cellpy-file (batch link mode and similar)."""
    resolved = resolve_hdf5_path(path)
    version = cellpy_file_meta.get_cellpy_file_version(resolved)
    fmt = get_format(version)
    parent_level = fmt.root
    table_dir = _resolve_table_dir(table_name, fmt)
    store_key = parent_level + table_dir

    try:
        with externals.pandas.HDFStore(resolved) as store:
            if max_cycle is not None and table_dir == fmt.step_dir:
                data = ds.Data()
                limits = extract_summary_from_cellpy_file(
                    data,
                    parent_level,
                    store,
                    fmt.summary_dir,
                    selector={"max_cycle": max_cycle},
                )
                table = store.select(store_key)
                if limits.limit_data_points:
                    table = table.loc[
                        table["point_last"] <= limits.limit_data_points
                    ]
                return table
            return store.select(store_key)
    except KeyError as e:
        logging.warning("Could not read the table")
        raise WrongFileVersion(e) from e


def _headers_summary():
    from cellpy.parameters.internal_settings import get_headers_summary

    return get_headers_summary()


def hdf5_cycle_filter(table=None, limits: LoadLimits | None = None):
    if limits is None:
        limits = LoadLimits()
    if max_cycle := limits.limit_loaded_cycles:
        if table == "summary":
            logging.debug(f"limited to cycle_number {max_cycle}")
            return f"index <= {int(max_cycle)}"
        if table == "raw":
            logging.debug(f"limited to data_point {limits.limit_data_points}")
            return f"index <= {int(limits.limit_data_points)}"
        if table == "steps":
            logging.debug(f"limited to data_point {limits.limit_data_points}")
            return f"index <= {int(limits.limit_data_points)}"
    return None


def create_initial_data_set_from_cellpy_file(
    meta_dir, parent_level, store, test_dependent_meta_dir=None
):
    if test_dependent_meta_dir is not None:
        common_meta_table = store.select(parent_level + meta_dir)
        test_dependent_meta = store.select(parent_level + test_dependent_meta_dir)
        data = ds.Data()
        return data, common_meta_table, test_dependent_meta

    data = ds.Data()
    meta_table = None

    try:
        meta_table = store.select(parent_level + meta_dir)
    except KeyError as e:
        logging.info("This file is VERY old - no info given here")
        logging.info("You should convert the files to a newer version!")
        logging.debug(e)
        return data, meta_table

    try:
        meta_table.to_dict(orient="list")
    except Exception as e:
        warnings.warn(f"Unhandled exception raised: {e}")
        return data, meta_table

    return data, meta_table


def extract_summary_from_cellpy_file(
    data: "Data",
    parent_level: str,
    store: "externals.pandas.HDFStore",
    summary_dir: str,
    selector: Union[None, dict] = None,
    limits: LoadLimits | None = None,
    upgrade_from_to: tuple | None = None,
):
    if limits is None:
        limits = LoadLimits()
    if selector is not None:
        cycle_filter = []
        if max_cycle := selector.get("max_cycle", None):
            cycle_filter.append(f"index <= {int(max_cycle)}")
            limits.limit_loaded_cycles = max_cycle
    else:
        limits.limit_loaded_cycles = None
        cycle_filter = hdf5_cycle_filter("summary", limits)

    data.summary = store.select(parent_level + summary_dir, where=cycle_filter)
    if upgrade_from_to is not None:
        old, new = upgrade_from_to
        logging.debug(f"upgrading from {old} to {new}")
        data.summary = rename_summary_columns(data.summary, old, new)

    # Polars Phase A (#457): keys live in columns. The frozen v8 storage keeps
    # cycle_index as the stored index (the where-clauses above rely on it);
    # in memory it becomes a plain column.
    hdr_cycle = _headers_summary().cycle_index
    if data.summary.index.name == hdr_cycle:
        data.summary = data.summary.reset_index(
            drop=hdr_cycle in data.summary.columns
        )

    try:
        max_data_point = data.summary[_headers_summary().data_point].max()
    except KeyError as e:
        raise KeyError(
            "You are most likely trying to open a too old cellpy file"
        ) from e

    limits.limit_data_points = int(max_data_point)
    logging.debug(f"data-point max limit: {limits.limit_data_points}")
    return limits


def extract_raw_from_cellpy_file(
    data,
    parent_level,
    raw_dir,
    store,
    limits: LoadLimits | None = None,
    upgrade_from_to: tuple | None = None,
):
    if limits is None:
        limits = LoadLimits()
    cycle_filter = hdf5_cycle_filter(table="raw", limits=limits)
    data.raw = store.select(parent_level + raw_dir, where=cycle_filter)
    if upgrade_from_to is not None:
        old, new = upgrade_from_to
        logging.debug(f"upgrading from {old} to {new}")
        data.raw = rename_raw_columns(data.raw, old, new)

    # Polars Phase A (#457): keys live in columns. The frozen v8 storage keeps
    # data_point as the stored index (saved with drop=False, so the column is
    # also present); in memory the frame carries a plain RangeIndex.
    from cellpy.parameters.internal_settings import get_headers_normal

    hdr_data_point = get_headers_normal().data_point_txt
    if data.raw.index.name == hdr_data_point:
        data.raw = data.raw.reset_index(
            drop=hdr_data_point in data.raw.columns
        )


def extract_steps_from_cellpy_file(
    data,
    parent_level,
    step_dir,
    store,
    limits: LoadLimits | None = None,
    upgrade_from_to: tuple | None = None,
):
    if limits is None:
        limits = LoadLimits()
    try:
        data.steps = store.select(parent_level + step_dir)
        if limits.limit_data_points:
            data.steps = data.steps.loc[
                data.steps["point_last"] <= limits.limit_data_points
            ]
            logging.debug(f"limited to data_point {limits.limit_data_points}")
        if upgrade_from_to is not None:
            old, new = upgrade_from_to
            logging.debug(f"upgrading from {old} to {new}")
            data.steps = rename_step_columns(data.steps, old, new)
    except Exception as e:
        print(e)
        logging.debug("could not get steps from cellpy-file")
        data.steps = externals.pandas.DataFrame()
        warnings.warn(f"Unhandled exception raised: {e}")


def extract_fids_from_cellpy_file(
    fid_dir, parent_level, store, upgrade_from_to: tuple | None = None
):
    logging.debug(f"Extracting fid table from {fid_dir} in hdf5 store")
    try:
        fid_table = store.select(parent_level + fid_dir)
        fid_table_selected = True
        if upgrade_from_to is not None:
            old, new = upgrade_from_to
            logging.debug(f"upgrading from {old} to {new}")
            fid_table = rename_fid_columns(fid_table, old, new)
    except Exception as e:
        logging.debug(e)
        logging.debug("could not get fid from cellpy-file")
        fid_table = []
        warnings.warn("no fid_table - you should update your cellpy-file")
        fid_table_selected = False
    return fid_table, fid_table_selected


def extract_meta_from_cellpy_file(
    data: "Data",
    meta_table: "externals.pandas.DataFrame",
    test_dependent_meta_table: "externals.pandas.DataFrame",
    filename: Union[Path, str],
    upgrade_from_to: tuple | None = None,
) -> None:
    if upgrade_from_to is not None:
        old, new = upgrade_from_to
        print(f"upgrading meta from {old} to {new}")
        logging.debug(f"upgrading meta from {old} to {new}")

    data.loaded_from = str(filename)
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
            data.raw_units[key] = v[0]
        except KeyError:
            logging.critical(f"missing key in meta_table: {h5_key}")

    data.meta_common.update(as_list=False, **meta_dict)
    test_dependent_meta_dict = test_dependent_meta_table.to_dict(orient="list")
    data.meta_test_dependent.update(as_list=True, **test_dependent_meta_dict)


def _assign_fids_from_table(data: "Data", fid_table, fid_table_selected: bool) -> None:
    if fid_table_selected:
        data.raw_data_files, data.raw_data_files_length = cellpy_file_fids.convert2fid_list(
            fid_table
        )
    else:
        data.raw_data_files = []
        data.raw_data_files_length = []


def load_current_version(
    filename,
    selector=None,
    parent_level: str | None = None,
    fmt: CellpyFileFormat = FORMAT_V8,
) -> tuple["Data", LoadLimits]:
    if parent_level is None:
        parent_level = fmt.root

    logging.debug(f"filename: {filename}")
    logging.debug(f"selector: {selector}")
    limits = LoadLimits()
    with externals.pandas.HDFStore(filename) as store:
        (
            data,
            meta_table,
            test_dependent_meta_table,
        ) = create_initial_data_set_from_cellpy_file(
            fmt.common_meta_dir,
            parent_level,
            store,
            test_dependent_meta_dir=fmt.test_dependent_meta_dir,
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

    extract_meta_from_cellpy_file(
        data, meta_table, test_dependent_meta_table, filename
    )
    _assign_fids_from_table(data, fid_table, fid_table_selected)
    return data, limits


def load(
    filename,
    *,
    accept_old: bool = True,
    selector=None,
    parent_level: str | None = None,
) -> LoadResult:
    """Load a cellpy-file and return populated ``Data`` with explicit limits."""
    from cellpy.readers.cellpy_file import legacy_read

    if parent_level is None:
        parent_level = prms._cellpyfile_root

    if parent_level != prms._cellpyfile_root:
        logging.debug(
            f"Using non-default parent label for the hdf-store: {parent_level}"
        )

    if not os.path.isfile(filename):
        logging.info(f"File does not exist: {filename}")
        raise IOError(f"File does not exist: {filename}")

    with ds.pickle_protocol(PICKLE_PROTOCOL):
        cellpy_file_version = cellpy_file_meta.get_cellpy_file_version(filename)
        logging.debug(
            f"Cellpy file version {cellpy_file_version}; selector={selector}"
        )

        if cellpy_file_version > CELLPY_FILE_VERSION:
            raise WrongFileVersion(
                f"File format too new: {filename} :: version: {cellpy_file_version}"
                f"Reload from raw or upgrade your cellpy!"
            )

        if cellpy_file_version < MINIMUM_CELLPY_FILE_VERSION:
            raise WrongFileVersion(
                f"File format too old: {filename} :: version: {cellpy_file_version}"
                f"Reload from raw or downgrade your cellpy!"
            )

        if cellpy_file_version < CELLPY_FILE_VERSION:
            if accept_old:
                logging.debug(f"old cellpy file version {cellpy_file_version}")
                logging.debug(f"filename: {filename}")
                logging.warning(
                    "Loading old file-type. It is recommended that you remake the step table and the "
                    "summary table."
                )
                data, limits = legacy_read.load_legacy(
                    filename, cellpy_file_version, selector=selector
                )
                logging.debug("loaded old file")
                logging.debug(data)
            else:
                raise WrongFileVersion(
                    f"File format too old: {filename} :: version: {cellpy_file_version}"
                    f"Try loading setting accept_old=True"
                )
        else:
            logging.debug(f"Loading {filename} :: v{cellpy_file_version}")
            data, limits = load_current_version(filename, selector=selector)

    return LoadResult.from_limits(data, cellpy_file_version, limits)
