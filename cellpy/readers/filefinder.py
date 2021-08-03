# -*- coding: utf-8 -*-

import os
import glob
import fnmatch
import pathlib
import warnings
import time

from cellpy.parameters import prms
import cellpy.exceptions
import logging

# logger = logging.getLogger(__name__)


def create_full_names(
    run_name, cellpy_file_extension=None, raw_file_dir=None, cellpy_file_dir=None
):
    if cellpy_file_extension is None:
        cellpy_file_extension = "h5"

    if raw_file_dir is None:
        raw_file_dir = prms.Paths["rawdatadir"]

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.Paths["cellpydatadir"]

    raw_file = os.path.join(raw_file_dir, run_name)

    cellpy_file = run_name + "." + cellpy_file_extension
    cellpy_file = os.path.join(cellpy_file_dir, cellpy_file)

    return raw_file, cellpy_file


def _search_for_arbin_sql_csv_files(raw_file_dir=None):
    # 0) prms for testing/devel
    raw_file_dir = r"I:\Org\MPT-BAT-LAB\Processed\Experiments\seamless\Raw data"
    sub_dirs = True
    run_name = "*"

    # 1) define the (top) folder
    raw_file_dir = pathlib.Path(raw_file_dir)

    if not raw_file_dir.is_dir():
        warnings.warn("your raw file directory cannot be accessed!")
        raise cellpy.exceptions.IOError(f"Directory {raw_file_dir} does not exist.")

    glob_text_raw = f"*{run_name}*_Wb_1.csv"

    if sub_dirs:
        run_files = pathlib.Path(raw_file_dir).glob(glob_text_raw)
    else:
        run_files = pathlib.Path(raw_file_dir).rglob(glob_text_raw)

    run_files = [str(f.resolve()) for f in run_files]
    run_files.sort()

    return run_files


def _search_for_files_v2(
    run_name,
    raw_extension=None,
    cellpy_file_extension=None,
    raw_file_dir=None,
    cellpy_file_dir=None,
    prm_filename=None,
    file_name_format=None,
    reg_exp=None,
    sub_dirs=False,
):
    print(" RUNNING EXPERIMENTAL VERSION ".center(80, "-"))
    version = 0.2

    logging.debug(f"searching for {run_name}")

    if raw_file_dir is None:
        raw_file_dir = prms.Paths["rawdatadir"]

    if not isinstance(raw_file_dir, (list, tuple)):
        raw_file_dir = [pathlib.Path(raw_file_dir)]
    else:
        raw_file_dir = [pathlib.Path(d) for d in raw_file_dir]

    if reg_exp is not None:
        logging.warning("Sorry, but using reg exp is not implemented yet.")

    if raw_extension is None:
        raw_extension = ".res"

    if cellpy_file_extension is None:
        cellpy_file_extension = ".h5"

    if prm_filename is not None:
        logging.debug("reading prm file disabled")

    if cellpy_file_dir is None:
        cellpy_file_dir = pathlib.Path(prms.Paths["cellpydatadir"])
    else:
        cellpy_file_dir = pathlib.Path(cellpy_file_dir)

    if file_name_format is None and reg_exp is None:
        try:
            # To be implemented in version 0.5:
            file_name_format = prms.FileNames.file_name_format
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        # TODO: give warning/error-message if run_name contains more than one file (due to duplicate in db)
        glob_text_raw = f"{run_name}*{raw_extension}"
    else:
        glob_text_raw = file_name_format

    cellpy_file = f"{run_name}{cellpy_file_extension}"
    cellpy_file = cellpy_file_dir / cellpy_file

    run_files = []
    for d in raw_file_dir:
        if not d.is_dir():
            warnings.warn("your raw file directory cannot be accessed!")
            # raise cellpy.exceptions.IOError("your raw file directory cannot be accessed!")
            _run_files = []
        else:
            if sub_dirs:
                _run_files = d.rglob(glob_text_raw)
            else:
                _run_files = d.glob(glob_text_raw)
            _run_files = [str(f.resolve()) for f in run_files]
            _run_files.sort()
        run_files.extend(_run_files)

    return run_files, cellpy_file


