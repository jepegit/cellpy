# -*- coding: utf-8 -*-
import getpass
import glob
import logging
import os
import pathlib
import sys
import warnings
from collections import OrderedDict
from dataclasses import asdict, dataclass
from pprint import pprint

import box
import dotenv
import ruamel
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from cellpy.exceptions import ConfigFileNotRead, ConfigFileNotWritten
from cellpy.parameters import prms
from cellpy.parameters.internal_settings import OTHERPATHS
from cellpy.internals.core import OtherPath

DEFAULT_FILENAME_START = ".cellpy_prms_"
DEFAULT_FILENAME_END = ".conf"
USE_MY_DOCUMENTS = False

DEFAULT_FILENAME = DEFAULT_FILENAME_START + "default" + DEFAULT_FILENAME_END

# logger = logging.getLogger(__name__)

yaml = YAML()


def initialize():
    """initializes cellpy by reading the config file and the environment file"""
    try:
        _read_prm_file(_get_prm_file())
        _load_env_file()
    except FileNotFoundError:
        warnings.warn("Could not find the config-file")
    except UserWarning:
        warnings.warn("Could not read the config-file")


def _load_env_file():
    """loads the environment file"""
    env_file = pathlib.Path(prms.Paths.env_file)
    env_file_in_user_dir = pathlib.Path.home() / prms.Paths.env_file
    if env_file.is_file():
        dotenv.load_dotenv(env_file)
    elif env_file_in_user_dir.is_file():
        dotenv.load_dotenv(env_file_in_user_dir)
    else:
        logging.debug("No .env file found")


def get_user_name():
    """get the username of the current user (cross-platform)"""
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
    if os.name == "nt" and USE_MY_DOCUMENTS:
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
            yaml.dump(config_dict, config_file)
    except YAMLError:
        raise ConfigFileNotWritten


def _update_prms(config_dict):
    """updates the prms with the values in the config_dict"""
    # config_dict is your current config
    # _config_attr is the attribute in the prms module (i.e. the defaults)

    logging.debug("updating parameters")
    logging.debug(f"new prms: {config_dict}")
    for key in config_dict:
        if config_dict[key] is None:
            logging.debug(f"{config_dict[key]} is None")
            continue
        if key == "Paths":
            _config_attr = getattr(prms, key)
            for k in config_dict[key]:
                z = config_dict[key][k]

                _txt = f"{k}: {z}"
                if k.lower() == "db_filename":
                    # special hack because it is a filename and not a path
                    pass
                elif k.lower() in OTHERPATHS:
                    logging.debug("converting to OtherPath")
                    # special hack because it is possibly an external location
                    z = OtherPath(
                        str(z)
                    ).resolve()  # v1.0.0: this is only resolving local paths
                else:
                    logging.debug("converting to pathlib.Path")
                    z = pathlib.Path(z).resolve()
                _txt += f" -> {z}"

                logging.debug(_txt)
                setattr(_config_attr, k, z)

        elif hasattr(prms, key):
            _config_attr = getattr(prms, key)
            if _config_attr is None:
                logging.debug(f"{_config_attr} is None")
                continue
            for k in config_dict[key]:
                z = config_dict[key][k]
                if isinstance(z, dict):
                    y = getattr(_config_attr, k)
                    z = box.Box({**y, **z})
                if isinstance(z, ruamel.yaml.comments.CommentedMap):
                    z = box.Box(z)
                setattr(_config_attr, k, z)
        else:
            logging.info("\n  not-supported prm: %s" % key)


def _convert_instruments_to_dict(x):
    # Converting instruments to dictionary (since it contains box.Box objects)
    d = asdict(x)
    for k, v in d.items():
        try:
            d[k] = v.to_dict()
        except AttributeError:
            pass

    return d


def _convert_to_dict(x):
    try:
        dictionary = x.to_dict()
    except AttributeError:
        dictionary = asdict(x)
    return dictionary


def _convert_paths_to_dict(x):
    dictionary = {}
    for k in x.keys():
        # hack to get around the leading underscore (since they are properties):
        if len(k) > 1 and k[0] == "_" and k.lower()[1:] in OTHERPATHS:
            t = getattr(x, k).full_path
            k = k[1:]
        else:
            t = str(getattr(x, k))
        dictionary[k] = t
    return dictionary


