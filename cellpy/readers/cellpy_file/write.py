"""Cellpy-file (HDF5) write path — infotable building and store persistence."""

from __future__ import annotations

import logging
import warnings
from dataclasses import asdict

from cellpy.parameters.internal_settings import PICKLE_PROTOCOL
from cellpy.readers.cellpy_file.format import CELLPY_FILE_VERSION, FORMAT_V8, CellpyFileFormat
from cellpy.readers import data_structures as ds
from cellpy.readers import externals
from cellpy.readers.cellpy_file import dtype as cellpy_file_dtype
from cellpy.readers.cellpy_file import fids as cellpy_file_fids

_module_logger = logging.getLogger(__name__)


def _headers_normal():
    from cellpy.parameters.internal_settings import get_headers_normal

    return get_headers_normal()


def create_infotable(data, fmt: CellpyFileFormat = FORMAT_V8):
    """Build common meta, test-dependent meta, and fid tables for saving."""
    new_info_table = asdict(data.meta_common)
    new_info_table_test_dependent = asdict(data.meta_test_dependent)
    new_info_table["cellpy_file_version"] = CELLPY_FILE_VERSION

    limits = data.raw_limits
    for key in limits:
        h5_key = f"{fmt.raw_limit_prefix}{key}"
        new_info_table[key] = limits[h5_key]

    units = data.raw_units
    for key in units:
        h5_key = f"{fmt.raw_unit_prefix}{key}"
        value = units[key]
        if not isinstance(value, str):
            raise IOError(
                f"raw unit for {key} ({value}) must be of type string, not {type(value)}"
            )
        new_info_table[h5_key] = value

    new_info_table = externals.pandas.DataFrame.from_records([new_info_table])
    new_info_table_test_dependent = externals.pandas.DataFrame.from_records(
        [new_info_table_test_dependent]
    )

    fidtable = cellpy_file_fids.convert2fid_table(data)
    fidtable = externals.pandas.DataFrame(fidtable)
    return new_info_table, new_info_table_test_dependent, fidtable


def save(data, path, *, format_spec: CellpyFileFormat = FORMAT_V8) -> None:
    """Write ``Data`` to a cellpy-file (HDF5) with a single owned store lifecycle."""
    fmt = format_spec
    common_meta_table, test_dependent_meta_table, fid_table = create_infotable(
        data, fmt=fmt
    )

    warnings.simplefilter("ignore", externals.pandas.errors.PerformanceWarning)
    try:
        with ds.pickle_protocol(PICKLE_PROTOCOL):
            with externals.pandas.HDFStore(
                path,
                complib=fmt.complib,
                complevel=fmt.complevel,
            ) as store:
                root = fmt.root
                logging.debug("trying to put raw data")
                logging.debug(" - lets set Data_Point as index")
                hdr_data_point = _headers_normal().data_point_txt
                if data.raw.index.name != hdr_data_point:
                    data.raw = data.raw.set_index(hdr_data_point, drop=False)
                store.put(root + fmt.raw_dir, data.raw, format=fmt.raw_format)
                logging.debug(" raw -> hdf5 OK")

                logging.debug("trying to put summary")
                store.put(
                    root + fmt.summary_dir,
                    data.summary,
                    format=fmt.summary_format,
                )
                logging.debug(" summary -> hdf5 OK")

                logging.debug("trying to put meta data")
                store.put(
                    root + fmt.common_meta_dir,
                    common_meta_table,
                    format=fmt.infotable_format,
                )
                logging.debug(" common meta -> hdf5 OK")
                store.put(
                    root + fmt.test_dependent_meta_dir,
                    test_dependent_meta_table,
                    format=fmt.infotable_format,
                )
                logging.debug(" test dependent meta -> hdf5 OK")

                logging.debug("trying to put fidtable")
                store.put(
                    root + fmt.fid_dir, fid_table, format=fmt.fidtable_format
                )
                logging.debug(" fid -> hdf5 OK")

                logging.debug("trying to put step")
                try:
                    store.put(
                        root + fmt.step_dir,
                        data.steps,
                        format=fmt.stepdata_format,
                    )
                    logging.debug(" step -> hdf5 OK")
                except TypeError:
                    cellpy_file_dtype.fix_dtype_step_table(data)
                    store.put(
                        root + fmt.step_dir,
                        data.steps,
                        format=fmt.stepdata_format,
                    )
                    logging.debug(" fixed step -> hdf5 OK")
    finally:
        warnings.simplefilter("default", externals.pandas.errors.PerformanceWarning)
