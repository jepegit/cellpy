# -*- coding: utf-8 -*-

default_prms = """
[Paths]
outdatadir: ..\outdata
rawdatadir: ..\indata
cellpydatadir: ..\indata
db_path: ..\databases
filelogdir: ..\databases

[FileNames]
db_filename: cellpy_db.xlsx
dbc_filename: cellpy_dbc.xlsx
"""

# [Instrument]
# instrument_type: arbin
# file_type: res

# [Experiment]
# cell_configuration: anode
# localvars: ife


# TODO (jepe): Should let cellpy read and store the prms on creation (optional)
# TODO (jepe): func for returning prm file name and location
# TODO (jepe): remove prm dbc_filename and logdir
# TODO (jepe): add prm db_type instead
# TODO (jepe): finish write_prm function


import glob
import os
import sys
from collections import OrderedDict
import configparser
import logging
import yaml

import cellpy.parameters.prms as prms

logger = logging.getLogger(__name__)

def _write_prm_file(file_name=None):
    logger.debug("saving configuration to %s" % file_name)
    config_dict = _pack_prms()
    with open(file_name, "w") as config_file:
        yaml.dump(config_dict, config_file, default_flow_style=False,explicit_start=True, explicit_end=True)

IS_DICT = True
def _update_prms(config_dict):
    logger.debug("updating parameters")
    logger.debug("new prms:" +str(config_dict))

    for key in config_dict:
        if hasattr(prms, key):
            _config_attr = getattr(prms, key)

            if IS_DICT: # TODO: use if isinstance(_config_attr, dict) or something similar
                for k in config_dict[key]:
                    _config_attr[k] = config_dict[key][k]
            else:
                setattr(_config_attr, config_dict[key])
        else:
            logger.info("\n  not-supported prm: %s" % key)


    # prms.Paths = config_dict["Paths"]
    #
    # config_dict = {
    #     "Paths": prms.Paths,
    #     "FileNames": prms.FileNames,
    #     "Db": prms.Db,
    #     "DataSet": prms.DataSet,
    #     "Reader": prms.Reader,
    #     "Instruments": prms.Instruments,
    #     "excel_db_cols": prms.excel_db_cols,
    #     "excel_db_filename_cols": prms.excel_db_filename_cols,
    # }



def _pack_prms():
    """if you introduce new 'save-able' parameter dictionaries, then you have to include them here"""
    config_dict = {
        "Paths": prms.Paths,
        "FileNames": prms.FileNames,
        "Db": prms.Db,
        "DataSet": prms.DataSet,
        "Reader": prms.Reader,
        "Instruments": prms.Instruments,
        "excel_db_cols": prms.excel_db_cols,
        "excel_db_filename_cols": prms.excel_db_filename_cols,
        "Batch": prms.Batch,
    }
    return config_dict



def _read_prm_file(prm_filename):
    """read the prm file"""
    logger.debug("Reading config-file: %s" % prm_filename)
    with open(prm_filename, "r") as config_file:
        prm_dict = yaml.load(config_file)
    _update_prms(prm_dict)


def __look_at(file_name):
    with open(file_name, "r") as config_file:
        t = yaml.load(config_file)
    print(t)

