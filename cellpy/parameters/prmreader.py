# -*- coding: utf-8 -*-
import getpass
import logging
import os
import pathlib
import warnings
from pathlib import Path
from pprint import pprint
from rich import print
import dotenv
from dataclasses import asdict
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

import cellpy.config as config
from cellpy.config.legacy import (
    DEFAULT_FILENAME,
    DEFAULT_FILENAME_END,
    DEFAULT_FILENAME_START,
    export_legacy_yaml_dict,
    find_legacy_yaml_file,
    get_user_dir as _legacy_get_user_dir,
    load_legacy_yaml_dict,
)
from cellpy.config.loader import LoadOptions
from cellpy.config.session import get_config, reload
from cellpy.exceptions import ConfigFileNotRead, ConfigFileNotWritten
from cellpy.parameters import prms
from cellpy.parameters._shim import _SHIM_SECTIONS
from cellpy.parameters.internal_settings import OTHERPATHS
from cellpy.internals.connections import OtherPath

ENVIRONMENT_EXAMPLE = """
# This is an example of an environment file for cellpy.
# The environment file is used to set environment variables
# that are used by cellpy.
# The environment file should be located in the user directory
# (i.e. the directory returned by pathlib.Path.home()).
# The default environment file is named .env_cellpy, but you can
# change this in your config file.
# The environment file should contain the following variables:
# CELLPY_PASSWORD=<password>
# CELLPY_KEY_FILENAME=<key_filename>
# CELLPY_HOST=<host>
# CELLPY_USER=<user>
"""

yaml = YAML()


def initialize():
    """Initializes cellpy by reading the config file and the environment file."""

    try:
        legacy_path = find_legacy_yaml_file()
        options = LoadOptions()
        if legacy_path is not None:
            options = LoadOptions(legacy_yaml_file=legacy_path)
        reload(options=options)
        _load_env_file()
    except FileNotFoundError:
        warnings.warn("Could not find the config-file")
    except OSError:
        warnings.warn("Could not read the config-file")


def _load_env_file():
    """Loads the environment file into ``os.environ`` (legacy OtherPath consumers)."""

    env_file = pathlib.Path(config.paths.env_file)
    env_file_in_user_dir = pathlib.Path.home() / env_file.name
    if env_file.is_file():
        dotenv.load_dotenv(env_file)
    elif env_file_in_user_dir.is_file():
        dotenv.load_dotenv(env_file_in_user_dir)
    else:
        logging.debug("No .env file found")


def _pack_prms():
    """Pack current config into legacy YAML section dict."""

    return export_legacy_yaml_dict(get_config())


def get_user_name():
    """Get the username of the current user (cross-platform)"""
    return getpass.getuser()


def create_custom_init_filename(user_name=None):
    """Creates a custom prms filename"""
    if user_name is None:
        return DEFAULT_FILENAME_START + get_user_name() + DEFAULT_FILENAME_END
    return DEFAULT_FILENAME_START + user_name + DEFAULT_FILENAME_END


def get_user_dir_and_dst(init_filename=None):
    """Gets the name of the user directory and full prm filepath"""
    if init_filename is None:
        init_filename = create_custom_init_filename()
    user_dir = get_user_dir()
    dst_file = user_dir / init_filename
    return user_dir, dst_file


def get_user_dir():
    """Gets the name of the user directory"""
    return _legacy_get_user_dir()


def _write_prm_file(file_name=None):
    logging.debug(f"saving configuration to {file_name}")
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


def _write_env_file(env_file_name=None):
    """writes example environment file"""
    dev = False
    if env_file_name is None:
        env_file_name = get_env_file_name()

    logging.debug(f"saving environment arguments to {env_file_name}")
    if dev:
        print("---content----------------------------------------")
        print("* OBS! in dev-mode, file will not be saved!")
        print(ENVIRONMENT_EXAMPLE)
        print("--------------------------------------------------")
        return

    try:
        with open(env_file_name, "w") as env_file:
            env_file.write(ENVIRONMENT_EXAMPLE)
    except Exception as e:
        print(f"could not write to {env_file_name}")
        print(e)


