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
from typing import Union
import urllib
from pathlib import Path

import click
import pkg_resources
from github import Github

import cellpy._version
from cellpy.exceptions import ConfigFileNotWritten
from cellpy.parameters import prmreader
from cellpy.parameters.internal_settings import OTHERPATHS
from cellpy.internals.core import OtherPath

VERSION = cellpy._version.__version__
REPO = "jepegit/cellpy"
USER = "jepegit"
GITHUB_PWD_VAR_NAME = "GD_PWD"
DEFAULT_EDITOR = 'vim'
EDITORS = {'Windows': 'notepad'}


def save_prm_file(prm_filename):
    """saves (writes) the prms to file"""
    prmreader._write_prm_file(prm_filename)


def get_package_prm_dir():
    """gets the folder where the cellpy package lives"""
    prm_dir = pkg_resources.resource_filename("cellpy", "parameters")
    return pathlib.Path(prm_dir)


def get_default_config_file_path(init_filename=None):
    """gets the path to the default config-file"""
    prm_dir = get_package_prm_dir()
    if not init_filename:
        init_filename = prmreader.DEFAULT_FILENAME
    src = prm_dir / init_filename
    return src


def get_dst_file(user_dir, init_filename):
    user_dir = pathlib.Path(user_dir)
    dst_file = user_dir / init_filename
    return dst_file


def check_if_needed_modules_exists():
    pass


def modify_config_file():
    pass


def create_cellpy_folders():
    pass


@click.group("cellpy")
def cli():
    pass


# ----------------------- setup --------------------------------------
@click.command()
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    default=False,
    help="Allows you to specify div. folders and setting.",
)
@click.option(
    "--not-relative",
    "-nr",
    is_flag=True,
    default=False,
    help="If root-dir is given, put it directly in the root (/) folder"
    " i.e. don't put it in your home directory. Defaults to False. Remark"
    " that if you specifically write a path name instead of selecting the"
    " suggested default, the path you write will be used as is.",
)
@click.option(
    "--dry-run",
    "-dr",
    is_flag=True,
    default=False,
    help="Run setup in dry mode (only print - do not execute). This is"
    " typically used when developing and testing cellpy. Defaults to"
    " False.",
)
@click.option(
    "--reset",
    "-r",
    is_flag=True,
    default=False,
    help="Do not suggest path defaults based on your current configuration-file",
)
@click.option(
    "--root-dir",
    "-d",
    default=None,
    type=click.Path(),
    help="Use custom root dir. If not given, your home directory"
    " will be used as the top level where cellpy-folders"
    " will be put. The folder path must follow"
    " directly after this option (if used). Example:\n"
    " $ cellpy setup -d 'MyDir'",
)
@click.option(
    "--folder-name",
    "-n",
    default=None,
    type=click.Path(),
    help="",
)
@click.option(
    "--test_user", "-t", default=None, help="Fake name for fake user (for testing)"
)
def setup(interactive, not_relative, dry_run, reset, root_dir, folder_name, test_user):
    """This will help you to set up cellpy."""

    click.echo("[cellpy] (setup)")
    click.echo(f"[cellpy] root-dir: {root_dir}")

    # generate variables
    init_filename = prmreader.create_custom_init_filename()
    user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)

    if dry_run:
        click.echo("Create custom init filename and get user_dir and destination")
        click.echo(f"Got the following parameters:")
        click.echo(f" - init_filename: {init_filename}")
        click.echo(f" - user_dir: {user_dir}")
        click.echo(f" - dst_file: {dst_file}")
        click.echo(f" - not_relative: {not_relative}")

    if root_dir and not interactive:
        click.echo("[cellpy] custom root-dir can only be used in interactive mode")
        click.echo("[cellpy] -> setting interactive mode")
        interactive = True

    if not root_dir:
        root_dir = user_dir
        # root_dir = pathlib.Path(os.getcwd())
    root_dir = pathlib.Path(root_dir)

    if dry_run:
        click.echo(f" - root_dir: {root_dir}")

    if test_user:
        click.echo(f"[cellpy] (setup) DEV-MODE test_user: {test_user}")
        init_filename = prmreader.create_custom_init_filename(test_user)
        user_dir = root_dir
        dst_file = get_dst_file(user_dir, init_filename)
        click.echo(f"[cellpy] (setup) DEV-MODE user_dir: {user_dir}")
        click.echo(f"[cellpy] (setup) DEV-MODE dst_file: {dst_file}")

    if not pathlib.Path(dst_file).is_file():
        click.echo(f"[cellpy] {dst_file} not found -> I will make one for you!")
        reset = True

    if interactive:
        click.echo(" interactive mode ".center(80, "-"))
        _update_paths(
            custom_dir=root_dir,
            relative_home=not not_relative,
            default_dir=folder_name,
            dry_run=dry_run,
            reset=reset,
        )
        _write_config_file(user_dir, dst_file, init_filename, dry_run)
        _check(dry_run=dry_run)

    else:
        if reset:
            _update_paths(
                user_dir,
                False,
                default_dir=folder_name,
                dry_run=dry_run,
                reset=True,
                silent=True,
            )
        _write_config_file(user_dir, dst_file, init_filename, dry_run)
        _check(dry_run=dry_run)