def _get_prm_file(file_name=None, search_order=None):
    """returns name of the prm file"""
    if file_name is not None:
        if os.path.isfile(file_name):
            return file_name
        else:
            logger.info("Could not find the prm-file")

    default_name = prms._prm_default_name
    prm_globtxt = prms._prm_globtxt

    script_dir = os.path.abspath(os.path.dirname(__file__))

    search_path = dict()
    search_path["curdir"] = os.path.abspath(os.path.dirname(sys.argv[0]))
    search_path["filedir"] = script_dir
    search_path["userdir"] = os.path.expanduser("~")

    if search_order is None:
        search_order = ["userdir",] # ["curdir","filedir", "userdir",]
    else:
        search_order = search_order


    # The default name for the prm file is at the moment in the script-dir, while
    # default searching is in the userdir (yes, I know):
    prm_default = os.path.join(script_dir, default_name)

    # -searching-----------------------
    search_dict = OrderedDict()

    for key in search_order:
        search_dict[key] = [None, None]
        prm_directory = search_path[key]
        default_file = os.path.join(prm_directory, default_name)

        if os.path.isfile(default_file):
            search_dict[key][0] = default_file

        prm_globtxt_full = os.path.join(prm_directory, prm_globtxt)

        user_files = glob.glob(prm_globtxt_full)

        for f in user_files:
            if os.path.basename(f) != os.path.basename(default_file):
                search_dict[key][1] = f
                break

    # -selecting----------------------
    prm_file = None
    for key, file_list in search_dict.items():
        if file_list[-1]:
            prm_file = file_list[-1]
            break
        else:
            if not prm_file:
                prm_file = file_list[0]

    if prm_file:
        prm_filename = prm_file
    else:
        prm_filename = prm_default

    return prm_filename





class read(object):
    """reads prm file for cellpy.

    To simplify usage, it is possible to store some commonly used parameters
    in a _cellpy_prms_some_name.ini file (some_name could be any string).

    Currently, the following options (and defaults) are supported::

        [Paths]
        outdatadir: ..\outdata
        rawdatadir: ..\indata
        cellpydatadir: ..\indata
        db_path: ..\databases
        filelogdir: ..\databases

        [FileNames]
        db_filename: cellpy_db.xlsx
        dbc_filename: cellpy_dbc.xlsx

    The prmreader looks for files with file names starting with _cellpy_prms
    and ending with .ini in the following directories::

        curdir, filedir, userdir

    in ascending priority. If it finds several files, the file
    _cellpy_prms_default.ini will have lowest priority.

    The search path can be altered by adjusting the search_order list.

    Args:
        prm_filename (str)(optional) : parameter file name
        search_order (list)(optional): list with paths to search in ascending priority
                                       (available options: ["curdir","filedir","userdir"]).
    """
    # should include more prms
    # file_name_format
    #
    def __init__(self, prm_filename=None, search_order=None):
        self.script_dir = os.path.abspath(os.path.dirname(__file__))

        self.search_path = dict()
        self.search_path["curdir"] = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.search_path["filedir"] = self.script_dir
        self.search_path["userdir"] = os.path.expanduser("~")

        if search_order is None:
            self.search_order = ["curdir", "filedir", "userdir"]
        else:
            self.search_order = search_order

        self.default_name = "_cellpy_prms_default.ini"
        self.prm_default = os.path.join(self.script_dir, self.default_name)
        self.prm_filename = prm_filename
        self.outdatadir = "..\outdata"
        self.rawdatadir = "..\indata"
        self.cellpydatadir = "..\indata"
        self.db_path = "..\databases"
        self.filelogdir = "..\databases"
        self.db_filename = "cellpy_db.xlsx"
        self.dbc_filename = "cellpy_db.xlsx"
        prm_globtxt = "_cellpy_prms*.ini"

        if prm_filename:
            self._readprms(prm_filename=self.prm_filename)
        else:
            search_dict = OrderedDict()

            for key in self.search_order:
                search_dict[key] = [None,None]
                prm_directory = self.search_path[key]
                default_file = os.path.join(prm_directory, self.default_name)
                if os.path.isfile(default_file):
                    search_dict[key][0] = default_file
                prm_globtxt_full = os.path.join(prm_directory, prm_globtxt)
                user_files = glob.glob(prm_globtxt_full)

                for f in user_files:
                    if os.path.basename(f) != os.path.basename(default_file):
                        search_dict[key][1] = f
                        break

            prm_file = None
            for key, file_list in search_dict.items():
                if file_list[-1]:
                    prm_file = file_list[-1]
                    break
                else:
                    if not prm_file:
                        prm_file = file_list[0]

            if prm_file:
                self.prm_filename = prm_file
            else:
                self.prm_filename = self.prm_default

            if not os.path.isfile(self.prm_filename):
                print("could not find ini-file")
                no_file = True
            else:
                no_file = False
            self._readprms(no_file=no_file)

    def __get(self, parser, opt, name, too):
        try:
            too = parser.get(opt, name)

        except configparser.NoOptionError as e:
            print("error", end=' ')
            print(e)

    def _readprms(self, prm_filename=None, no_file=False):
        if not prm_filename:
            prm_filename = self.prm_filename
        parser = configparser.SafeConfigParser()
        if no_file:
            import io
            parser.readfp(io.StringIO(default_prms))
        else:
            parser.read(prm_filename)

        opt = "Paths"
        try:
            self.outdatadir = parser.get(opt, "outdatadir")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)
        try:
            self.rawdatadir = parser.get(opt, "rawdatadir")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)
        try:
            self.cellpydatadir = parser.get(opt, "cellpydatadir")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)
        try:
            self.db_path = parser.get(opt, "db_path")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)
        try:
            self.filelogdir = parser.get(opt, "filelogdir")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)

        opt = "FileNames"
        try:
            self.db_filename = parser.get(opt, "db_filename")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)
        try:
            self.dbc_filename = parser.get(opt, "dbc_filename")
        except configparser.NoOptionError as e:
            print("prmreader.py:", end=' ')
            print(e)

    def _writeprms(self):
        print("prmreader.py: _writeprms is not implemented yet")

    def __str__(self):
        txt = ""
        txt += "prm-file:    \t%s\n" % self.prm_filename
        txt += "------------------------------------------------------------\n"
        txt += "NAME          \tVALUE\n"
        txt += "outdatadir:  \t%s\n" % self.outdatadir
        txt += "rawdatadir:  \t%s\n" % self.rawdatadir
        txt += "cellpydatadir: \t%s\n" % self.cellpydatadir
        txt += "db_path:     \t%s\n" % self.db_path
        txt += "filelogdir:  \t%s\n" % self.filelogdir

        txt += "db_filename: \t%s\n" % self.db_filename
        txt += "dbc_filename:\t%s\n" % self.dbc_filename
        txt += "------------------------------------------------------------\n"
        txt += "seach-path:\n"
        for p,v in list(self.search_path.items()):
            txt += "  %s:\t%s\n" % (p,v)
        return txt


