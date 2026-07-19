import base64
import getpass
import logging
import os
import pathlib
import platform
from pprint import pprint
import re
import subprocess
import sys
import time
from typing import Annotated, Optional, Union
import urllib
from pathlib import Path

import rich
import typer

import cellpy._version
from cellpy.exceptions import ConfigFileNotWritten
from cellpy.parameters import prmreader
from cellpy.parameters.internal_settings import OTHERPATHS
from cellpy.internals.connections import OtherPath
from cellpy.utils.template_registry import REGISTERED_TEMPLATES
import cellpy.config as config
from cellpy import cli_api

DIFFICULT_MISSING_MODULES = {}

try:
    import cookiecutter.exceptions
    import cookiecutter.main
    import cookiecutter.prompt

except ModuleNotFoundError:
    _txt = (
        "Could not import cookiecutter (used by cellpy new). Try installing it, for example by writing:"
        "\n\n         python -m pip install cookiecutter\n"
    )
    DIFFICULT_MISSING_MODULES["cookiecutter"] = _txt

try:
    import github
    from github import Github

except ModuleNotFoundError:
    _txt = (
        "Could not import the github library (used by cellpy pull). Try installing it, for example by writing:"
        "\n\n         python -m pip install github\n"
    )
    DIFFICULT_MISSING_MODULES["github"] = _txt


try:
    import sqlalchemy_access

except ModuleNotFoundError:
    _txt = (
        "Could not import the sqlalchemy_access library (usually used by when reading arbin .res files "
        "on windows). If you need it, try installing it by writing:"
        "\n\n         python -m pip install sqlalchemy-access\n"
    )
    DIFFICULT_MISSING_MODULES["sqlalchemy-access"] = _txt


try:
    import lmfit

except ModuleNotFoundError:
    _txt = (
        "Could not import the lmfit library (used when fitting ocv rlx data)."
        " If you think you will need it, try installing it for example by writing:"
        "\n\n         python -m pip install lmfit\n"
    )
    DIFFICULT_MISSING_MODULES["lmfit"] = _txt


try:
    import jinja2_time

except ModuleNotFoundError:
    _txt = (
        "Could not import the jinja2_time library (used by cellpy new)."
        " Try installing it, for example by writing:"
        "\n\n         python -m pip install jinja2_time\n"
    )
    DIFFICULT_MISSING_MODULES["jinja2_time"] = _txt

VERSION = cellpy._version.__version__
REPO = "jepegit/cellpy"
USER = "jepegit"
GITHUB_PWD_VAR_NAME = "GD_PWD"
DEFAULT_EDITOR = "vim"
EDITORS = {"Windows": "notepad"}


def save_prm_file(prm_filename):
    """saves (writes) the prms to file"""
    prmreader._write_prm_file(prm_filename)


def dump_env_file(env_filename):
    """saves (writes) the env to file"""
    typer.echo(f" dumping env file to {env_filename}")
    prmreader._write_env_file(env_filename)


def get_package_prm_dir():
    """gets the folder where the cellpy package lives"""
    return pathlib.Path(cellpy.parameters.__file__).parent


def get_default_config_file_path(init_filename=None):
    """gets the path to the default config-file"""
    prm_dir = get_package_prm_dir()
    if not init_filename:
        init_filename = prmreader.DEFAULT_FILENAME
    src = prm_dir / init_filename
    return src


def get_dst_file(user_dir, init_filename):
    """gets the destination path for the config-file"""
    user_dir = pathlib.Path(user_dir)
    dst_file = user_dir / init_filename
    return dst_file


def echo_missing_modules():
    """prints out the missing modules"""
    for m in DIFFICULT_MISSING_MODULES:
        print(f"missing module: {m}")
        print(f"message: {DIFFICULT_MISSING_MODULES[m]}")


def _modify_config_file():
    pass


def _create_cellpy_folders():
    pass


cli = typer.Typer(
    name="cellpy",
    help="cellpy - command line interface.",
    # Click did not offer these, and the CLI surface is a contract (#569).
    add_completion=False,
)


# ----------------------- setup --------------------------------------
setup_app = typer.Typer()


@setup_app.callback(invoke_without_command=True)
def setup(
    ctx: typer.Context,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Allows you to specify div. folders and setting.",
        ),
    ] = False,
    not_relative: Annotated[
        bool,
        typer.Option(
            "--not-relative",
            "-nr",
            help="If root-dir is given, put it directly in the root (/) folder"
            " i.e. don't put it in your home directory. Defaults to False. Remark"
            " that if you specifically write a path name instead of selecting the"
            " suggested default, the path you write will be used as is.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-dr",
            help="Run setup in dry mode (only print - do not execute). This is"
            " typically used when developing and testing cellpy. Defaults to"
            " False.",
        ),
    ] = False,
    reset: Annotated[
        bool,
        typer.Option(
            "--reset",
            "-r",
            help="Do not suggest path defaults based on your current configuration-file",
        ),
    ] = False,
    root_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--root-dir",
            "-d",
            help="Use custom root dir. If not given, your home directory"
            " will be used as the top level where cellpy-folders"
            " will be put. The folder path must follow"
            " directly after this option (if used). Example:\n"
            " $ cellpy setup -d 'MyDir'",
        ),
    ] = None,
    folder_name: Annotated[
        Optional[Path],
        typer.Option("--folder-name", "-n", help=""),
    ] = None,
    test_user: Annotated[
        Optional[str],
        typer.Option(
            "--test_user", "-t", help="Fake name for fake user (for testing)"
        ),
    ] = None,
    silent: Annotated[
        bool,
        typer.Option("--silent", "-s", help="Silent mode (no questions asked)"),
    ] = False,
    no_deps: Annotated[
        bool,
        typer.Option("--no-deps", help="Don't install missing dependencies"),
    ] = False,
):
    """This will help you to set up cellpy."""

    if ctx.invoked_subcommand is not None:
        # a subcommand (e.g. ``cellpy setup migrate``) runs instead
        return

    typer.echo("[cellpy] (setup)")
    typer.echo(f"[cellpy] root-dir: {root_dir}")

    # notify of missing 'difficult' or optional modules
    if not no_deps:
        typer.echo("[cellpy] checking dependencies")
        for m in DIFFICULT_MISSING_MODULES:
            typer.echo(" [cellpy] WARNING! ".center(80, "-"))
            typer.echo("[cellpy] missing dependencies:")
            typer.echo(f"[cellpy] - {m}")
            typer.echo(f"[cellpy] {DIFFICULT_MISSING_MODULES[m]}")
            typer.echo(
                "[cellpy] (you can skip this check by using the --no-deps option)"
            )
            typer.echo(80 * "-")

    # generate variables
    init_filename = prmreader.create_custom_init_filename()
    user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
    env_file = prmreader.get_env_file_name()

    if dry_run:
        typer.echo("Create custom init filename and get user_dir and destination")
        typer.echo(f"Got the following parameters:")
        typer.echo(f" - init_filename: {init_filename}")
        typer.echo(f" - user_dir: {user_dir}")
        typer.echo(f" - dst_file: {dst_file}")
        typer.echo(f" - not_relative: {not_relative}")

    if root_dir and not interactive:
        typer.echo("[cellpy] custom root-dir can only be used in interactive mode")
        typer.echo("[cellpy] -> setting interactive mode")
        interactive = True

    if not root_dir:
        root_dir = user_dir
        # root_dir = pathlib.Path(os.getcwd())
    root_dir = pathlib.Path(root_dir)

    if dry_run:
        typer.echo(f" - root_dir: {root_dir}")

    if test_user:
        typer.echo(f"[cellpy] (setup) DEV-MODE test_user: {test_user}")
        init_filename = prmreader.create_custom_init_filename(test_user)
        user_dir = root_dir
        dst_file = get_dst_file(user_dir, init_filename)
        typer.echo(f"[cellpy] (setup) DEV-MODE user_dir: {user_dir}")
        typer.echo(f"[cellpy] (setup) DEV-MODE dst_file: {dst_file}")

    if not pathlib.Path(dst_file).is_file():
        typer.echo(f"[cellpy] {dst_file} not found -> I will make one for you")
        reset = True

    if not pathlib.Path(env_file).is_file():
        typer.echo(
            f"[cellpy] {env_file} not found -> I will make one (but you must edit it yourself)"
        )

    if interactive:
        typer.echo(" interactive mode ".center(80, "-"))
        _update_paths(
            custom_dir=root_dir,
            relative_home=not not_relative,
            default_dir=folder_name,
            dry_run=dry_run,
            reset=reset,
            interactive=True,
        )
        _write_config_file(user_dir, dst_file, init_filename, dry_run)
        _write_toml_config_file(dst_file, dry_run, test_user=test_user)
        _write_env_file(user_dir, env_file, dry_run)
        _check(dry_run=dry_run)

    else:
        if reset:
            _update_paths(
                user_dir,
                False,
                default_dir=folder_name,
                dry_run=dry_run,
                reset=True,
                interactive=False,
                silent=silent,
            )
        _write_config_file(user_dir, dst_file, init_filename, dry_run)
        _write_toml_config_file(dst_file, dry_run, test_user=test_user)
        _write_env_file(user_dir, env_file, dry_run)
        _check(dry_run=dry_run, full_check=False)