def _update_paths(
    custom_dir=None,
    relative_home=True,
    reset=False,
    dry_run=False,
    default_dir=None,
    silent=False,
):
    # please, refactor me :-(

    h = prmreader.get_user_dir()

    if default_dir is None:
        default_dir = "cellpy_data"

    if dry_run:
        click.echo(f" - default_dir: {default_dir}")
        click.echo(f" - custom_dir: {custom_dir}")
        click.echo(f" - retalive_home: {relative_home}")

    if custom_dir:
        reset = True
        if relative_home:
            h = h / custom_dir
        if not custom_dir.parts[-1] == default_dir:
            h = h / default_dir

    if not reset:
        outdatadir = pathlib.Path(prmreader.prms.Paths.outdatadir)
        rawdatadir = OtherPath(prmreader.prms.Paths.rawdatadir)
        cellpydatadir = OtherPath(prmreader.prms.Paths.cellpydatadir)
        filelogdir = pathlib.Path(prmreader.prms.Paths.filelogdir)
        examplesdir = pathlib.Path(prmreader.prms.Paths.examplesdir)
        db_path = pathlib.Path(prmreader.prms.Paths.db_path)
        db_filename = prmreader.prms.Paths.db_filename
        notebookdir = pathlib.Path(prmreader.prms.Paths.notebookdir)
        batchfiledir = pathlib.Path(prmreader.prms.Paths.batchfiledir)
        templatedir = pathlib.Path(prmreader.prms.Paths.templatedir)
        instrumentdir = pathlib.Path(prmreader.prms.Paths.instrumentsdir)
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
        click.echo(f" - base (h): {h}")

    if not silent:
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
            _create_dir(d)
        else:
            click.echo(f"dry run (so I did not create {d})")

    # update config-file based on suggestions
    prmreader.prms.Paths.outdatadir = str(outdatadir)
    prmreader.prms.Paths.rawdatadir = str(rawdatadir)
    prmreader.prms.Paths.cellpydatadir = str(cellpydatadir)
    prmreader.prms.Paths.filelogdir = str(filelogdir)
    prmreader.prms.Paths.examplesdir = str(examplesdir)
    prmreader.prms.Paths.db_path = str(db_path)
    prmreader.prms.Paths.db_filename = str(db_filename)
    prmreader.prms.Paths.notebookdir = str(notebookdir)
    prmreader.prms.Paths.batchfiledir = str(batchfiledir)
    prmreader.prms.Paths.templatedir = str(templatedir)
    prmreader.prms.Paths.instrumentdir = str(instrumentdir)


def _ask_about_path(q, p):
    click.echo(f"\n[cellpy] (setup) input {q}")
    click.echo(f"[cellpy] (setup) current: {p}")
    new_path = input("[cellpy] (setup) [KEEP/new value] >>> ").strip()
    if not new_path:
        new_path = p
    return pathlib.Path(new_path)


def _ask_about_otherpath(q, p):
    click.echo(f"\n[cellpy] (setup) input {q}")
    click.echo(f"[cellpy] (setup) current: {p}")
    new_path = input("[cellpy] (setup) [KEEP/new value] >>> ").strip()
    if not new_path:
        new_path = p
    return OtherPath(new_path)


def _ask_about_name(q, n):
    click.echo(f"\n[cellpy] (setup) input {q}")
    click.echo(f"[cellpy] (setup) current: {n}")
    new_name = input("[cellpy] (setup) [KEEP/new value] >>> ").strip()
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
                click.echo(f"[cellpy] (setup) Created {o}")
            except FileExistsError:
                click.echo(f"[cellpy] (setup) {o} already exists.")
            except FileNotFoundError:
                click.echo(f"[cellpy] (setup) {o} not available.")
            except Exception as e:
                click.echo(f"[cellpy] (setup) WARNING! Could not create {o}.")
                logging.debug(e)
                click.echo(f"[cellpy] (setup) ...continuing anyway.")
        else:
            click.echo(f"[cellpy] (setup) Could not create {o}")
    return o


def _check_import_cellpy():
    try:
        import cellpy
        from cellpy import log
        from cellpy.readers import cellreader

        return True
    except:
        return False


