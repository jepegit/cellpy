# -*- coding: utf-8 -*-

import os
import glob
from cellpy.parametres import prmreader


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

    hdf5_extension = "h5"
    res_extension = "res"

    # might include searching and removing "." in extensions
    # should include extension definitions in prm file

    if raw_extension is None:
        raw_extension = res_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = hdf5_extension

    if not all([raw_file_dir,cellpy_file_dir,file_name_format]):
        prms = prmreader.read(prm_filename)

    if raw_file_dir is None:
        raw_file_dir = prms.resdatadir

    if cellpy_file_dir is None:
        cellpy_file_dir = prms.hdf5datadir

    if file_name_format is None:
        try:
            file_name_format = prms.file_name_format
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"
            print "Could not read file_name_format from _cellpy_prms_xxx.ini."
            print "Using:"
            print "file_name_format:", file_name_format
            file_format_explanation = "YYYYMMDD is date, EEE is electrode number "
            file_format_explanation += "CC is cell number, TT is cell_type, RR is run number."
            print file_format_explanation

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        glob_text_raw = "%s_*.%s" % (os.path.basename(run_name),raw_extension)
    else:
        glob_text_raw = file_name_format

    run_files = glob.glob1(raw_file_dir,glob_text_raw)
    run_files.sort()
    cellpy_file = run_name + "." + cellpy_file_extension
    cellpy_file = os.path.join(cellpy_file_dir,cellpy_file)

    return run_files, cellpy_file


if __name__ == '__main__':
    print "searching for files"
    my_run_name = "20160805_test001_45_cc"
    my_raw_file_dir = os.path.abspath("../testdata")
    my_cellpy_file_dir = os.path.abspath("../testdata")
    search_for_files(my_run_name, raw_file_dir=my_raw_file_dir, cellpy_file_dir=my_cellpy_file_dir)
