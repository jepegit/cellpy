import logging
import os
import time
import pandas as pd

import csv
import itertools

from cellpy import prms
from cellpy import cellreader, dbreader, filefinder
from cellpy.exceptions import ExportFailed, NullData

logger = logging.getLogger(__name__)


def look_up_and_get(cellpy_file_name, table_name):
    """extracts table from cellpy hdf5-file"""

    print(f"\nTrying to run 'look_up_and_get(cellpy_file_name, table_name)'")
    print(f"with prms {cellpy_file_name}, {table_name}")
    print("OH-NO!!!!!!!!! -> 'look_up_and_get' is not made yet!")


def create_folder_structure(project_name, batch_name):
    """This function creates a folder structure for the batch project.

    The folder structure consists of main working folder ``project_name`
    located in the ``outdatadir`` (as defined in the cellpy configuration file)
    with a sub-folder named ``batch_name``. It also creates a folder
    inside the ``batch_name`` folder for storing the raw data.
    If the folders does not exist, they will be made. The function also returns
    the name of the info-df.

    Args:
        project_name: name of the project
        batch_name: name of the batch

    Returns: (info_file, (project_dir, batch_dir, raw_dir))

    """
    out_data_dir = prms.Paths["outdatadir"]
    project_dir = os.path.join(out_data_dir, project_name)
    batch_dir = os.path.join(project_dir, batch_name)
    raw_dir = os.path.join(batch_dir, "raw_data")

    # create folders
    if not os.path.isdir(project_dir):
        os.mkdir(project_dir)
    if not os.path.isdir(batch_dir):
        os.mkdir(batch_dir)
    if not os.path.isdir(raw_dir):
        os.mkdir(raw_dir)

    # create file-name for the info_df (json)
    info_file = "cellpy_batch_%s.json" % batch_name
    info_file = os.path.join(project_dir, info_file)
    return info_file, (project_dir, batch_dir, raw_dir)


def find_files(info_dict, filename_cache=None):
    # searches for the raw data files and the cellpyfile-name
    for run_name in info_dict["filenames"]:
        if prms._use_filename_cache:
            raw_files, cellpyfile, filename_cache = filefinder.search_for_files(run_name, cache=filename_cache)
        else:
            raw_files, cellpyfile = filefinder.search_for_files(run_name)
        if not raw_files:
            raw_files = None
        info_dict["raw_file_names"].append(raw_files)
        info_dict["cellpy_file_names"].append(cellpyfile)

    return info_dict


def fix_groups(groups):
    _groups = []
    for g in groups:
        if not float(g) > 0:
            _groups.append(1000)
        else:
            _groups.append(int(g))
    return _groups


def save_multi(data, file_name, sep=";"):
    """convenience function for storing data column-wise in a csv-file."""
    logger.debug("saving multi")
    with open(file_name, "w", newline='') as f:
        logger.debug(f"{file_name} opened")
        writer = csv.writer(f, delimiter=sep)
        try:
            writer.writerows(itertools.zip_longest(*data))
        except Exception as e:
            logger.info(f"Exception encountered in batch._save_multi: {e}")
            raise ExportFailed
        logger.debug("wrote rows using itertools in _save_multi")


def make_unique_groups(info_df):
    # fixes group numbering
    unique_g = info_df.groups.unique()
    unique_g = sorted(unique_g)
    new_unique_g = list(range(len(unique_g)))
    info_df["sub_groups"] = info_df["groups"] * 0
    for i, j in zip(unique_g, new_unique_g):
        counter = 1
        for indx, row in info_df.loc[info_df.groups == i].iterrows():
            info_df.at[indx, "sub_groups"] = counter
            # info_df.set_value(indx, "sub_groups", counter)
            counter += 1
        info_df.loc[info_df.groups == i, 'groups'] = j + 1
    return info_df


def _remove_date(label):
    _ = label.split("_")
    return _[1] + "_" + _[2]


def create_labels(label, *args):
    """Returns a re-formatted label (currently it only removes the dates
    from the run-name)"""
    return _remove_date(label)
