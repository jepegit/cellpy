"""FileID ↔ fid-table conversion for cellpy-files."""

from __future__ import annotations

import collections
import logging
import warnings

import cellpy.internals.connections as internals
from cellpy.readers import data_structures as ds


def convert2fid_table(cell):
    # used when saving cellpy-file
    logging.debug("converting FileID object to fid-table that can be saved")
    fidtable = collections.OrderedDict()
    fidtable["raw_data_name"] = []
    fidtable["raw_data_full_name"] = []
    fidtable["raw_data_size"] = []
    fidtable["raw_data_last_modified"] = []
    fidtable["raw_data_last_accessed"] = []
    fidtable["raw_data_last_info_changed"] = []
    fidtable["raw_data_location"] = []
    # TODO: consider deprecating this as we now have implemented last_data_point:
    fidtable["raw_data_files_length"] = []

    fidtable["last_data_point"] = []
    fids = cell.raw_data_files
    if fids:
        for fid, length in zip(fids, cell.raw_data_files_length):
            try:
                fidtable["raw_data_name"].append(fid.name)
                fidtable["raw_data_full_name"].append(fid.full_name)
                fidtable["raw_data_size"].append(fid.size)
                fidtable["raw_data_last_modified"].append(fid.last_modified)
                fidtable["raw_data_last_accessed"].append(fid.last_accessed)
                fidtable["raw_data_last_info_changed"].append(fid.last_info_changed)
            except AttributeError:  # TODO: this is probably not needed anymore
                logging.debug("this is probably not from a file")
                fidtable["raw_data_name"].append("db")
                fidtable["raw_data_full_name"].append("db")
                fidtable["raw_data_size"].append(fid.size)
                fidtable["raw_data_last_modified"].append("db")
                fidtable["raw_data_last_accessed"].append("db")
                fidtable["raw_data_last_info_changed"].append("db")

            fidtable["raw_data_location"].append(fid.location)
            fidtable["raw_data_files_length"].append(length)
            fidtable["last_data_point"].append(
                fid.last_data_point
            )  # will most likely be the same as length
    else:
        warnings.warn("seems you lost info about your raw-data (missing fids)")
    return fidtable


def convert2fid_list(tbl):
    # used when reading cellpy-file
    logging.debug("converting loaded fid-table to FileID object")
    fids = []
    lengths = []
    min_amount = 0
    for counter, item in enumerate(tbl["raw_data_name"]):
        fid = ds.FileID()
        try:
            fid.name = internals.OtherPath(item).name
        except NotImplementedError:
            fid.name = item
        fid.full_name = tbl["raw_data_full_name"][counter]
        fid.size = tbl["raw_data_size"][counter]
        fid.last_modified = tbl["raw_data_last_modified"][counter]
        fid.last_accessed = tbl["raw_data_last_accessed"][counter]
        fid.last_info_changed = tbl["raw_data_last_info_changed"][counter]
        fid.location = tbl["raw_data_location"][counter]
        length = tbl["raw_data_files_length"][counter]
        if "last_data_point" in tbl.columns:
            fid.last_data_point = tbl["last_data_point"][counter]
        else:
            fid.last_data_point = 0
        if "is_db" in tbl.columns:
            fid.is_db = tbl["is_db"][counter]
        fids.append(fid)
        lengths.append(length)
        min_amount = 1
    if min_amount < 1:
        logging.debug("info about raw files missing")
    return fids, lengths
