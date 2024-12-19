# -*- coding: utf-8 -*-

import fnmatch
import glob
import logging
import os
import pathlib
import sys
import time
from typing import Optional, Union, List, Tuple
import warnings

from . import externals as externals
import cellpy.exceptions
from cellpy.parameters import prms
from cellpy.internals.core import OtherPath


# TODO: @jepe - add function for dumping the raw-file directory to a file,
#   for example an sqlite db or a json file,
#   and add function for reading and searching in the dumped file

# TODO: @jepe - add function for searching in cloud storage (dropbox, google drive etc)
# TODO: @jepe - add function for searching in database (sqlite, postgresql etc)
# TODO: @jepe - allow for providing a glob pattern also when using file_list by editing the batch.py script


def find_in_raw_file_directory(
    raw_file_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    project_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    extension: Optional[str] = None,
    glob_txt: Optional[str] = None,
    allow_error_level: Optional[int] = 3,
):
    """Dumps the raw-file directory to a list.

    Args:
        raw_file_dir(path): optional, directory where to look for run-files
            (default: read prm-file)
        project_dir(path): optional, subdirectory in raw_file_dir to look for run-files
        extension (str): optional, extension of run-files (without the '.'). If
            not given, all files will be listed.
        glob_txt (str, optional): optional, glob pattern to use when searching for files.
        allow_error_level (int, optional): accept errors up to this level when using the find command Defaults to 3.
            (1 raises Exception, 2 skips, 3 tries to process the stdout regardless).

    Returns:
        list of str: list of file paths.

    Examples:
        >>> # find all files in your raw-file directory:
        >>> filelist_1 = filefinder.find_in_raw_file_directory()

        >>> # find all files in your raw-file directory in the subdirectory 'MY-PROJECT':
        >>> filelist_2 = filefinder.find_in_raw_file_directory(raw_file_dir=rawdatadir/"MY-PROJECT")

        >>> # find all files in your raw-file directory with the extension '.raw' in the subdirectory 'MY-PROJECT':
        >>> filelist_3 = filefinder.find_in_raw_file_directory(raw_file_dir=rawdatadir/"MY-PROJECT", extension="raw")

        >>> # find all files in your raw-file directory with the extension '.raw' in the subdirectory 'MY-PROJECT'
        >>> # that contains the string 'good' in the file name
        >>> filelist_4 = filefinder.find_in_raw_file_directory(
        >>>     raw_file_dir=rawdatadir/"MY-PROJECT",
        >>>     glob_txt="*good*",
        >>>     extension="raw"
        >>>)

    Notes:
        Uses 'find' and 'ssh' to search for files.
    """

    logging.info("--- EXPERIMENTAL ---")
    logging.info("This function uses 'find' and 'ssh' to search for files.")
    logging.info("Not all systems have these commands available.")

    file_list = []

    if raw_file_dir is None:
        raw_file_dir = prms.Paths.rawdatadir

    # 'dressing' the raw_file_dir in a list in case we want to
    # search in several folders (not implemented yet):
    if not isinstance(raw_file_dir, (list, tuple)):
        raw_file_dir = [OtherPath(raw_file_dir)]
    else:
        raw_file_dir = [OtherPath(d) for d in raw_file_dir]

    if project_dir is not None:
        raw_file_dir = [r / project_dir for r in raw_file_dir]

    if glob_txt is None:
        glob_txt = "*"  # all files

    if extension is not None:
        if extension.startswith("."):
            glob_txt = f"{glob_txt}{extension}"
        else:
            glob_txt = f"{glob_txt}.{extension}"

    platform = sys.platform
    logging.info(f"Searching for files matching: {glob_txt}")
    for d in raw_file_dir:
        connect_kwargs, host = d.connection_info()
        if not host and platform == "win32":
            logging.info("Windows platform detected - assuming 'find' is not available")
            _file_list = glob.glob(f"{d.raw_path}/**/{glob_txt}", recursive=True)
            f = _file_list[0]
        else:
            # TODO: make a better error-message if the d.raw_path does not exist:
            with externals.fabric.Connection(host, connect_kwargs=connect_kwargs) as conn:
                find_command = f'find -L {d.raw_path} -name "{glob_txt}"'
                out = conn.run(f"{find_command}", hide="both", warn=True)
            if out.return_code != 0:
                logging.critical(f"Errors encounter when running the find command in {d.raw_path}")
                logging.debug(f"{find_command} -> {out.stderr}")
                if allow_error_level == 1:
                    raise cellpy.exceptions.SearchError(
                        f"Following errors encounter when running the find command in ({d.raw_path}) ->\n{out.stderr}"
                    )
                elif allow_error_level == 2:
                    logging.critical("Skipping this folder")
                    continue
                elif allow_error_level == 3:
                    logging.critical("Trying to process the stdout regardless")

            _file_list = out.stdout.splitlines()

        file_list += list(map(lambda x: f"{d.uri_prefix}{host}" + x, _file_list))
    number_of_files = len(file_list)
    if number_of_files == 0:
        logging.critical("No files found")
    logging.info(f"Found {number_of_files} files")
    return file_list