def _check_import_pyodbc():
    import platform

    from cellpy.parameters import prms

    ODBC = prms._odbc
    SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver

    use_subprocess = prms.Instruments.Arbin.use_subprocess
    detect_subprocess_need = prms.Instruments.Arbin.detect_subprocess_need
    click.echo(f" reading prms")
    click.echo(f" - ODBC: {ODBC}")
    click.echo(f" - SEARCH_FOR_ODBC_DRIVERS: {SEARCH_FOR_ODBC_DRIVERS}")
    click.echo(f" - use_subprocess: {use_subprocess}")
    click.echo(f" - detect_subprocess_need: {detect_subprocess_need}")
    click.echo(f" - stated office version: {prms.Instruments.Arbin.office_version}")

    click.echo(" checking system")
    is_posix = False
    is_macos = False
    if os.name == "posix":
        is_posix = True
        click.echo(f" - running on posix")
    current_platform = platform.system()
    if current_platform == "Darwin":
        is_macos = True
        click.echo(f" - running on a mac")

    python_version, os_version = platform.architecture()
    click.echo(f" - python version: {python_version}")
    click.echo(f" - os version: {os_version}")

    if not is_posix:
        if not prms.Instruments.Arbin.sub_process_path:
            sub_process_path = str(prms._sub_process_path)
        else:
            sub_process_path = str(prms.Instruments.Arbin.sub_process_path)
        click.echo(f" stated path to sub-process: {sub_process_path}")
        if not os.path.isfile(sub_process_path):
            click.echo(f" - OBS! missing")

    if is_posix:
        click.echo(" checking existence of mdb-export")
        sub_process_path = "mdb-export"
        from subprocess import PIPE, run

        command = ["command", "-v", sub_process_path]

        try:
            result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            if result.returncode == 0:
                click.echo(f" - found it: {result.stdout}")
            else:
                click.echo(f" - failed finding it")

            if is_macos:
                driver = "/usr/local/lib/libmdbodbc.dylib"
                click.echo(f" looks like you are on a mac (driver set to\n {driver})")
                if not os.path.isfile(driver):
                    click.echo(" - but cannot find it!")
                    return False
            return True

        except AssertionError:
            click.echo(" - not found")
            return False

    # not posix - checking for odbc drivers
    # 1) checking if you have defined one
    try:
        driver = prms.Instruments.Arbin.odbc_driver
        if not driver:
            raise AttributeError
        click.echo("You have defined an odbc driver in your conifg file")
        click.echo(f"driver: {driver}")
    except AttributeError:
        click.echo("FYI: you have not defined any odbc_driver(s)")
        click.echo(
            "(The name of the driver from the configuration file is "
            "used as a backup when cellpy cannot locate a driver by itself)"
        )

    use_ado = False

    if ODBC == "ado":
        use_ado = True
        click.echo(" you stated that you prefer the ado loader")
        click.echo(" checking if adodbapi is installed")
        try:
            import adodbapi as dbloader
        except ImportError:
            use_ado = False
            click.echo(" Failed! Try setting pyodbc as your loader or install")
            click.echo(" adodbapi (http://adodbapi.sourceforge.net/)")

    if not use_ado:
        if ODBC == "pyodbc":
            click.echo(" you stated that you prefer the pyodbc loader")
            try:
                import pyodbc as dbloader
            except ImportError:
                click.echo(" Failed! Could not import it.")
                click.echo(" Try 'pip install pyodbc'")
                dbloader = None

        elif ODBC == "pypyodbc":
            click.echo(" you stated that you prefer the pypyodbc loader")
            try:
                import pypyodbc as dbloader
            except ImportError:
                click.echo(" Failed! Could not import it.")
                click.echo(" try 'pip install pypyodbc'")
                click.echo(" or set pyodbc as your loader in your prm file")
                click.echo(" (and install it)")
                dbloader = None

    click.echo(" searching for odbc drivers")
    try:
        drivers = [
            driver
            for driver in dbloader.drivers()
            if "Microsoft Access Driver" in driver
        ]
        click.echo(f"Found these: {drivers}")
        driver = drivers[0]
        click.echo(f"odbc driver: {driver}")
        return True

    except IndexError as e:
        logging.debug("Unfortunately, it seems the list of drivers is emtpy.")
        click.echo(
            "\nCould not find any odbc-drivers suitable for .res-type files. "
            "Check out the homepage of pydobc for info on installing drivers"
        )
        click.echo(
            "One solution that might work is downloading "
            "the Microsoft Access database engine "
            "(in correct bytes (32 or 64)) "
            "from:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=13255"
        )
        click.echo("Or install mdbtools and set it up (check the cellpy docs for help)")
        click.echo("\n")
        return False


def _check_config_file():
    prm_file_name = _configloc()
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
            click.echo(f"{k}: {value}")
            # splitting this into two if-statements to make it easier to debug if OtherPath changes
            if k in OTHERPATHS:
                print(f"skipping check for external {k} (for now)")
                # if not OtherPath(
                #     value
                # ).is_dir():  # Assuming OtherPath returns True if it is external.
                #     missing += 1
                #     click.echo("COULD NOT CONNECT!")
                #     click.echo(f"({value} is not a directory)")
            elif value and not pathlib.Path(value).is_dir():
                missing += 1
                click.echo("COULD NOT CONNECT!")
                click.echo(f"({value} is not a directory)")
            if not value:
                missing += 1
                click.echo("MISSING")

        value = prm_paths.get("db_filename", None)
        click.echo(f"db_filename: {value}")
        if not value:
            missing += 1
            click.echo("MISSING")

        if missing:
            return False
        else:
            return True

    except Exception as e:
        click.echo("Following error occurred:")
        click.echo(e)
        return False