def _save_current_prms_to_user_dir():
    # This should be put into the cellpy setup script
    file_name = os.path.join(prms.user_dir, prms._prm_default_name)
    _write_prm_file(file_name)

def main():
    print("Testing")
    #out = r"C:\Users\jepe\_cellpy_prms_jepe.conf"
    #_write_prm_file(out)
    print(prms.Reader)

    f = _get_prm_file()
    _write_prm_file(f)

    print(f)

    _read_prm_file(f)

    print(prms.Reader)


def old_main():
    r = read()  # TODO: remove this
    print("\n----------------------Read file-----------------------------")
    print("Search path:")
    for k, d in list(r.search_path.items()):
        print(k, d, end=' ')
        print(os.path.isdir(d))

    print("Prms:")
    print("------------------------------------------------------------")
    print(r)
    print("------------------------------------------------------------")

    errors = False
    if not os.path.isdir(r.db_path):
        print("Error! db_path not found")
        errors = True
    if not os.path.isdir(r.outdatadir):
        print("Error! outdatadir not found")
        errors = True
    if not os.path.isdir(r.rawdatadir):
        print("Error! rawdatadir not found")
        errors = True
    if not os.path.isdir(r.cellpydatadir):
        print("Error! cellpydatadir not found")
        errors = True
    if not os.path.isdir(r.filelogdir):
        print("Error! filelogdir not found")
        errors = True

    if not os.path.isfile(os.path.join(r.db_path, r.db_filename)):
        print("Error! db_filename not found")
        errors = True
    if not os.path.isfile(os.path.join(r.db_path, r.dbc_filename)):
        print("Error! dbc_filename not found")
        errors = True

    if errors is False:
        print("All ok")



if __name__ == "__main__":
    main()