def search_for_files(
    run_name,
    raw_extension=None,
    cellpy_file_extension=None,
    raw_file_dir=None,
    cellpy_file_dir=None,
    prm_filename=None,
    file_name_format=None,
    reg_exp=None,
    cache=None,
    sub_folders=False,
    experimental=False,
):
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
        reg_exp(str): use regular expression instead (defaults to None).
        cache(list): list of cached file names to search through.
        sub_folders (bool): x
        experimental (bool): use the experimental version (might crash)

    Returns:
        run-file names (list) and cellpy-file-name (path).
    """

    if experimental:
        return _search_for_files_v2(
            run_name,
            raw_extension=raw_extension,
            cellpy_file_extension=cellpy_file_extension,
            raw_file_dir=raw_file_dir,
            cellpy_file_dir=cellpy_file_dir,
            prm_filename=prm_filename,
            file_name_format=file_name_format,
            reg_exp=reg_exp,
            sub_folders=sub_folders,
        )

    # TODO: rename this and edit it so that it also can
    #  look up in db as well as do faster searching
    time_00 = time.time()
    default_extension = "res"
    version = 0.1
    # might include searching and removing "." in extensions
    # should include extension definitions in prm file (version 0.6)
    logging.debug(f"searching for {run_name}")

    if reg_exp is not None:
        logging.warning("Sorry, but using reg exp is not implemented yet.")

    if raw_extension is None:
        raw_extension = default_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = "h5"

    if prm_filename is not None:
        logging.debug("reading prm file disabled")

    if raw_file_dir is None:
        raw_file_dir = prms.Paths["rawdatadir"]

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.Paths["cellpydatadir"]

    if file_name_format is None and reg_exp is None:
        try:
            # To be implemented in version 0.5:
            file_name_format = prms.FileNames.file_name_format
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"
            if version >= 0.5:
                print("Could not read file_name_format from _cellpy_prms_xxx.conf.")
                print("Using:")
                print("file_name_format:", file_name_format)
                file_format_explanation = "YYYYMMDD is date,"
                file_format_explanation += " EEE is electrode number"
                file_format_explanation += " CC is cell number,"
                file_format_explanation += " TT is cell_type, RR is run number."
                print(file_format_explanation)

    if not os.path.isdir(raw_file_dir):
        warnings.warn(f"your raw file directory {raw_file_dir} cannot be accessed!")
        # raise cellpy.exceptions.IOError("your raw file directory cannot be accessed!")

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        # TODO: give warning/error-message if run_name contains more than one file (due to duplicate in db)
        glob_text_raw = "%s_*.%s" % (os.path.basename(run_name), raw_extension)

    elif file_name_format == "extended_path":
        # TODO: give warning/error-message if run_name contains more than one file (due to duplicate in db)
        glob_text_raw = "%s*%s" % (os.path.basename(run_name), raw_extension)

    else:
        glob_text_raw = file_name_format

    cellpy_file = f"{run_name}.{cellpy_file_extension}"
    cellpy_file = os.path.join(cellpy_file_dir, cellpy_file)

    # TODO: @jepe - use pathlib [muhammad 1]
    # TODO: @jepe - use reg_exp
    # TODO: @jepe - allow for searching in sub-folders [muhammad 2]
    # TODO: @jepe - allow for searching in cloud
    # TODO: @jepe - allow for searching in several folders
    # TODO: @jepe - how to implement searching in db?

    if cache is None:
        use_pathlib_path = False
        return_as_str_list = True
        run_files = _sub_search(
            glob_text_raw, raw_file_dir, return_as_str_list, use_pathlib_path
        )
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return run_files, cellpy_file

    else:
        cache, run_files = _sub_search_cashe(cache, glob_text_raw, raw_file_dir)
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return run_files, cellpy_file, cache


def _sub_search_cashe(cache, glob_text_raw, raw_file_dir):
    logging.debug("using cache in filefinder")
    warnings.warn("using chace is not updated yet")
    if os.path.isdir(raw_file_dir):
        if len(cache) == 0:
            cache = os.listdir(raw_file_dir)

        run_files = [
            os.path.join(raw_file_dir, x)
            for x in cache
            if fnmatch.fnmatch(x, glob_text_raw)
        ]
        run_files.sort()
    else:
        run_files = []
    return cache, run_files


def _sub_search(glob_text_raw, raw_file_dir, return_as_str_list, use_pathlib_path):
    print(glob_text_raw)
    if use_pathlib_path:
        logging.debug("using pathlib.Path")
        if os.path.isdir(raw_file_dir):
            run_files = pathlib.Path(raw_file_dir).glob(glob_text_raw)
            if return_as_str_list:
                run_files = [str(f.resolve()) for f in run_files]
                run_files.sort()
        else:
            run_files = []

    else:
        print("searching for files in")
        print(raw_file_dir)

        if os.path.isdir(raw_file_dir):
            glob_text_raw_full = os.path.join(raw_file_dir, glob_text_raw)
            run_files = glob.glob(glob_text_raw_full)
            print(run_files)
            run_files.sort()
        else:
            run_files = []

    return run_files


def _find_resfiles(cellpyfile, raw_datadir, counter_min=1, counter_max=10):
    # function to find res files by locating all files of the form
    # (date-label)_(slurry-label)_(el-label)_(cell-type)_*
    # NOT USED

    counter_sep = "_"
    counter_digits = 2
    res_extension = ".res"
    res_dir = raw_datadir
    res_files = []
    cellpyfile = os.path.basename(cellpyfile)
    cellpyfile = os.path.splitext(cellpyfile)[0]
    for j in range(counter_min, counter_max + 1):
        look_for = "%s%s%s%s" % (
            cellpyfile,
            counter_sep,
            str(j).zfill(counter_digits),
            res_extension,
        )

        look_for = os.path.join(res_dir, look_for)
        if os.path.isfile(look_for):
            res_files.append(look_for)

    return res_files


if __name__ == "__main__":
    print("searching for files")
    my_run_name = "20160805_test001_45_cc"
    my_raw_file_dir = os.path.abspath("../data_ex")
    my_cellpy_file_dir = os.path.abspath("../data_ex")
    search_for_files(
        my_run_name, raw_file_dir=my_raw_file_dir, cellpy_file_dir=my_cellpy_file_dir
    )