def _convert_instruments_to_dict(x):
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
    from cellpy.config.models import PathsConfig
    from cellpy.parameters._shim import _SectionProxy

    if isinstance(x, _SectionProxy):
        x = x._target()
    if isinstance(x, PathsConfig):
        dictionary = {}
        for key in PathsConfig.model_fields:
            value = getattr(x, key)
            if key in {"rawdatadir", "cellpydatadir"}:
                dictionary[key] = value.full_path if hasattr(value, "full_path") else str(value)
            elif key == "db_filename":
                dictionary[key] = value
            else:
                dictionary[key] = str(value)
        return dictionary

    dictionary = {}
    for k in x.keys():
        if len(k) > 1 and k[0] == "_" and k.lower()[1:] in OTHERPATHS:
            t = getattr(x, k).full_path
            k = k[1:]
        else:
            t = str(getattr(x, k))
        dictionary[k] = t
    return dictionary


def _resolve_loaded_paths(resolve_paths: bool = True) -> None:
    """Resolve local path fields after loading a prm file (legacy behavior)."""

    if not resolve_paths:
        return
    from cellpy.config.models import PathsConfig

    paths: PathsConfig = get_config().paths
    for key in PathsConfig.model_fields:
        if key == "db_filename":
            continue
        value = getattr(paths, key)
        if key in {"rawdatadir", "cellpydatadir"} and isinstance(value, OtherPath):
            setattr(paths, key, value.resolve())
        elif isinstance(value, Path):
            setattr(paths, key, value.resolve())


def _read_prm_file(prm_filename, resolve_paths=True):
    """read the prm file"""

    logging.debug("Reading config-file: %s" % prm_filename)
    try:
        overrides = load_legacy_yaml_dict(pathlib.Path(prm_filename))
    except YAMLError as e:
        raise ConfigFileNotRead from e
    reload(overrides=overrides, options=LoadOptions(skip_files=True, skip_env=True))
    _resolve_loaded_paths(resolve_paths=resolve_paths)
    _load_env_file()


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
        logging.info("Could not find the prm-file")

    legacy = find_legacy_yaml_file(search_order=search_order)
    if legacy is not None:
        return str(legacy)

    script_dir = pathlib.Path(__file__).resolve().parent
    return str(script_dir / DEFAULT_FILENAME)


def _save_current_prms_to_user_dir():
    file_name = os.path.join(prms.user_dir, prms._prm_default_name)  # NOQA
    _write_prm_file(file_name)


def get_env_file_name():
    """Returns the location of the env-file"""

    env_file = pathlib.Path(config.paths.env_file)
    return env_file


def info():
    """Show resolved config sections (legacy ``prms`` names)."""

    print(80 * "=")
    print(f"Listing the content of the prms module ({prms.__name__})")
    print(80 * "-")
    config_file = _get_prm_file()
    env_file = get_env_file_name()
    print(f" prm file (for current user): {config_file}")
    print(f" - exists: {os.path.isfile(config_file)}")

    print(f" env file (for current user): {env_file}")
    print(f" - exists: {os.path.isfile(env_file)}")

    print()
    cfg = get_config()
    section_getters = {
        "Paths": lambda: cfg.paths,
        "FileNames": lambda: cfg.file_names,
        "Reader": lambda: cfg.reader,
        "Db": lambda: cfg.db,
        "DbCols": lambda: cfg.db_cols,
        "Batch": lambda: cfg.batch,
        "Instruments": lambda: cfg.instruments,
        "CellInfo": lambda: cfg.defaults.cell_info,
        "Materials": lambda: cfg.defaults.materials,
    }
    for legacy_name in sorted(_SHIM_SECTIONS):
        section = section_getters[legacy_name]()
        print(f" {legacy_name} ".center(80, "-"))
        print(section.model_dump(mode="json"))
        print()


def _main():
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
    pprint(str(config.batch.summary_plot_height_fractions), width=1)


if __name__ == "__main__":
    _main()