def _write_toml_config_file(dst_file, dry_run, test_user=None):
    """Write the ``cellpy.toml`` twin generated from the config models (#454).

    The TOML is the single source of truth going forward (config plan Step 5):
    it is *generated* from the resolved ``CellpyConfig`` models (secrets
    excluded), so adding a field is a one-file change in the models. In
    test-user (DEV) mode the file lands next to the legacy conf instead of the
    real platform config dir.
    """
    from cellpy import config as cellpy_config
    from cellpy.config import loader as config_loader

    if test_user:
        toml_path = pathlib.Path(dst_file).with_name("cellpy.toml")
    else:
        toml_path = config_loader.user_config_path()

    if dry_run:
        typer.echo(f"[cellpy] (setup) dry-run: would write {toml_path}")
        return

    data = cellpy_config.get_config().model_dump_for_file()
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    config_loader.write_toml(toml_path, data)
    typer.echo(f"[cellpy] (setup) wrote {toml_path}")


@setup_app.command(
    "migrate", short_help="Convert the legacy .conf (YAML) to cellpy.toml."
)
def setup_migrate(
    src: Annotated[
        Optional[Path],
        typer.Option(
            "--src",
            exists=True,
            help="Legacy config file to convert (auto-detected when not given).",
        ),
    ] = None,
    dst: Annotated[
        Optional[Path],
        typer.Option(
            "--dst",
            help="Target cellpy.toml (defaults to the platform user-config location).",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-dr", help="Only print what would be done."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite an existing cellpy.toml."),
    ] = False,
):
    """One-time conversion of the legacy YAML .conf file to cellpy.toml.

    The old file is left untouched (it keeps working through the v2.0
    deprecation window); the generated TOML takes precedence once present.
    """
    from cellpy.config import loader as config_loader
    from cellpy.config import migrate as config_migrate

    if src is None:
        try:
            src = prmreader._get_prm_file()
        except Exception:
            src = None
        if src is None or not pathlib.Path(src).is_file():
            typer.echo(
                "[cellpy] (setup migrate) no legacy config file found - "
                "nothing to migrate (run `cellpy setup` to create a fresh one)."
            )
            return
    src = pathlib.Path(src)

    toml_path = pathlib.Path(dst) if dst else config_loader.user_config_path()
    if toml_path.is_file() and not force:
        typer.echo(
            f"[cellpy] (setup migrate) {toml_path} already exists "
            "- use --force to overwrite."
        )
        return

    typer.echo(f"[cellpy] (setup migrate) source: {src}")
    typer.echo(f"[cellpy] (setup migrate) target: {toml_path}")
    if dry_run:
        typer.echo("[cellpy] (setup migrate) dry-run: not writing anything.")
        return

    toml_path.parent.mkdir(parents=True, exist_ok=True)
    config_migrate.convert_yaml_file_to_toml(src, toml_path)
    typer.echo("[cellpy] (setup migrate) done - the old file is kept untouched.")


def _update_paths(
    custom_dir=None,
    relative_home=True,
    reset=False,
    dry_run=False,
    default_dir=None,
    silent=False,
    interactive=False,
):
    # please, refactor me :-(

    h = prmreader.get_user_dir()

    if default_dir is None:
        default_dir = "cellpy_data"

    if dry_run:
        typer.echo(f" - default_dir: {default_dir}")
        typer.echo(f" - custom_dir: {custom_dir}")
        typer.echo(f" - relative_home: {relative_home}")

    if custom_dir:
        reset = True
        if relative_home:
            h = h / custom_dir
        if not custom_dir.parts[-1] == default_dir:
            h = h / default_dir

    if not reset:
        outdatadir = pathlib.Path(config.paths.outdatadir)
        rawdatadir = OtherPath(config.paths.rawdatadir)
        cellpydatadir = OtherPath(config.paths.cellpydatadir)
        filelogdir = pathlib.Path(config.paths.filelogdir)
        examplesdir = pathlib.Path(config.paths.examplesdir)
        db_path = pathlib.Path(config.paths.db_path)
        db_filename = config.paths.db_filename
        notebookdir = pathlib.Path(config.paths.notebookdir)
        batchfiledir = pathlib.Path(config.paths.batchfiledir)
        templatedir = pathlib.Path(config.paths.templatedir)
        instrumentdir = pathlib.Path(config.paths.instrumentsdir)
    else:
        outdatadir = "out"
        rawdatadir = "raw"
        cellpydatadir = "cellpyfiles"
        filelogdir = "logs"
        examplesdir = "examples"
        db_path = "db"
        db_filename = "cellpy_db.xlsx"
        notebookdir = "notebooks"
        batchfiledir = "batchfiles"
        templatedir = "templates"
        instrumentdir = "instruments"

    outdatadir = h / outdatadir
    rawdatadir = h / rawdatadir
    cellpydatadir = h / cellpydatadir
    filelogdir = h / filelogdir
    examplesdir = h / examplesdir
    db_path = h / db_path
    notebookdir = h / notebookdir
    batchfiledir = h / batchfiledir
    templatedir = h / templatedir
    instrumentdir = h / instrumentdir

    if dry_run:
        typer.echo(f" - base (h): {h}")

    if interactive:
        outdatadir = _ask_about_path(
            "where to output processed data and results", outdatadir
        )
        rawdatadir = _ask_about_otherpath("where your raw data are located", rawdatadir)
        cellpydatadir = _ask_about_otherpath("where to put cellpy-files", cellpydatadir)
        filelogdir = _ask_about_path("where to dump the log-files", filelogdir)
        examplesdir = _ask_about_path(
            "where to download cellpy examples and tests", examplesdir
        )
        db_path = _ask_about_path("what folder your db file lives in", db_path)
        db_filename = _ask_about_name("the name of your db-file", db_filename)
        notebookdir = _ask_about_path(
            "where to put your jupyter notebooks", notebookdir
        )
        batchfiledir = _ask_about_path("where to put your batch files", batchfiledir)
        templatedir = _ask_about_path("where to put your batch files", templatedir)
        instrumentdir = _ask_about_path("where to put your batch files", instrumentdir)

    # update folders based on suggestions
    for d in [
        outdatadir,
        rawdatadir,
        cellpydatadir,
        filelogdir,
        examplesdir,
        notebookdir,
        db_path,
        batchfiledir,
        templatedir,
        instrumentdir,
    ]:
        if not dry_run:
            _create_dir(d, confirm=not silent)
        else:
            typer.echo(f"dry run (so I did not create {d})")

    # update config-file based on suggestions
    config.paths.outdatadir = str(outdatadir)
    config.paths.rawdatadir = str(rawdatadir)
    config.paths.cellpydatadir = str(cellpydatadir)
    config.paths.filelogdir = str(filelogdir)
    config.paths.examplesdir = str(examplesdir)
    config.paths.db_path = str(db_path)
    config.paths.db_filename = str(db_filename)
    config.paths.notebookdir = str(notebookdir)
    config.paths.batchfiledir = str(batchfiledir)
    config.paths.templatedir = str(templatedir)
    config.paths.instrumentdir = str(instrumentdir)


