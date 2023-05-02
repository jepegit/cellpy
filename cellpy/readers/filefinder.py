# -*- coding: utf-8 -*-

import fnmatch
import glob
import logging
import os
import pathlib
import time
from typing import Optional, Union, List, Tuple
import warnings

import cellpy.exceptions
from cellpy.parameters import prms
from cellpy.internals.core import OtherPath


def search_for_files(
    run_name: str,
    raw_extension: Optional[str] = None,
    cellpy_file_extension: Optional[str] = None,
    raw_file_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    cellpy_file_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    prm_filename: Union[pathlib.Path, str, None] = None,
    file_name_format: Optional[str] = None,
    reg_exp: Optional[str] = None,
    sub_folders: Optional[bool] = True,
    file_list: Optional[List[str]] = None,
    pre_path: Union[OtherPath, pathlib.Path, str, None] = None,
) -> Tuple[List[str], str]:
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
        file_list (list of str): perform the search within a given list
            of filenames instead of searching the folder(s). The list should
            not contain the full filepath (only the actual file names). If
            you want to provide the full path, you will have to modify the
            file_name_format or reg_exp accordingly.
        pre_path (path or str): path to prepend the list of files selected
             from the file_list.


    Returns:
        run-file names (list of strings) and cellpy-file-name (str of full path).
    """

    # TODO: @jepe - use reg_exp
    # TODO: @jepe - allow for searching in cloud
    # TODO: @jepe - how to implement searching in db?
    # TODO: update prms and conf file to allow for setting if search should be done in
    #  sub-folders, several folders, db, cloud etc
    # TODO: @jepe - find a way to implement automatic file_list creation in a top level func.
    logging.debug(f"searching for {run_name}")
    version = 0.3
    t0 = time.time()

    if reg_exp is None:
        reg_exp = prms.FileNames.reg_exp

    if raw_extension is None:
        raw_extension = prms.FileNames.raw_extension

    if raw_extension is None:
        raw_extension = prms.FileNames.raw_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = prms.FileNames.cellpy_file_extension

    # backward compatibility check
    if cellpy_file_extension.startswith("."):
        warnings.warn(
            "Deprecation warning: cellpy_file_extension should not include the '.'"
        )
        cellpy_file_extension = cellpy_file_extension[1:]

    if raw_file_dir is None:
        raw_file_dir = prms.Paths.rawdatadir

    logging.debug(f"2 {raw_file_dir=}")
    if file_name_format is None:
        file_name_format = prms.FileNames.file_name_format

    if not isinstance(raw_file_dir, (list, tuple)):
        raw_file_dir = [OtherPath(raw_file_dir)]
    else:
        raw_file_dir = [OtherPath(d) for d in raw_file_dir]

    if reg_exp:
        logging.warning(f"Got reg_exp: {reg_exp}")
        logging.warning("Sorry, but using reg exp is not implemented yet.")

    if prm_filename is not None:
        logging.debug("Sorry, reading prm file is not implemented yet.")

    if cellpy_file_dir is None:
        cellpy_file_dir = OtherPath(prms.Paths.cellpydatadir)
    else:
        cellpy_file_dir = OtherPath(cellpy_file_dir)

    if file_name_format is None and reg_exp is None:
        try:
            # To be implemented in version 0.5:
            file_name_format = prms.FileNames.file_name_format
        except AttributeError:
            file_name_format = "YYYYMMDD_[name]EEE_CC_TT_RR"

    if file_name_format.upper() == "YYYYMMDD_[NAME]EEE_CC_TT_RR":
        # backward compatibility check
        if raw_extension.startswith("."):
            warnings.warn(
                "Deprecation warning: raw_extension should not include the '.'"
            )
            raw_extension = raw_extension[1:]
            warnings.warn(f"Removing it -> {raw_extension}")
        # TODO: give warning/error-message if run_name contains more than one file (due to duplicate in db)
        glob_text_raw = f"{run_name}*.{raw_extension}"
    else:
        glob_text_raw = file_name_format

    logging.debug(f"searching for raw files in: {raw_file_dir}")
    logging.debug(f"searching for {run_name}")
    logging.debug(f"using glob {glob_text_raw}")

    cellpy_file = f"{run_name}.{cellpy_file_extension}"
    cellpy_file = cellpy_file_dir / cellpy_file
    # Not sure if for example pandas can handle OtherPath objects:
    cellpy_file = cellpy_file.full_path

    logging.debug(f"generated cellpy filename {cellpy_file}")

    if file_list is not None:
        if len(raw_file_dir) > 1:
            logging.info("you provided several raw file directories")
        logging.debug("searching within provided list of files")
        run_files = fnmatch.filter(file_list, glob_text_raw)
        if pre_path is not None:
            pre_path = OtherPath(pre_path)
            run_files = list(map(lambda x: pre_path / x, run_files))
    else:
        run_files = []
        for d in raw_file_dir:
            if d.is_external:
                logging.debug("external file")
            if not d.is_dir():
                warnings.warn("your raw file directory cannot be accessed!")
                # raise cellpy.exceptions.IOError("your raw file directory cannot be accessed!")
                _run_files = []
            else:
                logging.debug(f"checking in folder {d}")
                logging.debug(f"{sub_folders=}")
                if sub_folders:
                    _run_files = d.rglob(glob_text_raw)

                else:
                    _run_files = d.glob(glob_text_raw)

                _run_files = [str(_f.resolve()) for _f in _run_files]
                _run_files.sort()
            run_files.extend(_run_files)

    return run_files, cellpy_file


def check_01():
    import dotenv
    from cellpy import log

    log.setup_logging(default_level="DEBUG")
    dotenv.load_dotenv(r"C:\scripting\cellpy\local\.env_cellpy_local")
    print("searching for files")
    my_run_name = "20160805_test001_45_cc"
    # my_run_name = "20210218_Seam08_02_01_cc"
    my_raw_file_dir = OtherPath(
        f"scp://{os.getenv('CELLPY_HOST')}/home/{os.getenv('CELLPY_USER')}/tmp/"
    )
    # my_raw_file_dir = OtherPath(r"C:\scripting\processing_cellpy\raw")
    my_cellpy_file_dir = OtherPath("C:/scripting/processing_cellpy/data/")
    f = search_for_files(
        my_run_name, raw_file_dir=my_raw_file_dir, cellpy_file_dir=my_cellpy_file_dir
    )
    print(f)
    #
    # print(my_raw_file_dir)
    # print(my_raw_file_dir.is_dir())
    # print(my_raw_file_dir.raw_path)


def check_02():
    import dotenv
    import fabric
    import stat

    dotenv.load_dotenv(r"C:\scripting\cellpy\local\.env_cellpy_local")
    host = os.getenv("CELLPY_HOST")
    user = os.getenv("CELLPY_USER")
    key_file = os.getenv("CELLPY_KEY_FILENAME")
    print(f"host: {host}")
    print(f"user: {user}")
    connect_kwargs = {"key_filename": key_file}

    with fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
        sftp_conn = conn.sftp()
        sftp_conn.chdir("tmp")
        print("===================")
        for fileattr in sftp_conn.listdir_attr():
            if stat.S_ISDIR(fileattr.st_mode):
                print(f"dir: {fileattr.filename}")
            else:
                print(f"file: {fileattr.filename}")
        print("===================")
        glob_str = "20*.res"
        sub_dirs = [
            f for f in sftp_conn.listdir() if stat.S_ISDIR(sftp_conn.stat(f).st_mode)
        ]
        files = [
            f
            for f in sftp_conn.listdir()
            if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)
        ]
        filtered_files = fnmatch.filter(files, glob_str)
        for sub_dir in sub_dirs:
            sftp_conn.chdir(sub_dir)
            new_files = [
                f
                for f in sftp_conn.listdir()
                if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)
            ]
            new_filtered_files = fnmatch.filter(new_files, glob_str)
            new_filtered_files = [
                f"{sub_dir}{path_separator}{f}" for f in new_filtered_files
            ]
            filtered_files += new_filtered_files
            sftp_conn.chdir("..")

        for f in filtered_files:
            print(f"file: {f} of type {type(f)}")


if __name__ == "__main__":
    check_01()