def list_raw_file_directory(
    raw_file_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    project_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    extension: Optional[str] = None,
    levels: Optional[int] = 1,
    only_filename: Optional[bool] = False,
    with_prefix: Optional[bool] = True,
):
    """Dumps the raw-file directory to a list.

    Args:
        raw_file_dir(path): optional, directory where to look for run-files
            (default: read prm-file)
        project_dir(path): optional, subdirectory in raw_file_dir to look for run-files
        extension (str): optional, extension of run-files (without the '.'). If
            not given, all files will be listed.
        levels (int, optional): How many sublevels to list. Defaults to 1.
            If you want to list all sublevels, use `listdir(levels=-1)`.
            If you want to list only the current level (no subdirectories),
            use `listdir(levels=0)`.
        only_filename (bool, optional): If True, only the file names will be
            returned. Defaults to False.
        with_prefix (bool, optional): If True, the full path to the files including
            the prefix and the location (e.g. 'scp://user@server.com/...')
            will be returned. Defaults to True.

    Returns:
        list of str: list of file paths (only the actual file names).

    Notes:
        This function might be rather slow and memory consuming if you have
        a lot of files in your raw-file directory. If you have a lot of files,
        you might want to consider running this function in a separate process
        (e.g. in a separate python script or using multiprocessing).

        The function currently returns the full path to the files from the
        root directory. It does not include the prefix (e.g. ssh://).
        Future versions might change this to either include the prefix or
        return the files relative to the ``raw_file_dir`` directory.
    """

    file_list = []

    if raw_file_dir is None:
        raw_file_dir = prms.Paths.rawdatadir

    # 'dressing' the raw_file_dir in a list in case we want to
    # search in several folders (not implemented yet):
    if not isinstance(raw_file_dir, (list, tuple)):
        raw_file_dir = [OtherPath(raw_file_dir)]
    else:
        raw_file_dir = [OtherPath(d) for d in raw_file_dir]

    if project_dir is not None:
        raw_file_dir = [r / project_dir for r in raw_file_dir]

    for d in raw_file_dir:
        _file_list = d.listdir(levels=levels)
        if extension is not None:
            logging.debug(f"filtering for extension: {extension}")
            _file_list = fnmatch.filter(_file_list, f"*.{extension}")
        if only_filename:
            logging.debug("only returning the file names")
            _file_list = [f.name for f in _file_list]
        elif with_prefix:
            logging.debug("adding prefix to file names")
            logging.debug(f"{d.pathlike_location=}")
            _file_list = [d.pathlike_location / f for f in _file_list]

        file_list.extend(_file_list)

    return file_list