def _ask_about_path(q, p):
    typer.echo(f"\n[cellpy] (setup) input {q}")
    typer.echo(f"[cellpy] (setup) current: {p}")
    new_path = input("[cellpy] (setup) new value (press enter to keep) >>> ").strip()
    if not new_path:
        new_path = p
    return pathlib.Path(new_path)


def _ask_about_otherpath(q, p):
    typer.echo(f"\n[cellpy] (setup) input {q}")
    typer.echo(f"[cellpy] (setup) current: {p}")
    new_path = input("[cellpy] (setup) new value (press enter to keep) >>> ").strip()
    if not new_path:
        new_path = p
    return OtherPath(new_path)


def _ask_about_name(q, n):
    typer.echo(f"\n[cellpy] (setup) input {q}")
    typer.echo(f"[cellpy] (setup) current: {n}")
    new_name = input("[cellpy] (setup) new value (press enter to keep) >>> ").strip()
    if not new_name:
        new_name = n
    return new_name


def _create_dir(path, confirm=True, parents=True, exist_ok=True):
    if isinstance(path, OtherPath):
        if path.is_external:
            return path
    o = path.resolve()
    if not o.is_dir():
        o_parent = o.parent
        create_dir = True
        if confirm:
            if not o_parent.is_dir():
                create_dir = input(
                    f"\n[cellpy] (setup) {o_parent} does not exist. Create it [y]/n ?"
                )
                if not create_dir:
                    create_dir = True
                elif create_dir in ["y", "Y"]:
                    create_dir = True
                else:
                    create_dir = False

        if create_dir:
            try:
                o.mkdir(parents=parents, exist_ok=exist_ok)
                typer.echo(f"[cellpy] (setup) Created {o}")
            except FileExistsError:
                typer.echo(f"[cellpy] (setup) {o} already exists.")
            except FileNotFoundError:
                typer.echo(f"[cellpy] (setup) {o} not available.")
            except Exception as e:
                typer.echo(f"[cellpy] (setup) WARNING! Could not create {o}.")
                logging.debug(e)
                typer.echo(f"[cellpy] (setup) ...continuing anyway.")
        else:
            typer.echo(f"[cellpy] (setup) Could not create {o}")
    return o


def _check_import_cellpy():
    try:
        import cellpy
        from cellpy import log
        from cellpy.readers import cellreader

        return True
    except:
        typer.echo(" Failed to import cellpy")
        typer.echo(" Severity: critical")
        return False


def _check_import_pyodbc():
    import platform

    from cellpy.parameters import prms

    ODBC = prms._odbc
    SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver

    use_subprocess = config.instruments.Arbin.use_subprocess
    detect_subprocess_need = config.instruments.Arbin.detect_subprocess_need
    typer.echo(f" This is needed for loading Arbin .res files")
    typer.echo(f" parsing prms")
    typer.echo(
        f" (from your configuration file if it exists, otherwise using defaults)"
    )
    typer.echo(f" - ODBC: {ODBC}")
    typer.echo(f" - SEARCH_FOR_ODBC_DRIVERS: {SEARCH_FOR_ODBC_DRIVERS}")
    typer.echo(f" - use_subprocess: {use_subprocess}")
    typer.echo(f" - detect_subprocess_need: {detect_subprocess_need}")
    typer.echo(f" - stated office version: {config.instruments.Arbin.office_version}")

    typer.echo(" checking system")
    is_posix = False
    is_macos = False
    if os.name == "posix":
        is_posix = True
        typer.echo(f" - running on posix")
    current_platform = platform.system()
    if current_platform == "Darwin":
        is_macos = True
        typer.echo(f" - running on a mac")

    python_version, os_version = platform.architecture()
    typer.echo(f" - python version: {python_version}")
    typer.echo(f" - os version: {os_version}")

    if not is_posix:
        if not config.instruments.Arbin.sub_process_path:
            sub_process_path = str(prms._sub_process_path)
        else:
            sub_process_path = str(config.instruments.Arbin.sub_process_path)
        typer.echo(f" stated path to sub-process: {sub_process_path}")
        if not os.path.isfile(sub_process_path):
            typer.echo(f" - OBS! missing")

    if is_posix:
        typer.echo(" checking existence of mdb-export")
        sub_process_path = "mdb-export"
        from subprocess import PIPE, run

        command = ["command", "-v", sub_process_path]

        try:
            typer.echo(f" - trying to run {command}")
            result = run(
                command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True
            )
            if result.returncode == 0:
                typer.echo(f" - found it!")
                return True

            typer.echo(f" - could not find {sub_process_path}")

            if is_macos:
                driver = "/usr/local/lib/libmdbodbc.dylib"
                typer.echo(
                    f" looks like you are on a mac. Searching for suitable driver: {driver})"
                )
                if not os.path.isfile(driver):
                    typer.echo(f" - could not find {driver}")
                    typer.echo(
                        " ! If you want to load Arbin .res files you will have to install it manually."
                    )
                    typer.echo(" - Try installing it with brew:\n")
                    typer.echo("   brew install mdbtools")
                    return False
                typer.echo(f" - found it: {driver}")
                return True
            else:
                typer.echo(
                    " ! If you want to load Arbin .res files you will have to install it manually."
                )
                typer.echo("   For example (for ubuntu):\n")
                typer.echo("   sudp apt-get update")
                typer.echo("   sudp apt-get install -y mdbtools")
            return False

        except AssertionError:
            typer.echo(" - could not find any suitable driver")
            return False

    # not posix - checking for odbc drivers
    # 1) checking if you have defined one
    try:
        driver = config.instruments.Arbin.odbc_driver
        if not driver:
            raise AttributeError
        typer.echo(" You have defined an odbc driver in your config file")
        typer.echo(f" - driver: {driver}")
    except AttributeError:
        typer.echo(" FYI: you have not defined any odbc_driver(s)")
        typer.echo(
            " (The name of the driver from the configuration file is "
            "used as a backup when cellpy cannot locate a driver by itself)"
        )

    use_ado = False

    if ODBC == "ado":
        use_ado = True
        typer.echo(" you stated that you prefer the ado loader")
        typer.echo(" checking if adodbapi is installed")
        try:
            import adodbapi as dbloader
        except ImportError:
            use_ado = False
            typer.echo(" Failed! Try setting pyodbc as your loader or install")
            typer.echo(" adodbapi (http://adodbapi.sourceforge.net/)")

    if not use_ado:
        if ODBC == "pyodbc":
            typer.echo(" you stated that you prefer the pyodbc loader")
            try:
                import pyodbc as dbloader
            except ImportError:
                typer.echo(" Failed! Could not import it.")
                typer.echo(" Try 'pip install pyodbc'")
                dbloader = None

        elif ODBC == "pypyodbc":
            typer.echo(" you stated that you prefer the pypyodbc loader")
            try:
                import pypyodbc as dbloader  # type: ignore
            except ImportError:
                typer.echo(" Failed! Could not import it.")
                typer.echo(" try 'pip install pypyodbc'")
                typer.echo(" or set pyodbc as your loader in your prm file")
                typer.echo(" (and install it)")
                dbloader = None

    typer.echo(" searching for odbc drivers")
    try:
        drivers = [
            driver
            for driver in dbloader.drivers()
            if "Microsoft Access Driver" in driver
        ]
        typer.echo(f" Found these: {drivers}")
        driver = drivers[0]
        typer.echo(f" - odbc driver: {driver}")
        return True

    except IndexError as e:
        logging.debug(" Unfortunately, it seems the list of drivers is emtpy.")
        typer.echo(
            "\n Could not find any odbc-drivers suitable for .res-type files. "
            "Check out the homepage of pydobc for info on installing drivers"
        )
        typer.echo(
            " One solution that might work is downloading "
            "the Microsoft Access database engine "
            "(in correct bytes (32 or 64)) "
            "from:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=13255"
        )
        typer.echo(
            " Or install mdbtools and set it up (check the cellpy docs for help)"
        )
        typer.echo("\n")
        return False