def _check(dry_run=False):
    click.echo(" checking ".center(80, "="))
    if dry_run:
        click.echo("*** dry-run: skipping the test")
        return
    failed_checks = 0
    number_of_checks = 0

    def sub_check(check_type, check_func):
        failed = 0
        click.echo(f"[cellpy] * - Checking {check_type}")
        if check_func():
            click.echo(f"[cellpy] -> succeeded!")
        else:
            click.echo("f[cellpy] -> failed!!!!")
            failed = 1
        click.echo(80 * "-")
        return failed

    check_types = ["cellpy imports", "importing pyodbc", "configuration (prm) file"]
    check_funcs = [_check_import_cellpy, _check_import_pyodbc, _check_config_file]

    for ct, cf in zip(check_types, check_funcs):
        try:
            failed_checks += sub_check(ct, cf)
        except Exception as e:
            click.echo(f"[cellpy] check raised an exception ({e})")
        number_of_checks += 1
    succeeded_checks = number_of_checks - failed_checks
    if failed_checks > 0:
        click.echo(f"[cellpy] OH NO!!! You (or I) failed!")
        click.echo(f"[cellpy] Failed {failed_checks} out of {number_of_checks} checks.")
    else:
        click.echo(
            f"[cellpy] Succeeded {succeeded_checks} out of {number_of_checks} checks."
        )
    click.echo(80 * "=")


def _write_config_file(user_dir, dst_file, init_filename, dry_run):
    click.echo(" update configuration ".center(80, "-"))
    click.echo("[cellpy] (setup) Writing configurations to user directory:")
    click.echo(f"\n         {user_dir}\n")

    if os.path.isfile(dst_file):
        click.echo("[cellpy] (setup) File already exists!")
        click.echo("[cellpy] (setup) Keeping most of the old configuration parameters")
    try:
        if dry_run:
            click.echo(
                f"*** dry-run: skipping actual saving of {dst_file} ***", color="red"
            )
        else:
            click.echo(f"[cellpy] (setup) Saving file ({dst_file})")
            save_prm_file(dst_file)

    except ConfigFileNotWritten:
        click.echo("[cellpy] (setup) Something went wrong! Could not write the file")
        click.echo(
            "[cellpy] (setup) Trying to write a file"
            + f"called {prmreader.DEFAULT_FILENAME} instead"
        )

        try:
            user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
            if dry_run:
                click.echo(
                    f"*** dry-run: skipping actual saving of {dst_file} ***",
                    color="red",
                )
            else:
                save_prm_file(dst_file)

        except ConfigFileNotWritten:
            _txt = "[cellpy] (setup) No, that did not work either.\n"
            _txt += "[cellpy] (setup) Well, guess you have to talk to the developers."
            click.echo(_txt)
    else:
        click.echo(f"[cellpy] (setup) Configuration file written!")
        click.echo(
            f"[cellpy] (setup) OK! Now you can edit it. For example by "
            f"issuing \n\n         [your-favourite-editor] {init_filename}\n"
        )


def _get_default_editor():
    """
    Return the default text editor.

    This code is based on the `editor` library by @rec.
    """

    return os.environ.get('VISUAL') or (
        os.environ.get('EDITOR')
        or EDITORS.get(platform.system(), DEFAULT_EDITOR)
    )


# ----------------------- edit ---------------------------------------
@click.command()
@click.option(
    "--default-editor",
    "-e",
    default=None,
    type=str,
    help="try to use this editor instead",
)
@click.option("--debug", "-d", is_flag=True, help="Run in debug mode.")
@click.option("--silent", "-s", is_flag=True, help="Run in silent mode.")
@click.argument(
    "name",
    type=str,
    default=None,
    required=False,
)
def edit(name, default_editor, debug, silent):
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
        click.echo("unknown file")
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
    click.echo(f"[cellpy] (edit) Calling '{default_editor}'")
    try:
        subprocess.call(args)
    except:
        click.echo(f"[cellpy] (edit) Failed!")
        click.echo(
            "[cellpy] (edit) Try 'cellpy edit -e notepad.exe' if you are on Windows"
        )


# ----------------------- info ---------------------------------------
@click.command()
@click.option("--version", "-v", is_flag=True, help="Print version information.")
@click.option(
    "--configloc", "-l", is_flag=True, help="Print full path to the config file."
)
@click.option("--params", "-p", is_flag=True, help="Dump all parameters to screen.")
@click.option(
    "--check",
    "-c",
    is_flag=True,
    help="Do a sanity check to see if things" " works as they should.",
)
def info(version, configloc, params, check):
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

    if complete_info:
        _version()
        _configloc()


