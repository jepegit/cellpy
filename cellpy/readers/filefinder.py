# -*- coding: utf-8 -*-

import os
import glob
import warnings
# from cellpy.parameters import prmreader
import cellpy.parameters.prms as prms
import logging
logger = logging.getLogger(__name__)

def search_for_files(run_name, raw_extension=None, cellpy_file_extension=None,
                     raw_file_dir=None, cellpy_file_dir=None, prm_filename = None,
                     file_name_format=None):
    """Searches for files (raw-data files and cellpy-files).


    Args:
        run_name(str): run-file identification.
        raw_extension(str): optional, extension of run-files (without the '.').
        cellpy_file_extension(str): optional, extension for cellpy files (without the '.').
        raw_file_dir(path): optional, directory where to look for run-files (default: read prm-file)
        cellpy_file_dir(path): optional, directory where to look for cellpy-files
                              (default: read prm-file)
        prm_filename(path): optional parameter file can be given.
        file_name_format(str): format of raw-file names or a glob pattern
                               (default: YYYYMMDD_[name]EEE_CC_TT_RR).

    Returns:
        run-file names (list) and cellpy-file-name (path).
    """

    cellpy_file_extension = "h5"
    res_extension = "res"
    version = 0.1
    # might include searching and removing "." in extensions
    # should include extension definitions in prm file (version 0.6)

    if raw_extension is None:
        raw_extension = res_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = cellpy_file_extension

    if prm_filename is not None:
        warnings.warn("reading prm file disabled")

    if not all([raw_file_dir,cellpy_file_dir,file_name_format]):
        #import cellpy.parameters.prms as prms
        # prms = prmreader.read()
        logger.info("using prms already set")

    if raw_file_dir is None:
        raw_file_dir = prms.Paths["rawdatadir"]

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.Paths["cellpydatadir"]

    if file_name_format is None:
        try:
            file_name_format = prms.file_name_format # To be implemented in version 0.5
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"
            if version >= 0.5:
                print "Could not read file_name_format from _cellpy_prms_xxx.conf."
                print "Using:"
                print "file_name_format:", file_name_format
                file_format_explanation = "YYYYMMDD is date, EEE is electrode number "
                file_format_explanation += "CC is cell number, TT is cell_type, RR is run number."
                print file_format_explanation

    # check if raw_file_dir exists
    if not os.path.isdir(raw_file_dir):
        warnings.warn("your raw file directory cannot be accessed!")

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        glob_text_raw = "%s_*.%s" % (os.path.basename(run_name),raw_extension)
    else:
        glob_text_raw = file_name_format

    glob_text_raw = os.path.join(raw_file_dir,glob_text_raw)
    run_files = glob.glob(glob_text_raw)

    #  run_files = glob.glob1(raw_file_dir,glob_text_raw)
    run_files.sort()
    cellpy_file = run_name + "." + cellpy_file_extension
    cellpy_file = os.path.join(cellpy_file_dir,cellpy_file)

    return run_files, cellpy_file


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
    print "searching for files"
    my_run_name = "20160805_test001_45_cc"
    my_raw_file_dir = os.path.abspath("../data_ex")
    my_cellpy_file_dir = os.path.abspath("../data_ex")
    search_for_files(my_run_name, raw_file_dir=my_raw_file_dir, cellpy_file_dir=my_cellpy_file_dir)