def _check_config_file():
    prm_file_name = _configloc()
    env_file_name = _envloc()

    if env_file_name is None:
        typer.echo(" FYI! Could not locate the environment file")

    if prm_file_name is None:
        typer.echo(" Could not find the config file")
        typer.echo(" You can create one by running 'cellpy setup'")
        return False

    prm_dict = prmreader._read_prm_file_without_updating(prm_file_name)
    try:
        prm_paths = prm_dict["Paths"]
        required_dirs = [
            "cellpydatadir",
            "examplesdir",
            "filelogdir",
            "notebookdir",
            "outdatadir",
            "rawdatadir",
            "batchfiledir",
            "templatedir",
            "db_path",
        ]
        missing = 0
        for k in required_dirs:
            value = prm_paths.get(k, None)
            typer.echo(f" - {k}: {value}")
            # splitting this into two if-statements to make it easier to debug if OtherPath changes
            if k in OTHERPATHS:
                print(f" skipping check for external {k} (for now)")
                # if not OtherPath(
                #     value
                # ).is_dir():  # Assuming OtherPath returns True if it is external.
                #     missing += 1
                #     typer.echo("COULD NOT CONNECT!")
                #     typer.echo(f"({value} is not a directory)")
            elif value and not pathlib.Path(value).is_dir():
                missing += 1
                typer.echo(" COULD NOT CONNECT!")
                typer.echo(f" ({value} is not a directory)")
            if not value:
                missing += 1
                typer.echo(" MISSING")

        value = prm_paths.get("db_filename", None)
        typer.echo(f" - db_filename: {value}")
        if not value:
            missing += 1
            typer.echo(" MISSING")

        if missing:
            return False
        else:
            return True

    except Exception as e:
        typer.echo(" Following error occurred:")
        typer.echo(e)
        return False


def _check(dry_run=False, full_check=True):
    typer.echo(" checking ".center(80, "="))
    if dry_run:
        typer.echo("*** dry-run: skipping the test")
        return
    failed_checks = 0
    number_of_checks = 0

    def sub_check(check_type, check_func):
        failed = 0
        typer.echo(f"[cellpy] * - Checking {check_type}")
        if check_func():
            typer.echo(f"[cellpy] -> succeeded!")
        else:
            typer.echo("f[cellpy] -> failed!!!!")
            failed = 1
        typer.echo(80 * "-")
        return failed

    check_types = [
        "cellpy imports",
        "importing pyodbc",
    ]
    check_funcs = [
        _check_import_cellpy,
        _check_import_pyodbc,
    ]

    # additional checks that require loading the config file (not a part of setup)
    additional_types = ["configuration files"]
    additional_funcs = [_check_config_file]
    if full_check:
        check_types.extend(additional_types)
        check_funcs.extend(additional_funcs)

    for ct, cf in zip(check_types, check_funcs):
        try:
            failed_checks += sub_check(ct, cf)
        except Exception as e:
            typer.echo(f"[cellpy] check raised an exception ({e})")
        number_of_checks += 1
    typer.echo(" results ".center(80, "="))
    succeeded_checks = number_of_checks - failed_checks

    if failed_checks > 0:
        typer.echo(
            f"[cellpy] Some of the checks failed! This could potentially be a problem."
        )
        typer.echo(f"[cellpy] Failed {failed_checks} out of {number_of_checks} checks.")
    else:
        typer.echo(
            f"[cellpy] Succeeded {succeeded_checks} out of {number_of_checks} checks."
        )
    typer.echo(80 * "=")


def _write_config_file(user_dir, dst_file, init_filename, dry_run):
    typer.echo(" update configuration ".center(80, "-"))
    typer.echo("[cellpy] (setup) Writing configurations to user directory:")
    typer.echo(f"\n         {user_dir}\n")

    if os.path.isfile(dst_file):
        typer.echo("[cellpy] (setup) File already exists!")
        typer.echo("[cellpy] (setup) Keeping most of the old configuration parameters")
    try:
        if dry_run:
            typer.echo(
                f"*** dry-run: skipping actual saving of {dst_file} ***", color="red"
            )
        else:
            typer.echo(f"[cellpy] (setup) Saving file ({dst_file})")
            save_prm_file(dst_file)

    except ConfigFileNotWritten:
        typer.echo("[cellpy] (setup) Something went wrong! Could not write the file")
        typer.echo(
            "[cellpy] (setup) Trying to write a file"
            + f"called {prmreader.DEFAULT_FILENAME} instead"
        )

        try:
            user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
            if dry_run:
                typer.echo(
                    f"*** dry-run: skipping actual saving of {dst_file} ***",
                    color="red",
                )
            else:
                save_prm_file(dst_file)

        except ConfigFileNotWritten:
            _txt = "[cellpy] (setup) No, that did not work either.\n"
            _txt += "[cellpy] (setup) Well, guess you have to talk to the developers."
            typer.echo(_txt)
    else:
        typer.echo(f"[cellpy] (setup) Configuration file written!")
        typer.echo(
            f"[cellpy] (setup) OK! Now you can edit it. For example by "
            f"issuing \n\n         [your-favourite-editor] {init_filename}\n"
        )


def _write_env_file(user_dir, dst_file, dry_run):
    typer.echo(" update configuration ".center(80, "-"))
    typer.echo("[cellpy] (setup) Writing environment file:")
    typer.echo(f"\n         {dst_file}\n")

    if os.path.isfile(dst_file):
        typer.echo(f"[cellpy] (setup) Environment file {dst_file} already exists!")
        if not dry_run:
            return
    try:
        if dry_run:
            typer.echo(
                f"*** dry-run: skipping actual saving of {dst_file} ***", color="red"
            )
        else:
            typer.echo(f"[cellpy] (setup) Saving file ({dst_file})")
            dump_env_file(dst_file)

    except ConfigFileNotWritten:
        _txt = "[cellpy] (setup) No, that did not work either.\n"
        _txt += "[cellpy] (setup) Well, guess you have to talk to the developers."
        typer.echo(_txt)
    else:
        typer.echo(f"[cellpy] (setup) Environment file written!")
        typer.echo(
            f"[cellpy] (setup) OK! Now you can edit it. For example by "
            f"issuing \n\n         [your-favourite-editor] {dst_file}\n"
        )