# ----------------------- run ----------------------------------------
@click.command()
@click.option(
    "--journal",
    "-j",
    is_flag=True,
    help="Run a batch job defined in the given journal-file",
)
@click.option("--key", "-k", is_flag=True, help="Run a batch job defined by batch-name")
@click.option(
    "--folder",
    "-f",
    is_flag=True,
    help="Run all batch jobs iteratively in a given folder",
)
@click.option(
    "--cellpy-project",
    "-p",
    is_flag=True,
    help="Use PaperMill to run the notebook(s) within the given project folder "
    "(will only work properly if the notebooks can be sorted in correct run-order by 'sorted'). "
    "Warning! since we are using `click` - the NAME will be 'converted' when it is loaded "
    "(same as print(name) does) - "
    "so you can't use backslash ('\\') as normal in windows (use either '/' or '\\\\' instead).",
)
@click.option("--debug", "-d", is_flag=True, help="Run in debug mode.")
@click.option("--silent", "-s", is_flag=True, help="Run in silent mode.")
@click.option("--raw", is_flag=True, help="Force loading raw-file(s).")
@click.option("--cellpyfile", is_flag=True, help="Force cellpy-file(s).")
@click.option("--minimal", is_flag=True, help="Minimal processing.")
@click.option(
    "--nom-cap",
    default=None,
    type=float,
    help="nominal capacity (used in calculating rates etc)",
)
@click.option(
    "--batch_col",
    default=None,
    type=str,
    help="batch column (if selecting running from db)",
)
@click.option(
    "--project",
    default=None,
    type=str,
    help="name of the project (if selecting running from db)",
)
@click.option("--list", "-l", "list_", is_flag=True, help="List batch-files.")
@click.argument("name", default="NONE")
def run(
    journal,
    key,
    folder,
    cellpy_project,
    debug,
    silent,
    raw,
    cellpyfile,
    minimal,
    nom_cap,
    batch_col,
    project,
    list_,
    name,
):
    """Run a cellpy process (e.g. a batch-job).

    You can use this to launch specific applications.

    Examples:

        run a batch job described in a journal file

           cellpy run -j my_experiment.json

    """
    if list_:
        _run_list(name)
        return

    if name == "NONE":
        click.echo(
            "Usage: cellpy run [OPTIONS] NAME\n"
            "Try 'cellpy run --help' for help.\n\n"
            "Error: Missing argument 'NAME'."
        )
        sys.exit(-1)

    if debug:
        click.echo("[cellpy] (run) debug mode on")

    if silent:
        click.echo("[cellpy] (run) silent mode on")

    click.echo("[cellpy]\n")

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
    click.echo(
        f"running from db \nkey={name}, batch_col={batch_col}, project={project}"
    )

    kwargs = dict()
    kwargs["name"] = name

    if debug:
        kwargs["default_log_level"] = "DEBUG"
    if not minimal:
        kwargs["export_raw"] = False
        kwargs["export_cycles"] = False
        kwargs["export_ica"] = False

    if batch_col is not None:
        kwargs["batch_col"] = batch_col
    if project is None:
        kwargs["project"] = "various"
    else:
        kwargs["project"] = project

    click.echo("Warming up ...")

    from cellpy.utils import batch

    click.echo("  - starting batch processing")
    b = batch.process_batch(
        force_raw_file=raw,
        force_cellpy=cellpyfile,
        nom_cap=nom_cap,
        backend="matplotlib",
        **kwargs,
    )

    if b is not None and not silent:
        print(b)
    click.echo("---")


def _run_journal(file_name, debug, silent, raw, cellpyfile, minimal, nom_cap):
    click.echo(f"running journal {file_name}")
    # click.echo(f" --debug [{debug}]")
    # click.echo(f" --silent [{silent}]")
    # click.echo(f" --raw [{raw}]")
    # click.echo(f" --cellpyfile [{cellpyfile}]")
    # click.echo(f" --minimal [{minimal}]")
    # click.echo(f" --nom_cap [{nom_cap}] {type(nom_cap)}")

    kwargs = dict()
    if debug:
        kwargs["default_log_level"] = "DEBUG"
    if not minimal:
        kwargs["export_raw"] = False
        kwargs["export_cycles"] = False
        kwargs["export_ica"] = False

    from cellpy import prms
    from cellpy.utils import batch

    batchfiledir = pathlib.Path(prms.Paths.batchfiledir)
    file = pathlib.Path(file_name)
    if not file.is_file():
        click.echo(f"file_name={file_name} not found - looking into batchfiledir")
        if not batchfiledir.is_dir():
            click.echo("batchfiledir not found - aborting")
            return
        file = batchfiledir / file.name

    if not file.is_file():
        click.echo(f"{file} not found - aborting")
        return

    b = batch.process_batch(
        file,
        force_raw_file=raw,
        force_cellpy=cellpyfile,
        nom_cap=nom_cap,
        backend="matplotlib",
        **kwargs,
    )
    if b is not None and not silent:
        print(b)
    click.echo("---")


def _run_list(batchfiledir):
    from cellpy import prms

    if batchfiledir == "NONE" or batchfiledir is None:
        batchfiledir = pathlib.Path(prms.Paths.batchfiledir)
    else:
        batchfiledir = pathlib.Path(batchfiledir).resolve()

    if batchfiledir.is_dir():
        click.echo(f"Content of '{batchfiledir}':\n")
        i = 0
        for i, f in enumerate(batchfiledir.glob("cellpy*.json")):
            click.echo(f"{f.name}")
        if i:
            print(f"\nnumber of batch-files located: {i}")
        else:
            print("No batch-files found in this directory.")
    else:
        click.echo(f"{batchfiledir} not found.")


