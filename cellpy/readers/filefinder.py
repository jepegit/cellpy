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


def search_for_files(
    run_name,
    raw_extension=None,
    cellpy_file_extension=None,
    raw_file_dir=None,
    cellpy_file_dir=None,
    prm_filename=None,
    file_name_format=None,
    reg_exp=None,
    sub_folders=False,
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
           sub_folders (bool): perform search also in sub-folders.

       Returns:
           run-file names (list) and cellpy-file-name (path).
       """

    # TODO: @jepe - use reg_exp
    # TODO: @jepe - allow for searching in cloud
    # TODO: @jepe - how to implement searching in db?
    # TODO: update prms and conf file to allow for setting if search should be done in
    #  sub-folders, several folders, db, cloud etc
    version = 0.2
    t0 = time.time()

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

    logging.debug(f"searching for raw files in: {raw_file_dir}")
    logging.debug(f"searching for {run_name}")
    logging.debug(f"using glob {glob_text_raw}")

    cellpy_file = f"{run_name}{cellpy_file_extension}"
    cellpy_file = cellpy_file_dir / cellpy_file

    logging.debug(f"generated cellpy filename {cellpy_file}")

    run_files = []
    for d in raw_file_dir:
        if not d.is_dir():
            warnings.warn("your raw file directory cannot be accessed!")
            # raise cellpy.exceptions.IOError("your raw file directory cannot be accessed!")
            _run_files = []
        else:
            logging.debug(f"checking in folder {d}")

            if sub_folders:
                _run_files = d.rglob(glob_text_raw)

            else:
                _run_files = d.glob(glob_text_raw)

            _run_files = [str(f.resolve()) for f in _run_files]
            # TODO: check that db reader can accept pathlib.Path objects (and fix the tests)
            # _run_files = [f.resolve() for f in _run_files]
            _run_files.sort()
        run_files.extend(_run_files)

    return run_files, cellpy_file


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