def _get_default_editor():
    """
    Return the default text editor.

    This code is based on the `editor` library by @rec.
    """

    return os.environ.get("VISUAL") or (
        os.environ.get("EDITOR") or EDITORS.get(platform.system(), DEFAULT_EDITOR)
    )


# ----------------------- edit ---------------------------------------
@cli.command()
def edit(
    name: Annotated[Optional[str], typer.Argument()] = None,
    default_editor: Annotated[
        Optional[str],
        typer.Option("--default-editor", "-e", help="try to use this editor instead"),
    ] = None,
    debug: Annotated[
        bool, typer.Option("--debug", "-d", help="Run in debug mode.")
    ] = False,
    silent: Annotated[
        bool, typer.Option("--silent", "-s", help="Run in silent mode.")
    ] = False,
):
    """Edit your cellpy config or database files.

    You can use this to edit the configuration file, the database file, or the
    environment file. If you do not specify which file to edit, the configuration
    file will be opened.

    Examples:

        edit your cellpy configuration file

            cellpy edit config

        or just

            cellpy edit

        edit your cellpy database file

            cellpy edit db

        edit your cellpy environment file using notepad.exe (on Windows)

            cellpy edit env -e notepad.exe

    """

    if name.lower() == "db":
        _run_db(debug, silent)
        return

    elif name.lower() not in ["env", "config"] and name is not None:
        typer.echo("unknown file")
        return

    if name is None or name.lower() == "config":
        config_file = _configloc()
        filename = str(config_file.resolve())
        if config_file is None:
            print("could not find the config file")
            return
    elif name.lower() == "env":
        filename = _envloc()
        if filename is None:
            print("could not find the env file")
            return
    else:
        filename = name

    if default_editor is None:
        default_editor = _get_default_editor()

    args = [default_editor, filename]
    typer.echo(f"[cellpy] (edit) Calling '{default_editor}'")
    try:
        subprocess.call(args)
    except:
        typer.echo(f"[cellpy] (edit) Failed!")
        typer.echo(
            "[cellpy] (edit) Try 'cellpy edit -e notepad.exe' if you are on Windows"
        )


# ----------------------- info ---------------------------------------
@cli.command()
def info(
    version: Annotated[
        bool, typer.Option("--version", "-v", help="Print version information.")
    ] = False,
    configloc: Annotated[
        bool,
        typer.Option(
            "--configloc", "-l", help="Print full path to the config file."
        ),
    ] = False,
    params: Annotated[
        bool, typer.Option("--params", "-p", help="Dump all parameters to screen.")
    ] = False,
    show_config: Annotated[
        bool,
        typer.Option(
            "--config",
            "-C",
            help="Print the resolved configuration values with provenance.",
        ),
    ] = False,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Do a sanity check to see if things works as they should.",
        ),
    ] = False,
):
    """This will give you some valuable information about your cellpy."""
    complete_info = True

    if check:
        complete_info = False
        _check()

    if version:
        complete_info = False
        _version()

    if configloc:
        complete_info = False
        _configloc()

    if params:
        complete_info = False
        _dump_params()

    if show_config:
        complete_info = False
        _dump_config_resolved()

    if complete_info:
        _version()
        _configloc()


def _dump_config_resolved():
    """Print resolved config values with per-field provenance (#454)."""
    from cellpy import config as cellpy_config

    data = cellpy_config.get_config().model_dump_for_file()
    provenance = cellpy_config.sources()
    typer.echo("[cellpy] resolved configuration (value  # source-layer):")
    for section, fields in data.items():
        typer.echo(f"\n[{section}]")
        if not isinstance(fields, dict):
            typer.echo(f"  {fields!r}")
            continue
        for key, value in fields.items():
            layer = provenance.get(f"{section}.{key}", "default")
            typer.echo(f"  {key} = {value!r}  # {layer}")


# ----------------------- run ----------------------------------------
@cli.command()
def run(
    name: Annotated[str, typer.Argument()] = "NONE",
    journal: Annotated[
        bool,
        typer.Option(
            "--journal", "-j", help="Run a batch job defined in the given journal-file"
        ),
    ] = False,
    key: Annotated[
        bool,
        typer.Option("--key", "-k", help="Run a batch job defined by batch-name"),
    ] = False,
    folder: Annotated[
        bool,
        typer.Option(
            "--folder", "-f", help="Run all batch jobs iteratively in a given folder"
        ),
    ] = False,
    cellpy_project: Annotated[
        bool,
        typer.Option(
            "--cellpy-project",
            "-p",
            help="Use PaperMill to run the notebook(s) within the given project folder "
            "(will only work properly if the notebooks can be sorted in correct run-order by 'sorted'). "
            "Warning! the NAME will be 'converted' when it is loaded "
            "(same as print(name) does) - "
            "so you can't use backslash ('\\') as normal in windows (use either '/' or '\\\\' instead).",
        ),
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", "-d", help="Run in debug mode.")
    ] = False,
    silent: Annotated[
        bool, typer.Option("--silent", "-s", help="Run in silent mode.")
    ] = False,
    raw: Annotated[
        bool, typer.Option("--raw", help="Force loading raw-file(s).")
    ] = False,
    cellpyfile: Annotated[
        bool, typer.Option("--cellpyfile", help="Force cellpy-file(s).")
    ] = False,
    minimal: Annotated[
        bool, typer.Option("--minimal", help="Minimal processing.")
    ] = False,
    nom_cap: Annotated[
        Optional[float],
        typer.Option(
            "--nom-cap", help="nominal capacity (used in calculating rates etc)"
        ),
    ] = None,
    batch_col: Annotated[
        Optional[str],
        typer.Option("--batch_col", help="batch column (if selecting running from db)"),
    ] = None,
    project: Annotated[
        Optional[str],
        typer.Option(
            "--project", help="name of the project (if selecting running from db)"
        ),
    ] = None,
    list_: Annotated[
        bool, typer.Option("--list", "-l", help="List batch-files.")
    ] = False,
):
    """Run a cellpy process (for example a batch-job).

    You can use this to launch specific applications.

    Examples:

        run a batch job described in a journal file

           cellpy run -j my_experiment.json

    """
    if list_:
        _run_list(name)
        return

    if name == "NONE":
        typer.echo(
            "Usage: cellpy run [OPTIONS] NAME\n"
            "Try 'cellpy run --help' for help.\n\n"
            "Error: Missing argument 'NAME'."
        )
        sys.exit(-1)

    if debug:
        typer.echo("[cellpy] (run) debug mode on")

    if silent:
        typer.echo("[cellpy] (run) silent mode on")

    typer.echo("[cellpy]\n")

    if cellpy_project:
        _run_project(name)

    elif journal:
        _run_journal(name, debug, silent, raw, cellpyfile, minimal, nom_cap)

    elif folder:
        _run_journals(name, debug, silent, raw, cellpyfile, minimal)

    elif key:
        _run_from_db(
            name,
            debug,
            silent,
            raw,
            cellpyfile,
            minimal,
            nom_cap,
            batch_col,
            project,
        )

    else:
        _run(name, debug, silent)