def _run_journals(folder_name, debug, silent, raw, cellpyfile, minimal):
    click.echo(f"running journals in {folder_name}")
    # click.echo(f" --debug [{debug}]")
    # click.echo(f" --silent [{silent}]")
    # click.echo(f" --raw [{raw}]")
    # click.echo(f" --cellpyfile [{cellpyfile}]")
    # click.echo(f" --minimal [{minimal}]")

    kwargs = dict()
    if debug:
        kwargs["default_log_level"] = "DEBUG"
    if not minimal:
        kwargs["export_raw"] = False
        kwargs["export_cycles"] = False
        kwargs["export_ica"] = False

    from cellpy.utils import batch

    folder_name = pathlib.Path(folder_name).resolve()

    if not folder_name.is_dir():
        click.echo(f"{folder_name} not found - aborting")
        return

    batch.iterate_batches(
        folder_name, force_raw_file=raw, force_cellpy=cellpyfile, silent=True, **kwargs
    )
    click.echo("---")


def _run_project(our_new_project, **kwargs):
    try:
        import papermill as pm
    except ImportError:
        click.echo(
            "[cellpy]: You need to install papermill for automatically execute the notebooks."
        )
        click.echo("[cellpy]: You can install it using pip like this:")
        click.echo(" >> pip install papermill")
        return
    our_new_project = pathlib.Path(our_new_project)
    click.echo(f"[cellpy]: trying to run notebooks in {our_new_project}")
    notebooks = sorted(list(our_new_project.glob("*.ipynb")))
    for notebook in notebooks:
        click.echo(f"[cellpy - papermill] running {notebook.name}")
        pm.execute_notebook(notebook, notebook, parameters=kwargs)


def _run(name, debug, silent):
    click.echo(f"running {name}")
    click.echo(f" --debug [{debug}]")
    click.echo(f" --silent [{silent}]")
    click.echo("[cellpy]: sorry, I am not allowed to run this on my own")


def _run_db(debug, silent):
    import platform

    from cellpy import prms

    if not silent:
        click.echo(f"running database editor")
    if debug:
        click.echo("running in debug-mode, but nothing to tell")

    db_path = Path(prms.Paths.db_path) / prms.Paths.db_filename

    if platform.system() == "Windows":
        try:
            os.system(f'start excel "{str(db_path)}"')
        except Exception as e:
            click.echo("Something went wrong trying to open")
            click.echo(db_path)
            print()
            print(e)

    elif platform.system() == "Linux":
        click.echo("RUNNING LINUX")
        # not tested
        subprocess.check_call(["open", "-a", "Microsoft Excel", db_path])

    elif platform.system() == "Darwin":
        click.echo(f" - running on a mac")
        subprocess.check_call(["open", "-a", "Microsoft Excel", db_path])

    else:
        print("RUNNING SOMETHING ELSE")
        print(platform.system())
        # not tested
        subprocess.check_call(["open", "-a", "Microsoft Excel", db_path])