def search_for_files(
    run_name: str,
    raw_extension: Optional[str] = None,
    cellpy_file_extension: Optional[str] = None,
    raw_file_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    project_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    cellpy_file_dir: Union[OtherPath, pathlib.Path, str, None] = None,
    prm_filename: Union[pathlib.Path, str, None] = None,
    file_name_format: Optional[str] = None,
    reg_exp: Optional[str] = None,
    sub_folders: Optional[bool] = True,
    file_list: Optional[List[str]] = None,
    with_prefix: Optional[bool] = True,
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
        project_dir(path): optional, subdirectory in raw_file_dir to look for run-files
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
        with_prefix (bool): if True, the file list contains full paths to the
            files (including the prefix and the location).
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
    version = 0.4
    t0 = time.time()

    if reg_exp is None:
        reg_exp = prms.FileNames.reg_exp

    if raw_extension is None:
        raw_extension = prms.FileNames.raw_extension

    if raw_extension is None:
        raw_extension = prms.FileNames.raw_extension

    if cellpy_file_extension is None:
        cellpy_file_extension = prms.FileNames.cellpy_file_extension

    # backward compatibility check:
    if cellpy_file_extension.startswith("."):
        warnings.warn("Deprecation warning: cellpy_file_extension should not include the '.'")
        cellpy_file_extension = cellpy_file_extension[1:]

    if raw_file_dir is None:
        raw_file_dir = prms.Paths.rawdatadir

    if file_name_format is None:
        file_name_format = prms.FileNames.file_name_format

    # 'dressing' the raw_file_dir in a list in case we want to
    # search in several folders (not implemented yet):
    if not isinstance(raw_file_dir, (list, tuple)):
        raw_file_dir = [OtherPath(raw_file_dir)]
    else:
        raw_file_dir = [OtherPath(d) for d in raw_file_dir]

    if project_dir is not None:
        raw_file_dir = [r / project_dir for r in raw_file_dir]

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
            warnings.warn("Deprecation warning: raw_extension should not include the '.'")
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

        if with_prefix:
            glob_text_raw_for_list = f"*{glob_text_raw}"
        else:
            glob_text_raw_for_list = glob_text_raw

        run_files = fnmatch.filter(file_list, glob_text_raw_for_list)

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


def _check_01():
    import dotenv
    from cellpy import log

    log.setup_logging(default_level="DEBUG")
    dotenv.load_dotenv(r"C:\scripting\cellpy\local\.env_cellpy_local")
    print("searching for files")
    my_run_name = "20160805_test001_45_cc"
    # my_run_name = "20210218_Seam08_02_01_cc"
    my_raw_file_dir = OtherPath(f"scp://{os.getenv('CELLPY_HOST')}/home/{os.getenv('CELLPY_USER')}/tmp/")
    # my_raw_file_dir = OtherPath(r"C:\scripting\processing_cellpy\raw")
    my_cellpy_file_dir = OtherPath("C:/scripting/processing_cellpy/data/")
    f = search_for_files(my_run_name, raw_file_dir=my_raw_file_dir, cellpy_file_dir=my_cellpy_file_dir)
    print(f)
    #
    # print(my_raw_file_dir)
    # print(my_raw_file_dir.is_dir())
    # print(my_raw_file_dir.raw_path)


def _check_02():
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
        sub_dirs = [f for f in sftp_conn.listdir() if stat.S_ISDIR(sftp_conn.stat(f).st_mode)]
        files = [f for f in sftp_conn.listdir() if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)]
        filtered_files = fnmatch.filter(files, glob_str)
        for sub_dir in sub_dirs:
            sftp_conn.chdir(sub_dir)
            new_files = [f for f in sftp_conn.listdir() if not stat.S_ISDIR(sftp_conn.stat(f).st_mode)]
            new_filtered_files = fnmatch.filter(new_files, glob_str)
            new_filtered_files = [f"{sub_dir}{path_separator}{f}" for f in new_filtered_files]
            filtered_files += new_filtered_files
            sftp_conn.chdir("..")

        for f in filtered_files:
            print(f"file: {f} of type {type(f)}")


def _check_03():
    from cellpy import prms
    from pprint import pprint

    prms.Paths.rawdatadir = r"C:\scripting\processing_cellpy\raw"
    file_list = list_raw_file_directory(
        raw_file_dir=None,
        project_dir=None,
        extension="res",
    )
    for f in file_list:
        print(f"{f} type: {type(f)} path: {f.full_path}")


if __name__ == "__main__":
    _check_03()