def _run_from_db(
    name,
    debug,
    silent,
    raw,
    cellpyfile,
    minimal,
    nom_cap,
    batch_col,
    project,
):
    cli_api.run_from_db(
        name,
        debug=debug,
        silent=silent,
        raw=raw,
        cellpyfile=cellpyfile,
        minimal=minimal,
        nom_cap=nom_cap,
        batch_col=batch_col,
        project=project,
        echo=typer.echo,
    )


def _run_journal(file_name, debug, silent, raw, cellpyfile, minimal, nom_cap):
    cli_api.run_journal(
        file_name,
        debug=debug,
        silent=silent,
        raw=raw,
        cellpyfile=cellpyfile,
        minimal=minimal,
        nom_cap=nom_cap,
        echo=typer.echo,
    )


def _run_list(batchfiledir):
    cli_api.list_journals(batchfiledir, echo=typer.echo)


def _run_journals(folder_name, debug, silent, raw, cellpyfile, minimal):
    cli_api.run_journals(
        folder_name,
        debug=debug,
        silent=silent,
        raw=raw,
        cellpyfile=cellpyfile,
        minimal=minimal,
        echo=typer.echo,
    )


def _run_project(our_new_project, **kwargs):
    cli_api.run_project(our_new_project, echo=typer.echo, **kwargs)


def _run(name, debug, silent):
    typer.echo(f"running {name}")
    typer.echo(f" --debug [{debug}]")
    typer.echo(f" --silent [{silent}]")
    typer.echo("[cellpy]: sorry, I am not allowed to run this on my own")


def _run_db(debug, silent):
    cli_api.open_db_editor(debug=debug, silent=silent, echo=typer.echo)


# ----------------------- pull ---------------------------------------
@cli.command()
def pull(
    tests: Annotated[
        bool, typer.Option("--tests", "-t", help="Download test-files from repo.")
    ] = False,
    examples: Annotated[
        bool,
        typer.Option("--examples", "-e", help="Download example-files from repo."),
    ] = False,
    clone: Annotated[
        bool, typer.Option("--clone", "-c", help="Clone the full repo.")
    ] = False,
    directory: Annotated[
        Optional[str],
        typer.Option("--directory", "-d", help="Save into custom directory DIR"),
    ] = None,
    password: Annotated[
        Optional[str],
        typer.Option("--password", "-p", help="Password option for the repo"),
    ] = None,
):
    """Download examples or tests from the big internet (needs git)."""
    if directory is not None:
        typer.echo(f"[cellpy] (pull) custom directory: {directory}")
    else:
        directory = pathlib.Path(config.paths.examplesdir)

    if password is not None:
        typer.echo("DEV MODE: password provided")
    if clone:
        _clone_repo(directory, password)
    else:
        if tests:
            _pull_tests(directory, password)
        if examples:
            _pull_examples(directory, password)
        else:
            typer.echo(
                f"[cellpy] (pull) Nothing selected for pulling. "
                f"Please select an option (--tests,--examples, -clone, ...) "
            )


def _clone_repo(directory, password):
    directory = pathlib.Path(directory)
    txt = "[cellpy] The plan is that this "
    txt += "[cellpy] cmd will pull (clone) the cellpy repo.\n"
    txt += "[cellpy] For now it only prints the link to the git-hub\n"
    txt += "[cellpy] repository:\n"
    txt += "[cellpy]\n"
    txt += "[cellpy] https://github.com/jepegit/cellpy.git\n"
    txt += "[cellpy]\n"
    typer.echo(txt)


def _pull_tests(directory, pw=None):
    txt = (
        "[cellpy] (pull) Pulling tests from",
        " https://github.com/jepegit/cellpy.git",
    )
    typer.echo(txt)
    _pull(gdirpath="tests", rootpath=directory, pw=pw)
    _pull(gdirpath="testdata", rootpath=directory, pw=pw)


def _pull_examples(directory, pw):
    txt = (
        "[cellpy] (pull) Pulling examples from",
        " https://github.com/jepegit/cellpy.git",
    )
    typer.echo(txt)
    _pull(gdirpath="examples", rootpath=directory, pw=pw)


def _version():
    version_text = "[cellpy] version: " + str(VERSION)
    typer.echo(version_text)


def _configloc():
    _, config_file_name = prmreader.get_user_dir_and_dst()
    typer.echo(f"[cellpy] -> {config_file_name}")
    if not os.path.isfile(config_file_name):
        typer.echo("[cellpy] File does not exist!")
    else:
        return config_file_name


def _envloc():
    env_file_name = prmreader.get_env_file_name()
    typer.echo(f"[cellpy] (from config) -> {env_file_name}")
    if not os.path.isfile(env_file_name):
        return
    return env_file_name


def _dump_params():
    typer.echo("[cellpy] Running prmreader.info:\n")
    prmreader.info()


def _download_g_blob(name, local_path):
    import urllib.request

    dirs = local_path.parent
    if not dirs.is_dir():
        typer.echo(f"[cellpy] (pull) creating dir: {dirs}")
        dirs.mkdir(parents=True)
    print(f"[cellpy] (pull) downloading blob: {name.download_url}")
    filename, headers = urllib.request.urlretrieve(
        name.download_url, filename=local_path
    )
    typer.echo(f"[cellpy] (pull) downloaded blob: {filename}")


def _parse_g_subdir(stuff, repo, gdirpath):
    """recursive function for parsing repo subdirectories"""
    for f in repo.get_contents(gdirpath):
        if f.type != "dir":
            stuff.append(f)
        else:
            _parse_g_subdir(stuff, repo, f.path)


def _parse_g_dir(repo, gdirpath):
    """yields content of repo directory"""
    stuff = []
    _parse_g_subdir(stuff, repo, gdirpath)
    for f in stuff:
        yield f


def _get_user_name():
    return "jepegit"


def _get_pw(method):
    if method == "ask":
        return getpass.getpass()
    elif method == "env":
        return os.environ.get(GITHUB_PWD_VAR_NAME, None)

    else:
        return None


def _pull(gdirpath="examples", rootpath=None, u=None, pw=None):
    if rootpath is None:
        rootpath = config.paths.examplesdir

    rootpath = pathlib.Path(rootpath)

    ndirpath = rootpath / gdirpath

    if pw is not None:
        typer.echo(" DEV MODE ".center(80, "-"))
        u = _get_user_name()
        if pw == "ask":
            typer.echo("   - ask for password")
            pw = _get_pw(pw)
        elif pw == "env":
            typer.echo("   - check environ for password ")
            pw = _get_pw(pw)
            typer.echo("   - got something")
            if pw is None:
                typer.echo("   - only None")
                u = None

    g = Github(u, pw)
    try:
        repo = g.get_repo(REPO)
    except github.RateLimitExceededException:
        typer.echo("   - rate limit exceeded")
        typer.echo("   - waiting 60 seconds, and trying only once more")
        typer.echo(
            "   - hint! you can check status directly using the github api, e.g. "
        )
        typer.echo("     $ curl -i https://api.github.com/users/USERNAME")
        typer.echo("   - press ctrl-c to abort")
        time.sleep(60)
        repo = g.get_repo(REPO)

    typer.echo(f"[cellpy] (pull) pulling {gdirpath}")
    typer.echo(f"[cellpy] (pull) -> {ndirpath}")

    if not ndirpath.is_dir():
        typer.echo(f"[cellpy] (pull) creating dir: {ndirpath}")
        ndirpath.mkdir(parents=True)

    for gfile in _parse_g_dir(repo, gdirpath):
        gfilename = pathlib.Path(gfile.path)
        nfilename = rootpath / gfilename
        try:
            _download_g_blob(gfile, nfilename)
        except github.RateLimitExceededException:
            typer.echo("   - rate limit exceeded")
            typer.echo("   - waiting 60 seconds, and trying only once more")
            typer.echo("   - press ctrl-c to abort")
            time.sleep(60)
            _download_g_blob(gfile, nfilename)


