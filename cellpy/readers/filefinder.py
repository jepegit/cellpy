# -*- coding: utf-8 -*-

import os
import glob
import fnmatch
import pathlib
import warnings
import time

from cellpy.parameters import prms
import logging

logger = logging.getLogger(__name__)


def create_full_names(run_name, cellpy_file_extension=None,
                      raw_file_dir=None, cellpy_file_dir=None):
    cellpy_file_extension = "h5"

    if cellpy_file_extension is None:
        cellpy_file_extension = cellpy_file_extension

    if raw_file_dir is None:
        raw_file_dir = prms.Paths["rawdatadir"]

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.Paths["cellpydatadir"]

    raw_file = os.path.join(raw_file_dir, run_name)

    cellpy_file = run_name + "." + cellpy_file_extension
    cellpy_file = os.path.join(cellpy_file_dir, cellpy_file)

    return raw_file, cellpy_file


def search_for_files(run_name, raw_extension=None, cellpy_file_extension=None,
                     raw_file_dir=None, cellpy_file_dir=None, prm_filename=None,
                     file_name_format=None, cache=None):
    """Searches for files (raw-data files and cellpy-files).


    Args:
        run_name(str): run-file identification.
        raw_extension(str): optional, extension of run-files (without the '.').
        cellpy_file_extension(str): optional, extension for cellpy files
            (without the '.').
        raw_file_dir(path): optional, directory where to look for run-files
            (default: read prm-file)
        cellpy_file_dir(path): optional, directory where to look for
            cellpy-files (default: read prm-file)
        prm_filename(path): optional parameter file can be given.
        file_name_format(str): format of raw-file names or a glob pattern
            (default: YYYYMMDD_[name]EEE_CC_TT_RR).
        cache(list): list of cached file names to search through

    Returns:
        run-file names (list) and cellpy-file-name (path).
    """

    time_00 = time.time()
    cellpy_file_extension = "h5"
    res_extension = "res"
    version = 0.1
    # might include searching and removing "." in extensions
    # should include extension definitions in prm file (version 0.6)
    logger.debug(f"searching for {run_name}")
    if raw_extension is None:
        raw_extension = res_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = cellpy_file_extension

    if prm_filename is not None:
        logging.debug("reading prm file disabled")

    if not all([raw_file_dir, cellpy_file_dir, file_name_format]):
        # import cellpy.parameters.prms as prms
        # prms = prmreader.read()
        logger.debug("using prms already set")

    if raw_file_dir is None:
        raw_file_dir = prms.Paths["rawdatadir"]

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.Paths["cellpydatadir"]

    if file_name_format is None:
        try:
            # To be implemented in version 0.5:
            file_name_format = prms.file_name_format
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"
            if version >= 0.5:
                print("Could not read file_name_format "
                      "from _cellpy_prms_xxx.conf.")
                print("Using:")
                print("file_name_format:", file_name_format)
                file_format_explanation = "YYYYMMDD is date,"
                file_format_explanation += " EEE is electrode number"
                file_format_explanation += " CC is cell number,"
                file_format_explanation += " TT is cell_type, RR is run number."
                print(file_format_explanation)

    # check if raw_file_dir exists
    if not os.path.isdir(raw_file_dir):
        warnings.warn("your raw file directory cannot be accessed!")

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        glob_text_raw = "%s_*.%s" % (os.path.basename(run_name), raw_extension)
        reg_exp_raw = "xxx"
    else:
        glob_text_raw = file_name_format

    cellpy_file = "{0}.{1}".format(run_name, cellpy_file_extension)
    cellpy_file = os.path.join(cellpy_file_dir, cellpy_file)

    # TODO: @jepe - use pathlib

    if cache is None:

        use_pathlib_path = False
        return_as_str_list = True

        if use_pathlib_path:
            logger.debug("using pathlib.Path")
            if os.path.isdir(raw_file_dir):
                run_files = pathlib.Path(raw_file_dir).glob(glob_text_raw)
                if return_as_str_list:
                    run_files = [str(f.resolve()) for f in run_files]
                    run_files.sort()
            else:
                run_files = []

        else:
            if os.path.isdir(raw_file_dir):
                glob_text_raw_full = os.path.join(raw_file_dir, glob_text_raw)
                run_files = glob.glob(glob_text_raw_full)
                run_files.sort()
            else:
                run_files = []

        logger.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return run_files, cellpy_file

    else:
        logger.debug("using cache in filefinder")
        if os.path.isdir(raw_file_dir):
            if len(cache) == 0:
                cache = os.listdir(raw_file_dir)
            run_files = [
                os.path.join(
                    raw_file_dir, x
                ) for x in cache if fnmatch.fnmatch(
                    x, glob_text_raw
                )
            ]
            run_files.sort()
        else:
            run_files = []

        logger.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return run_files, cellpy_file, cache


def _find_resfiles(cellpyfile, raw_datadir, counter_min=1, counter_max=10):
    # function to find res files by locating all files of the form
    # (date-label)_(slurry-label)_(el-label)_(cell-type)_*
    # UNDER DEVELOPMENT

    counter_sep = "_"
    counter_digits = 2
    res_extension = ".res"
    res_dir = raw_datadir
    res_files = []
    cellpyfile = os.path.basename(cellpyfile)
    cellpyfile = os.path.splitext(cellpyfile)[0]
    for j in range(counter_min, counter_max + 1):
        look_for = "%s%s%s%s" % (cellpyfile, counter_sep,
                                 str(j).zfill(counter_digits),
                                 res_extension)

        look_for = os.path.join(res_dir, look_for)
        if os.path.isfile(look_for):
            res_files.append(look_for)

    return res_files


if __name__ == '__main__':
    print("searching for files")
    my_run_name = "20160805_test001_45_cc"
    my_raw_file_dir = os.path.abspath("../data_ex")
    my_cellpy_file_dir = os.path.abspath("../data_ex")
    search_for_files(my_run_name, raw_file_dir=my_raw_file_dir,
                     cellpy_file_dir=my_cellpy_file_dir)
