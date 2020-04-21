# -*- coding: utf-8 -*-

import glob
import os
import pathlib
import sys
from collections import OrderedDict
import getpass
import logging
import warnings

import box
from ruamel.yaml import YAML

from cellpy.parameters import prms
from cellpy.exceptions import ConfigFileNotRead, ConfigFileNotWritten

DEFAULT_FILENAME_START = ".cellpy_prms_"
DEFAULT_FILENAME_END = ".conf"

DEFAULT_FILENAME = DEFAULT_FILENAME_START + "default" + DEFAULT_FILENAME_END

# logger = logging.getLogger(__name__)

yaml = YAML()


def get_user_name():
    """get the user name of the current user (cross platform)"""
    return getpass.getuser()


def create_custom_init_filename(user_name=None):
    """creates a custom prms filename"""
    if user_name is None:
        return DEFAULT_FILENAME_START + get_user_name() + DEFAULT_FILENAME_END
    else:
        return DEFAULT_FILENAME_START + user_name + DEFAULT_FILENAME_END


def get_user_dir_and_dst(init_filename=None):
    """gets the name of the user directory and full prm filepath"""
    if init_filename is None:
        init_filename = create_custom_init_filename()
    user_dir = get_user_dir()
    dst_file = user_dir / init_filename
    return user_dir, dst_file


def get_user_dir():
    """gets the name of the user directory"""
    # user_dir = pathlib.Path(os.path.abspath(os.path.expanduser("~")))
    user_dir = pathlib.Path().home().resolve()
    if os.name == "nt":
        _user_dir = user_dir / "documents"
        if _user_dir.is_dir():
            user_dir = _user_dir
    return user_dir


def _write_prm_file(file_name=None):
    logging.debug("saving configuration to %s" % file_name)
    config_dict = _pack_prms()
    try:
        with open(file_name, "w") as config_file:
            yaml.allow_unicode = True
            yaml.default_flow_style = False
            yaml.explicit_start = True
            yaml.explicit_end = True
            yaml.dump(
                config_dict, config_file,
            )
    except yaml.YAMLError:
        raise ConfigFileNotWritten


def _update_prms(config_dict):
    logging.debug("updating parameters")
    logging.debug("new prms:" + str(config_dict))

    for key in config_dict:
        if hasattr(prms, key):
            _config_attr = getattr(prms, key)
            for k in config_dict[key]:
                _config_attr[k] = config_dict[key][k]
        else:
            logging.info("\n  not-supported prm: %s" % key)


def _pack_prms():
    """if you introduce new 'save-able' parameter dictionaries, then you have
    to include them here"""

    config_dict = {
        "Paths": prms.Paths.to_dict(),
        "FileNames": prms.FileNames.to_dict(),
        "Db": prms.Db.to_dict(),
        "DbCols": prms.DbCols.to_dict(),
        "DataSet": prms.DataSet.to_dict(),
        "Reader": prms.Reader.to_dict(),
        "Instruments": prms.Instruments.to_dict(),
        "Batch": prms.Batch.to_dict(),
    }
    return config_dict


def _read_prm_file(prm_filename):
    """read the prm file"""
    logging.debug("Reading config-file: %s" % prm_filename)
    try:
        with open(prm_filename, "r") as config_file:
            prm_dict = yaml.load(config_file)

    except yaml.YAMLError as e:
        raise ConfigFileNotRead from e
    else:
        _update_prms(prm_dict)


def _read_prm_file_without_updating(prm_filename):
    """read the prm file but do not update the params"""
    logging.debug("Reading config-file: %s" % prm_filename)
    try:
        with open(prm_filename, "r") as config_file:
            prm_dict = yaml.load(config_file)

    except yaml.YAMLError as e:
        raise ConfigFileNotRead from e
    return prm_dict


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
            logging.info("Could not find the prm-file")

    default_name = prms._prm_default_name
    prm_globtxt = prms._prm_globtxt

    script_dir = os.path.abspath(os.path.dirname(__file__))

    search_path = dict()
    search_path["curdir"] = os.path.abspath(os.path.dirname(sys.argv[0]))
    search_path["filedir"] = script_dir
    search_path["userdir"] = get_user_dir()

    if search_order is None:
        search_order = ["userdir"]  # ["curdir","filedir", "userdir",]
    else:
        search_order = search_order

    # The default name for the prm file is at the moment in the script-dir,@
    # while default searching is in the userdir (yes, I know):
    prm_default = os.path.join(script_dir, default_name)

    # -searching-----------------------
    search_dict = OrderedDict()

    for key in search_order:
        search_dict[key] = [None, None]
        prm_directory = search_path[key]
        default_file = os.path.join(prm_directory, default_name)

        if os.path.isfile(default_file):
            # noinspection PyTypeChecker
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


def _save_current_prms_to_user_dir():
    # This should be put into the cellpy setup script
    file_name = os.path.join(prms.user_dir, prms._prm_default_name)
    _write_prm_file(file_name)


def info():
    """this function will show only the 'box'-type
    attributes and their content in the cellpy.prms module"""
    print("convenience function for listing prms")
    print(type(prms))
    print(prms.__name__)
    print(f"prm file: {_get_prm_file()}")

    for key in prms.__dict__:
        if isinstance(prms.__dict__[key], box.Box):
            print()
            print(80 * "=")
            print(f"prms.{key}:")
            print(80 * "-")
            for subkey in prms.__dict__[key]:
                print(f"prms.{key}.{subkey} = ", f"{prms.__dict__[key][subkey]}")
            print(80 * "=")


def main():
    print("Testing")
    # out = r"C:\Users\jepe\_cellpy_prms_jepe.conf"
    # _write_prm_file(out)
    print(prms.Reader)

    f = _get_prm_file()
    _write_prm_file(f)

    print(f)

    _read_prm_file(f)

    print(prms.Reader)


if __name__ == "__main__":
    main()