def _update_and_convert_to_dict(parameter_name):
    """check that all the parameters are correct in the prm-file"""
    # update from old prm-file (before v1.0.0):
    if parameter_name == "DbCols":
        if hasattr(prms, "DbCols"):
            db_cols = _convert_to_dict(prms.DbCols)
            if db_cols is None:
                return prms.DbColsClass()

            for k in db_cols:
                if isinstance(db_cols[k], (list, tuple)):
                    db_cols[k] = db_cols[k][0]
            return db_cols
        else:
            return prms.DbColsClass()


def _pack_prms():
    """if you introduce new 'save-able' parameter dictionaries, then you have
    to include them here"""

    config_dict = {
        "Paths": _convert_paths_to_dict(prms.Paths),
        "FileNames": _convert_to_dict(prms.FileNames),
        "Db": _convert_to_dict(prms.Db),
        "DbCols": _update_and_convert_to_dict("DbCols"),
        "CellInfo": _convert_to_dict(prms.CellInfo),
        "Reader": _convert_to_dict(prms.Reader),
        "Materials": _convert_to_dict(prms.Materials),
        "Instruments": _convert_instruments_to_dict(prms.Instruments),
        "Batch": _convert_to_dict(prms.Batch),
    }
    return config_dict


def _read_prm_file(prm_filename):
    """read the prm file"""
    logging.debug("Reading config-file: %s" % prm_filename)
    try:
        with open(prm_filename, "r") as config_file:
            prm_dict = yaml.load(config_file)

    except YAMLError as e:
        raise ConfigFileNotRead from e
    else:
        if isinstance(prm_dict, dict):
            _update_prms(prm_dict)
        else:
            print(type(prm_dict))


def _read_prm_file_without_updating(prm_filename):
    """read the prm file but do not update the params"""
    logging.debug("Reading config-file: %s" % prm_filename)
    try:
        with open(prm_filename, "r") as config_file:
            prm_dict = yaml.load(config_file)

    except YAMLError as e:
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

    default_name = prms._prm_default_name  # NOQA
    prm_globtxt = prms._prm_globtxt  # NOQA

    script_dir = os.path.abspath(os.path.dirname(__file__))

    search_path = dict()
    search_path["curdir"] = os.path.abspath(os.path.dirname(sys.argv[0]))
    search_path["filedir"] = script_dir
    search_path["user_dir"] = get_user_dir()

    if search_order is None:
        search_order = ["user_dir"]  # ["curdir","filedir", "user_dir",]
    else:
        search_order = search_order

    # The default name for the prm file is at the moment in the script-dir,@
    # while default searching is in the user_dir (yes, I know):
    prm_default = os.path.join(script_dir, default_name)

    # -searching-----------------------
    search_dict: OrderedDict[Any] = OrderedDict()

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
    file_name = os.path.join(prms.user_dir, prms._prm_default_name)  # NOQA
    _write_prm_file(file_name)


def info():
    """this function will show only the 'box'-type
    attributes and their content in the cellpy.prms module"""
    print("Convenience function for listing prms")
    print(prms.__name__)
    print(f"prm file (for current user): {_get_prm_file()}")
    print()

    for key, current_object in prms.__dict__.items():
        if key.startswith("_") and not key.startswith("__") and prms._debug:  # NOQA
            print(f"Internal: {key} (type={type(current_object)}): {current_object}")

        elif isinstance(current_object, box.Box):
            print()
            print(" OLD-TYPE PRM ".center(80, "="))
            print(f"prms.{key}:")
            print(80 * "-")
            for subkey in current_object:
                print(f"prms.{key}.{subkey} = ", f"{current_object[subkey]}")
            print()

        elif key == "Paths":
            print(" NEW-TYPE PRM WITH OTHERPATHS ".center(80, "*"))
            attributes = {
                k: v for k, v in vars(current_object).items() if not k.startswith("_")
            }
            for attr in OTHERPATHS:
                attributes[attr] = getattr(current_object, attr)
            pprint(attributes, width=1)

        elif isinstance(current_object, (prms.CellPyConfig, prms.CellPyDataConfig)):
            print(" NEW-TYPE PRM ".center(80, "="))
            attributes = {
                k: v for k, v in vars(current_object).items() if not k.startswith("_")
            }
            print(f" {key} ".center(80, "="))
            pprint(attributes, width=1)
            print()


def main():
    print(" STARTING THE ACTUAL SCRIPT ".center(80, "-"))
    print("PRM FILE:")
    f = _get_prm_file()
    print(f)
    print("READING:")
    _read_prm_file(f)
    print("PACKING:")
    pprint(_pack_prms())
    print("INFO:")
    info()
    print(prms)
    pprint(str(prms.Batch), width=1)
    print(prms.Batch.summary_plot_height_fractions)


if __name__ == "__main__":
    main()