def _get_default_template():
    template = "standard"
    try:
        template = config.batch.template
    except:
        logging.debug("You dont have any default template defined in you .conf file")
    return template


def _read_local_templates(local_templates_path=None):
    if local_templates_path is None:
        local_templates_path = pathlib.Path(config.paths.templatedir)
    templates = {}
    for p in list(local_templates_path.rglob("cellpy_cookie*.zip")):
        label = p.stem.strip()[len("cellpy_cookie_") :]
        templates[label] = (str(p), None)
    logging.debug(f"Found the following templates: {templates}")
    return templates


# ----------------------- new ----------------------------------------
@cli.command()
def new(
    template: Annotated[
        Optional[str], typer.Option("--template", "-t", help="Provide template name.")
    ] = None,
    directory: Annotated[
        Optional[str],
        typer.Option("--directory", "-d", help="Create in custom directory."),
    ] = None,
    project: Annotated[
        Optional[str],
        typer.Option(
            "--project", "-p", help="Provide project name (i.e. sub-directory name)."
        ),
    ] = None,
    experiment: Annotated[
        Optional[str],
        typer.Option(
            "--experiment", "-e", help="Provide experiment name (i.e. lookup-value)."
        ),
    ] = None,
    local_user_template: Annotated[
        bool,
        typer.Option(
            "--local-user-template",
            "-u",
            help="Use local template from the templates directory.",
        ),
    ] = False,
    serve_: Annotated[
        bool, typer.Option("--serve", "-s", help="Run Jupyter.")
    ] = False,
    run_: Annotated[
        bool,
        typer.Option(
            "--run",
            "-r",
            help="Use PaperMill to run the notebook(s) from the template (will only work properly if "
            "the notebooks can be sorted in correct run-order by 'sorted' and "
            "cellpy can find the jupyter executable).",
        ),
    ] = False,
    lab: Annotated[
        bool,
        typer.Option(
            "--lab", "-j", help="Use Jupyter Lab instead of Notebook when serving."
        ),
    ] = False,
    jupyter_executable: Annotated[
        Optional[str],
        typer.Option("--jupyter-executable", help="Jupyter executable."),
    ] = None,
    list_: Annotated[
        bool,
        typer.Option("--list", "-l", help="List available templates and exit."),
    ] = False,
):
    """Set up a batch experiment (might need git installed)."""
    _new(
        template,
        directory=directory,
        project_dir=project,
        session_id=experiment,
        local_user_template=local_user_template,
        serve_=serve_,
        run_=run_,
        lab=lab,
        executable=jupyter_executable,
        list_=list_,
    )