# ----------------------- pull ---------------------------------------
@click.command()
@click.option("--tests", "-t", is_flag=True, help="Download test-files from repo.")
@click.option(
    "--examples", "-e", is_flag=True, help="Download example-files from repo."
)
@click.option("--clone", "-c", is_flag=True, help="Clone the full repo.")
@click.option("--directory", "-d", default=None, help="Save into custom directory DIR")
@click.option("--password", "-p", default=None, help="Password option for the repo")
def pull(tests, examples, clone, directory, password):
    """Download examples or tests from the big internet (needs git)."""
    if directory is not None:
        click.echo(f"[cellpy] (pull) custom directory: {directory}")
    else:
        directory = pathlib.Path(prmreader.prms.Paths.examplesdir)

    if password is not None:
        click.echo("DEV MODE: password provided")
    if clone:
        _clone_repo(directory, password)
    else:
        if tests:
            _pull_tests(directory, password)
        if examples:
            _pull_examples(directory, password)
        else:
            click.echo(
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
    click.echo(txt)


def _pull_tests(directory, pw=None):
    txt = (
        "[cellpy] (pull) Pulling tests from",
        " https://github.com/jepegit/cellpy.git",
    )
    click.echo(txt)
    _pull(gdirpath="tests", rootpath=directory, pw=pw)
    _pull(gdirpath="testdata", rootpath=directory, pw=pw)


def _pull_examples(directory, pw):
    txt = (
        "[cellpy] (pull) Pulling examples from",
        " https://github.com/jepegit/cellpy.git",
    )
    click.echo(txt)
    _pull(gdirpath="examples", rootpath=directory, pw=pw)


def _version():
    txt = "[cellpy] version: " + str(VERSION)
    click.echo(txt)


def _configloc():
    _, config_file_name = prmreader.get_user_dir_and_dst()
    click.echo("[cellpy] ->%s" % config_file_name)
    if not os.path.isfile(config_file_name):
        click.echo("[cellpy] File does not exist!")
    else:
        return config_file_name


def _envloc():
    click.echo(f"[cellpy] ->{prmreader.get_env_file_name()}")
    if not os.path.isfile(prmreader.get_env_file_name()):
        click.echo("[cellpy] File does not exist!")
    else:
        return prmreader.get_env_file_name()


def _dump_params():
    click.echo("[cellpy] Dumping parameters to screen:\n")
    prmreader.info()


def _download_g_blob(name, local_path):
    import urllib.request

    dirs = local_path.parent
    if not dirs.is_dir():
        click.echo(f"[cellpy] (pull) creating dir: {dirs}")
        dirs.mkdir(parents=True)

    filename, headers = urllib.request.urlretrieve(
        name.download_url, filename=local_path
    )
    click.echo(f"[cellpy] (pull) downloaded blob: {filename}")


def _parse_g_dir(repo, gdirpath):
    """parses a repo directory two-levels deep"""
    for f in repo.get_contents(gdirpath):
        if f.type == "dir":
            for sf in repo.get_contents(f.path):
                yield sf
        else:
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
        rootpath = prmreader.prms.Paths.examplesdir

    rootpath = pathlib.Path(rootpath)

    ndirpath = rootpath / gdirpath

    if pw is not None:
        click.echo(" DEV MODE ".center(80, "-"))
        u = _get_user_name()
        if pw == "ask":
            click.echo("   - ask for password")
            pw = _get_pw(pw)
        elif pw == "env":
            click.echo("   - check environ for password ")
            pw = _get_pw(pw)
            click.echo("   - got something")
            if pw is None:
                click.echo("   - only None")
                u = None

    g = Github(u, pw)
    repo = g.get_repo(REPO)

    click.echo(f"[cellpy] (pull) pulling {gdirpath}")
    click.echo(f"[cellpy] (pull) -> {ndirpath}")

    if not ndirpath.is_dir():
        click.echo(f"[cellpy] (pull) creating dir: {ndirpath}")
        ndirpath.mkdir(parents=True)

    for gfile in _parse_g_dir(repo, gdirpath):
        gfilename = pathlib.Path(gfile.path)
        nfilename = rootpath / gfilename

        _download_g_blob(gfile, nfilename)


def _get_default_template():
    template = "standard"
    try:
        template = prmreader.prms.Batch.template
    except:
        logging.debug("You dont have any default template defined in you .conf file")
    return template


def _read_local_templates(local_templates_path=None):
    if local_templates_path is None:
        local_templates_path = pathlib.Path(prmreader.prms.Paths.templatedir)
    templates = {}
    for p in list(local_templates_path.rglob("cellpy_cookie*.zip")):
        label = p.stem.strip()[len("cellpy_cookie_") :]
        templates[label] = (str(p), None)
    logging.debug(f"Found the following templates: {templates}")
    return templates


# ----------------------- new ----------------------------------------
@click.command()
@click.option("--template", "-t", help="Provide template name.")
@click.option("--directory", "-d", default=None, help="Create in custom directory.")
@click.option(
    "--project",
    "-p",
    default=None,
    help="Provide project name (i.e. sub-directory name).",
)
@click.option(
    "--experiment",
    "-e",
    default=None,
    help="Provide experiment name (i.e. lookup-value).",
)
@click.option(
    "--local-user-template",
    "-u",
    is_flag=True,
    default=False,
    help="Use local template from the templates directory.",
)
@click.option("--serve", "-s", "serve_", is_flag=True, help="Run Jupyter.")
@click.option(
    "--run",
    "-r",
    "run_",
    is_flag=True,
    help="Use PaperMill to run the notebook(s) from the template "
    "(will only work properly if the notebooks can be sorted in correct run-order by 'sorted'.",
)
@click.option(
    "--lab",
    "-j",
    is_flag=True,
    help="Use Jupyter Lab instead of Notebook when serving.",
)
@click.option(
    "--list", "-l", "list_", is_flag=True, help="List available templates and exit."
)
def new(
    template,
    directory,
    project,
    experiment,
    local_user_template,
    serve_,
    run_,
    lab,
    list_,
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
    session_id: str = "experiment_001",
    no_input: bool = False,
    cookie_directory: str = "",
):
    """Set up a batch experiment (might need git installed).

    Args:
        template: short-name of template.
        directory: the directory for your cellpy projects.
        local_user_template: use local template if True.
        serve_: serve the notebook after creation if True.
        run_: run the notebooks using papermill if True.
        lab: use jupyter-lab instead of jupyter notebook if True.
        list_: list all available templates and return if True.
        project_dir: your project directory.
        session_id: the lookup value.
        no_input: accept defaults if True (only valid when providing project_dir and session_id)
        cookie_directory: name of the directory for your cookie (inside the repository or zip file).
    Returns:
        None
    """

    from cellpy.parameters import prms

    if list_:
        click.echo(f"\n[cellpy] batch templates")

        default_template = _get_default_template()
        local_templates = _read_local_templates()
        local_templates_path = prmreader.prms.Paths.templatedir
        registered_templates = prms._registered_templates
        click.echo(f"[cellpy] - default: {default_template}")
        click.echo("[cellpy] - registered templates (on github):")
        for label, link in registered_templates.items():
            click.echo(f"\t\t{label:18s} {link}")

        if local_templates:
            click.echo(f"[cellpy] - local templates ({local_templates_path}):")
            for label, link in local_templates.items():
                click.echo(f"\t\t{label:18s} {link}")
        else:
            click.echo(f"[cellpy] - local templates ({local_templates_path}): none")

        return

    if project_dir is None or session_id is None:
        no_input = False

    if not template:
        template = _get_default_template()

    if lab:
        server = "lab"
    else:
        server = "notebook"

    try:
        import cookiecutter.exceptions
        import cookiecutter.main
        import cookiecutter.prompt

    except ModuleNotFoundError:
        click.echo("Could not import cookiecutter.")
        click.echo("Try installing it, for example by writing:")
        click.echo("\npip install cookiecutter\n")

    click.echo(f"Template: {template}")
    if local_user_template:
        # forcing using local template
        templates = _read_local_templates()

        if not templates:
            click.echo(
                "You asked me to use a local template, but you have none. Aborting."
            )
            return
    else:
        templates = prms._registered_templates
        if local_templates := _read_local_templates():
            templates.update(local_templates)

    if not template.lower() in templates.keys():
        click.echo("This template does not exist. Aborting.")
        return

    if directory is None:
        logging.debug("no dir given")
        directory = prms.Paths.notebookdir

    if not os.path.isdir(directory):
        click.echo("Sorry. This did not work as expected!")
        click.echo(f" - {directory} does not exist")
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
                click.echo(f"Created {selected_project_dir}")

            else:
                selected_project_dir = None
                click.echo(f"Select another directory instead")

    if not selected_project_dir:
        project_dirs = [
            d.name
            for d in directory.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        project_dirs.insert(0, "[create new dir]")

        project_dir = cookiecutter.prompt.read_user_choice(
            "project folder", project_dirs
        )

        if project_dir == "[create new dir]":
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
                click.echo(f"created {project_dir}")
            except FileExistsError:
                click.echo("OK - but this directory already exists!")
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
            cookie_dir = template.lower()

        cookiecutter.main.cookiecutter(
            selected_template,
            extra_context={
                "author_name": os.getlogin(),
                "project_name": project_dir,
                "cellpy_version": cellpy_version,
                "session_id": session_id,
            },
            no_input=no_input,
            directory=cookie_dir,
        )
    except cookiecutter.exceptions.OutputDirExistsException as e:
        click.echo("Sorry. This did not work as expected!")
        click.echo(" - cookiecutter refused to create the project")
        click.echo(e)

    if serve_:
        os.chdir(directory)
        _serve(server)

    if run_:
        try:
            import papermill as pm
        except ImportError:
            click.echo(
                "[cellpy]: You need to install papermill for automatically execute the notebooks."
            )
            click.echo("[cellpy]: You can install it using pip like this:")
            click.echo(" >> pip install papermill")
            return
        new_existing_projects = os.listdir(selected_project_dir)
        our_new_projects = list(set(new_existing_projects) - set(existing_projects))

        if not len(our_new_projects):
            click.echo(
                "[cellpy]: Sorry, could not deiced what is the new project "
                "- so I don't dare to try to execute automatically."
            )
            return
        our_new_project = selected_project_dir / our_new_projects[0]

        _run_project(our_new_project)


def _serve(server):
    click.echo(f"serving with jupyter {server}")
    subprocess.run(["jupyter", server], check=True)
    click.echo("Finished serving.")


# ----------------------- serve ---------------------------------------
@click.command()
@click.option("--lab", "-l", is_flag=True, help="Use Jupyter Lab instead of Notebook")
@click.option("--directory", "-d", default=None, help="Start in custom directory DIR")
def serve(lab, directory):
    """Start a Jupyter server."""

    from cellpy.parameters import prms

    if directory is None:
        directory = prms.Paths.notebookdir
    elif directory == "home":
        directory = Path().home()
    elif directory == "here":
        directory = Path(os.getcwd())

    if not os.path.isdir(directory):
        click.echo("Sorry. This did not work as expected!")
        click.echo(f" - {directory} does not exist")
        return

    if lab:
        server = "lab"
    else:
        server = "notebook"

    os.chdir(directory)
    _serve(server)


cli.add_command(setup)
cli.add_command(info)
cli.add_command(edit)
cli.add_command(pull)
cli.add_command(run)
cli.add_command(new)
cli.add_command(serve)


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
    click.echo(file_name)
    user_directory, destination_file_name = prmreader.get_user_dir_and_dst(file_name)
    click.echo(user_directory)
    click.echo(destination_file_name)
    click.echo("trying to save it")
    save_prm_file(destination_file_name + "_dummy")

    click.echo(" Testing setup ".center(80, "="))
    setup(["--interactive", "--reset"])


def _cli_setup_interactive():
    from click.testing import CliRunner

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

    click.echo(" out ".center(80, "."))
    click.echo(result.output)
    from pprint import pprint

    pprint(prmreader.prms.Paths)
    click.echo(" conf-file ".center(80, "."))
    click.echo(init_file)
    click.echo()
    with init_file.open() as f:
        for line in f.readlines():
            click.echo(line.strip())


def check_it(var=None):
    import pathlib
    import sys

    p_env = pathlib.Path(sys.prefix)
    print(p_env.name)
    new(list_=True)


if __name__ == "__main__":
    u1 = os.getlogin()
    u2 = os.path.expanduser("~")
    u3 = os.environ.get("USERNAME")

    print(u1)
    print(u2)
    print(u3)
    # check_it()
    # click.echo("\n\n", " RUNNING MAIN PULL ".center(80, "*"), "\n")
    # _main_pull()
    # click.echo("ok")