def _new(
    template: str,
    directory: Union[Path, str, None] = None,
    project_dir: Union[str, None] = None,
    local_user_template: bool = False,
    serve_: bool = False,
    run_: bool = False,
    lab: bool = False,
    list_: bool = False,
    executable: Union[str, None] = None,
    session_id: str = "experiment_001",
    no_input: bool = False,
    cookie_directory: str = "",
    local_templates_with_sub_directories: bool = False,
):
    """Set up a batch experiment (might need git installed).

    Args:
        template: short-name of template.
        directory: the directory for your cellpy projects.
        local_user_template: use local template if True.
        serve_: serve the notebook after creation if True.
        run_: run the notebooks using papermill if True.
        lab: use jupyter-lab instead of jupyter notebook if True.
        executable: path to jupyter executable.
        list_: list all available templates and return if True.
        project_dir: your project directory.
        session_id: the lookup value.
        no_input: accept defaults if True (only valid when providing project_dir and session_id)
        cookie_directory: name of the directory for your cookie (inside the repository or zip file).
        local_templates_with_sub_directories: use sub-directories in local templates if True.
    Returns:
        None
    """

    from cellpy.parameters import prms

    try:
        import cookiecutter.exceptions
        import cookiecutter.main
        import cookiecutter.prompt

    except ModuleNotFoundError:
        typer.echo("Could not import cookiecutter.")
        typer.echo("Try installing it, for example by writing:")
        typer.echo("\npython -m pip install cookiecutter\n")

    if list_:
        typer.echo(f"\n[cellpy] batch templates")

        default_template = _get_default_template()
        local_templates = _read_local_templates()
        local_templates_path = config.paths.templatedir
        registered_templates = REGISTERED_TEMPLATES
        typer.echo(f"[cellpy] - default: {default_template}")
        typer.echo("[cellpy] - registered templates (on github):")
        for label, link in registered_templates.items():
            typer.echo(f"\t\t{label:18s} {link}")

        if local_templates:
            typer.echo(f"[cellpy] - local templates ({local_templates_path}):")
            for label, link in local_templates.items():
                typer.echo(f"\t\t{label:18s} {link}")
        else:
            typer.echo(f"[cellpy] - local templates ({local_templates_path}): none")

        return

    if project_dir is None or session_id is None:
        no_input = False

    if not template:
        template = _get_default_template()

    if lab:
        server = "lab"
    else:
        server = "notebook"

    typer.echo(f"Template: {template}")
    if local_user_template:
        # forcing using local template
        templates = _read_local_templates()

        if not templates:
            typer.echo(
                "You asked me to use a local template, but you have none. Aborting."
            )
            return
    else:
        templates = REGISTERED_TEMPLATES
        if local_templates := _read_local_templates():
            templates.update(local_templates)

    if not template.lower() in templates.keys():
        typer.echo("This template does not exist. Aborting.")
        return

    if directory is None:
        logging.debug("no dir given")
        directory = config.paths.notebookdir

    if not os.path.isdir(directory):
        typer.echo("Sorry. This did not work as expected!")
        typer.echo(f" - {directory} does not exist")
        return

    directory = Path(directory)
    selected_project_dir = None

    if project_dir:
        selected_project_dir = directory / project_dir
        if not selected_project_dir.is_dir():
            if cookiecutter.prompt.read_user_yes_no(
                f"{project_dir} does not exist. Create?", "yes"
            ):
                os.mkdir(selected_project_dir)
                typer.echo(f"Created {selected_project_dir}")

            else:
                selected_project_dir = None
                typer.echo("Select another directory instead")
    CREATE_NEW_DIR = "Create new project..."
    if not selected_project_dir:
        project_dirs = [
            d.name
            for d in directory.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        project_dirs.insert(0, CREATE_NEW_DIR)

        project_dir = cookiecutter.prompt.read_user_choice(
            "project folder", project_dirs
        )

        if project_dir == CREATE_NEW_DIR:
            default_name = "cellpy_project"
            temp_default_name = default_name
            for j in range(999):
                if temp_default_name in project_dirs:
                    temp_default_name = default_name + str(j + 1).zfill(3)
                else:
                    default_name = temp_default_name
                    break

            project_dir = cookiecutter.prompt.read_user_variable(
                "New name", default_name
            )
            try:
                os.mkdir(directory / project_dir)
                typer.echo(f"created {project_dir}")
            except FileExistsError:
                typer.echo("OK - but this directory already exists!")
        selected_project_dir = directory / project_dir

    # get a list of all folders
    existing_projects = os.listdir(selected_project_dir)

    os.chdir(selected_project_dir)
    cellpy_version = cellpy.__version__

    try:
        selected_template, cookie_dir = templates[template.lower()]

        if cookie_directory:
            cookie_dir = cookie_directory
        if not cookie_dir:
            # if cookie_dir is not set, use the template name
            if not local_user_template:
                cookie_dir = template.lower()
            elif local_templates_with_sub_directories:
                cookie_dir = template.lower()

        author_name = _get_author_name()
        cookiecutter.main.cookiecutter(
            selected_template,
            extra_context={
                "author_name": author_name,
                "project_name": project_dir,
                "cellpy_version": cellpy_version,
                "session_id": session_id,
            },
            no_input=no_input,
            directory=cookie_dir,
        )
    except cookiecutter.exceptions.OutputDirExistsException as e:
        typer.echo("Sorry. This did not work as expected!")
        typer.echo(" - cookiecutter refused to create the project")
        typer.echo(e)

    if serve_:
        os.chdir(directory)
        _serve(server, executable)

    elif run_:
        typer.echo("WARNING - experimental feature - use at your own risk")
        input("Press Enter to continue...")
        try:
            import papermill as pm  # type: ignore
        except ImportError:
            typer.echo(
                "[cellpy]: You need to install papermill for automatically execute the notebooks."
            )
            typer.echo("[cellpy]: You can install it using pip like this:")
            typer.echo(" >> pip install papermill")
            return
        new_existing_projects = os.listdir(selected_project_dir)
        our_new_projects = list(set(new_existing_projects) - set(existing_projects))

        if not len(our_new_projects):
            typer.echo(
                "[cellpy]: Sorry, could not deiced what is the new project "
                "- so I don't dare to try to execute automatically."
            )
            return
        our_new_project = selected_project_dir / our_new_projects[0]

        _run_project(our_new_project)


def _get_author_name():
    """Get the name of the author."""
    try:
        import getpass

        author_name = getpass.getuser()
    except Exception as e:
        typer.echo("Could not get the author name")
        typer.echo(e)
        author_name = "unknown"
    return author_name


def _serve(server, executable=None):
    typer.echo(f"serving with jupyter {server}")
    # TODO: search for jupyter and find the right one
    if executable is None:
        executable = "jupyter"
    subprocess.run([executable, server], check=True)
    typer.echo("Finished serving.")


# ----------------------- serve ---------------------------------------
@cli.command()
def serve(
    lab: Annotated[
        bool,
        typer.Option("--lab", "-l", help="Use Jupyter Lab instead of Notebook"),
    ] = False,
    directory: Annotated[
        Optional[str],
        typer.Option("--directory", "-d", help="Start in custom directory DIR"),
    ] = None,
    executable: Annotated[
        Optional[str],
        typer.Option(
            "--executable",
            "-e",
            help="Custom Jupyter executable (needed if Jupyter is not in the same env as cellpy)",
        ),
    ] = None,
):
    """Start a Jupyter server."""

    from cellpy.parameters import prms

    if directory is None:
        directory = config.paths.notebookdir
    elif directory == "home":
        directory = Path().home()
    elif directory == "here":
        directory = Path(os.getcwd())

    if not os.path.isdir(directory):
        typer.echo("Sorry. This did not work as expected!")
        typer.echo(f" - {directory} does not exist")
        return

    if lab:
        server = "lab"
    else:
        server = "notebook"

    os.chdir(directory)
    _serve(server, executable=executable)


# `setup` is the only group; the rest register themselves with @cli.command().
cli.add_typer(setup_app, name="setup")


@cli.command()
def convert(
    old_h5: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    new_h5: Annotated[Optional[Path], typer.Argument(dir_okay=False)] = None,
    to: Annotated[
        Optional[str],
        typer.Option(
            "--to",
            help="Target format: v9 (zip-of-parquet .cellpy) or v8 (legacy "
            "HDF5). Inferred from NEW_H5's suffix when not given, else v9.",
        ),
    ] = None,
):
    """Upgrade a legacy cellpy-file to a current on-disk format."""
    try:
        cli_api.convert(old_h5, new_h5, to=to, echo=typer.echo)
    except ValueError as exc:
        typer.echo(f"[cellpy] (convert) {exc}")
        raise typer.Exit(code=2)


# tests etc
def _main_pull():
    if sys.platform == "win32":
        rootpath = pathlib.Path(r"C:\Temp\cellpy_user")
    else:
        rootpath = pathlib.Path("/Users/jepe/scripting/tmp/cellpy_test_user")
    _pull_examples(rootpath, pw="env")
    _pull_tests(rootpath, pw="env")
    # _pull(gdirpath="examples", rootpath=rootpath, u="ask", pw="ask")
    # _pull(gdirpath="tests", rootpath=rootpath, u="ask", pw="ask")
    # _pull(gdirpath="testdata", rootpath=rootpath, u="ask", pw="ask")


def _main():
    file_name = prmreader.create_custom_init_filename()
    typer.echo(file_name)
    user_directory, destination_file_name = prmreader.get_user_dir_and_dst(file_name)
    typer.echo(user_directory)
    typer.echo(destination_file_name)
    typer.echo("trying to save it")
    save_prm_file(destination_file_name + "_dummy")

    typer.echo(" Testing setup ".center(80, "="))
    # `setup` is a plain function under Typer, not a self-invoking Click
    # command, so drive it through the app the way a user would.
    from typer.testing import CliRunner

    CliRunner().invoke(cli, ["setup", "--interactive", "--reset"])


def _cli_setup_interactive():
    from typer.testing import CliRunner

    if sys.platform == "win32":
        root_dir = r"C:\Temp\cellpy_user"
    else:
        root_dir = "/Users/jepe/scripting/tmp/cellpy_test_user"
    testuser = "tester"
    init_filename = prmreader.create_custom_init_filename(testuser)
    dst_file = get_dst_file(root_dir, init_filename)
    init_file = pathlib.Path(dst_file)
    opts = list()
    opts.append("setup")
    opts.append("-i")
    # opts.append("-nr")
    opts.append("-r")
    opts.extend(["-d", root_dir])
    opts.extend(["-t", testuser])

    input_str = "\n"  # out
    input_str += "\n"  # rawdatadir
    input_str += "\n"  # cellpyfiles
    input_str += "\n"  # log
    input_str += "\n"  # examples
    input_str += "\n"  # dbfolder
    input_str += "\n"  # dbfile
    runner = CliRunner()
    result = runner.invoke(cli, opts, input=input_str)

    typer.echo(" out ".center(80, "."))
    typer.echo(result.output)
    from pprint import pprint

    pprint(config.paths)
    typer.echo(" conf-file ".center(80, "."))
    typer.echo(init_file)
    typer.echo()
    with init_file.open() as f:
        for line in f.readlines():
            typer.echo(line.strip())


def _check_it(var=None):
    import pathlib
    import sys

    p_env = pathlib.Path(sys.prefix)
    print(p_env.name)
    new(list_=True)
    u1 = os.getlogin()
    u2 = os.path.expanduser("~")
    u3 = os.environ.get("USERNAME")
    u4 = _get_author_name()
    u5 = _get_user_name()

    print(u1)
    print(u2)
    print(u3)
    print(u4)
    print(u5)
    print(cellpy.parameters.__file__)
    print(pathlib.Path(cellpy.parameters.__file__).parent)
    # check_it()
    # typer.echo("\n\n", " RUNNING MAIN PULL ".center(80, "*"), "\n")
    _main_pull()
    # typer.echo("ok")


def _check_info_check():
    """Check your cellpy installation."""
    _check()


if __name__ == "__main__":
    _check_info_check()
