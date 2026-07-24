"""Library-first API behind the ``cellpy`` command line (CLI plan Phase 0–1).

What a command *does* and how it is *spelled* were the same code, so anything
the CLI could do was unreachable from a script: you either shelled out to
``cellpy run -j journal.json`` and parsed stdout, or you reimplemented it.

The logic lives here as ordinary typed functions, and ``cellpy.cli`` becomes
argument parsing that calls them. Nothing about the command line changes — this
is a move, not a redesign (#568 for ``convert``/``run``; #651 for the rest).

**Output.** These functions are quiet by default, as a library should be. Each
public entry takes an ``echo`` callable; the CLI passes ``typer.echo``. Larger
commands bind that echo with ``_using_echo`` so private helpers can call
``_say`` without threading the callable through every signature::

    from cellpy import cli_api
    cli_api.run_journal("my_experiment.json")            # quiet
    cli_api.run_journal("my_experiment.json", echo=print)  # chatty
    cli_api.setup_config(silent=True, echo=print)
"""

from __future__ import annotations

import getpass
import logging
import os
import pathlib
import platform
import subprocess
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Optional, Union

import cellpy
import cellpy._version
import cellpy.config as config
from cellpy.exceptions import ConfigFileNotWritten
from cellpy.internals.otherpath import OtherPath
from cellpy.parameters import prmreader
from cellpy.parameters.internal_settings import OTHERPATHS
from cellpy.utils.template_registry import REGISTERED_TEMPLATES

PathLike = Union[str, pathlib.Path]
Echo = Callable[[str], None]

VERSION = cellpy._version.__version__
REPO = "jepegit/cellpy"
USER = "jepegit"
GITHUB_PWD_VAR_NAME = "GD_PWD"
DEFAULT_EDITOR = "vim"
EDITORS = {"Windows": "notepad"}


def _silent(_message: str) -> None:
    """Default ``echo``: a library does not print unless asked to."""


def _resolve_echo(echo: Optional[Echo]) -> Echo:
    return echo if echo is not None else _silent


# -- convert --------------------------------------------------------------------


#: What ``convert`` can write. v9 is the zip-of-parquet ``.cellpy`` format that
#: ``CellpyCell.save`` writes by default; v8 is the legacy HDF5 layout.
CONVERT_TARGETS = ("v9", "v8")

_TARGET_SUFFIX = {"v9": ".cellpy", "v8": ".h5"}


#: Destination suffixes that mean "legacy HDF5", matching the rule
#: ``CellpyCell.save`` already uses to pick a writer.
_HDF5_SUFFIXES = {".h5", ".hdf5"}


def convert(
    source: PathLike,
    destination: Optional[PathLike] = None,
    *,
    to: Optional[str] = None,
    echo: Optional[Echo] = None,
) -> pathlib.Path:
    """Upgrade a legacy cellpy-file to a current on-disk format.

    Args:
        source: the old cellpy file.
        destination: where to write. Defaults to ``<name>_<target>`` beside the
            source, with the suffix the target format uses (``.cellpy`` for v9,
            ``.h5`` for v8).
        to: ``"v9"`` (zip-of-parquet — what ``CellpyCell.save`` writes) or
            ``"v8"`` (legacy HDF5). When omitted the target is inferred from
            *destination*'s suffix — ``.h5``/``.hdf5`` means v8, anything else
            means v9 — which is the same rule ``CellpyCell.save`` applies. With
            no destination either, the target is v9.
        echo: progress reporter; quiet by default.

    Returns:
        The path written.

    Raises:
        ValueError: if *to* is not a known target.

    !!! note "Changed in 2.0"
        This used to write v8 unconditionally, naming the output ``<name>_v8``.
        It now produces v9 by default. Pass ``to="v8"`` (or a ``.h5``
        destination) for the old format.
    """
    say = _resolve_echo(echo)

    from cellpy.readers.cellpy_file import load as cellpy_file_load
    from cellpy.readers.cellpy_file import save as cellpy_file_save
    from cellpy.readers.cellpy_file import v9 as cellpy_file_v9

    old_path = pathlib.Path(source)

    if to is None:
        # Infer from the destination the caller chose, so that
        # `convert old.h5 new.h5` does not put a zip inside a .h5 file.
        if destination is not None:
            suffix = pathlib.Path(destination).suffix.lower()
            target = "v8" if suffix in _HDF5_SUFFIXES else "v9"
        else:
            target = "v9"
    else:
        target = to.lower().strip()

    if target not in CONVERT_TARGETS:
        raise ValueError(
            f"unknown conversion target {to!r}; expected one of "
            f"{', '.join(CONVERT_TARGETS)}"
        )

    if destination is None:
        new_path = old_path.with_name(
            f"{old_path.stem}_{target}{_TARGET_SUFFIX[target]}"
        )
    else:
        new_path = pathlib.Path(destination)

    say(f"[cellpy] (convert) loading {old_path}")
    result = cellpy_file_load(old_path, accept_old=True)
    say(
        f"[cellpy] (convert) saving v{result.file_version} -> {target} "
        f"as {new_path}"
    )
    if target == "v9":
        cellpy_file_v9.save(result.data, new_path)
    else:
        cellpy_file_save(result.data, new_path)
    say(f"[cellpy] (convert) done: {new_path}")
    return new_path


# -- run ------------------------------------------------------------------------


def _batch_kwargs(debug: bool, minimal: bool) -> dict[str, Any]:
    """The export/log-level knobs the run commands share."""
    kwargs: dict[str, Any] = {}
    if debug:
        kwargs["default_log_level"] = "DEBUG"
    if not minimal:
        kwargs["export_raw"] = False
        kwargs["export_cycles"] = False
        kwargs["export_ica"] = False
    return kwargs


def run_journal(
    journal: PathLike,
    *,
    debug: bool = False,
    silent: bool = False,
    raw: bool = False,
    cellpyfile: bool = False,
    minimal: bool = False,
    nom_cap: Optional[float] = None,
    echo: Optional[Echo] = None,
) -> Any:
    """Process one batch journal.

    Args:
        journal: journal file. A bare name is looked up in the configured
            ``batchfiledir``, as the CLI has always done.
        debug: raise the log level to DEBUG.
        silent: do not print the resulting batch object.
        raw: force re-reading the raw files.
        cellpyfile: force using the cellpy files.
        minimal: skip the raw/cycles/ica exports.
        nom_cap: nominal capacity override.
        echo: progress reporter; quiet by default.

    Returns:
        The batch object, or None if the journal could not be found.
    """
    say = _resolve_echo(echo)
    say(f"running journal {journal}")

    from cellpy.utils import batch

    kwargs = _batch_kwargs(debug, minimal)

    batchfiledir = pathlib.Path(config.paths.batchfiledir)
    file = pathlib.Path(journal)
    if not file.is_file():
        say(f"file_name={journal} not found - looking into batchfiledir")
        if not batchfiledir.is_dir():
            say("batchfiledir not found - aborting")
            return None
        file = batchfiledir / file.name

    if not file.is_file():
        say(f"{file} not found - aborting")
        return None

    result = batch.process_batch(
        file,
        force_raw_file=raw,
        force_cellpy=cellpyfile,
        nom_cap=nom_cap,
        backend="matplotlib",
        **kwargs,
    )
    if result is not None and not silent:
        print(result)
    say("---")
    return result


def run_journals(
    folder: PathLike,
    *,
    debug: bool = False,
    silent: bool = False,
    raw: bool = False,
    cellpyfile: bool = False,
    minimal: bool = False,
    echo: Optional[Echo] = None,
) -> None:
    """Process every journal in a folder."""
    say = _resolve_echo(echo)
    say(f"running journals in {folder}")

    from cellpy.utils import batch

    kwargs = _batch_kwargs(debug, minimal)
    folder_path = pathlib.Path(folder).resolve()

    if not folder_path.is_dir():
        say(f"{folder_path} not found - aborting")
        return

    batch.iterate_batches(
        folder_path,
        force_raw_file=raw,
        force_cellpy=cellpyfile,
        silent=True,
        **kwargs,
    )
    say("---")


def run_from_db(
    name: str,
    *,
    debug: bool = False,
    silent: bool = False,
    raw: bool = False,
    cellpyfile: bool = False,
    minimal: bool = False,
    nom_cap: Optional[float] = None,
    batch_col: Optional[str] = None,
    project: Optional[str] = None,
    echo: Optional[Echo] = None,
) -> Any:
    """Process a batch selected from the database."""
    say = _resolve_echo(echo)
    say(f"running from db \nkey={name}, batch_col={batch_col}, project={project}")

    from cellpy.utils import batch

    kwargs = _batch_kwargs(debug, minimal)
    kwargs["name"] = name
    if batch_col is not None:
        kwargs["batch_col"] = batch_col
    kwargs["project"] = "various" if project is None else project

    say("Warming up ...")
    say("  - starting batch processing")
    result = batch.process_batch(
        force_raw_file=raw,
        force_cellpy=cellpyfile,
        nom_cap=nom_cap,
        backend="matplotlib",
        **kwargs,
    )
    if result is not None and not silent:
        print(result)
    say("---")
    return result


def run_project(project: PathLike, *, echo: Optional[Echo] = None, **kwargs: Any) -> None:
    """Execute every notebook in a project folder with papermill."""
    say = _resolve_echo(echo)
    try:
        import papermill as pm  # type: ignore
    except ImportError:
        say(
            "[cellpy]: You need to install papermill for automatically execute the notebooks."
        )
        say("[cellpy]: You can install it using pip like this:")
        say(" >> pip install papermill")
        return

    project_path = pathlib.Path(project)
    say(f"[cellpy]: trying to run notebooks in {project_path}")
    for notebook in sorted(project_path.glob("*.ipynb")):
        say(f"[cellpy - papermill] running {notebook.name}")
        pm.execute_notebook(notebook, notebook, parameters=kwargs)


def list_journals(
    batchfiledir: Optional[PathLike] = None,
    *,
    echo: Optional[Echo] = None,
) -> list[pathlib.Path]:
    """List the batch journals in ``batchfiledir``.

    Returns the paths as well as echoing them, so a script can use the result
    instead of scraping the output.
    """
    say = _resolve_echo(echo)

    if batchfiledir in (None, "NONE"):
        folder = pathlib.Path(config.paths.batchfiledir)
    else:
        folder = pathlib.Path(batchfiledir).resolve()

    if not folder.is_dir():
        say(f"{folder} not found.")
        return []

    say(f"Content of '{folder}':\n")
    found = sorted(folder.glob("cellpy*.json"))
    for journal in found:
        say(f"{journal.name}")

    # Deliberate fix, the one behaviour change in this extraction. The original
    # counted with a loop variable left over from `enumerate`, so it reported
    # one fewer file than it had just listed — and for exactly one file the
    # leftover index was 0, which is falsy, so it printed "No batch-files
    # found" directly beneath the file it had listed.
    if found:
        print(f"\nnumber of batch-files located: {len(found)}")
    else:
        print("No batch-files found in this directory.")
    return found


def open_db_editor(
    *, debug: bool = False, silent: bool = False, echo: Optional[Echo] = None
) -> None:
    """Open the cellpy database in the platform's spreadsheet application."""
    say = _resolve_echo(echo)

    if not silent:
        say("running database editor")
    if debug:
        say("running in debug-mode, but nothing to tell")

    db_path = pathlib.Path(config.paths.db_path) / config.paths.db_filename
    system = platform.system()

    if system == "Windows":
        import os

        try:
            os.system(f'start excel "{str(db_path)}"')
        except Exception as exc:
            say("Something went wrong trying to open")
            say(str(db_path))
            print()
            print(exc)
        return

    if system == "Linux":
        say("RUNNING LINUX")
    elif system == "Darwin":
        say(" - running on a mac")
    else:
        print("RUNNING SOMETHING ELSE")
        print(system)

    # not tested on any of these
    subprocess.check_call(["open", "-a", "Microsoft Excel", db_path])

# -- echo binder for moved CLI helpers (#651) -----------------------------------
# Public APIs take ``echo=`` and wrap work in ``_using_echo`` so private helpers
# can call ``_say`` without threading the callable through every signature.
# Quiet by default (same contract as ``convert`` / ``run_journal``).

_echo_var: ContextVar[Echo] = ContextVar("cellpy_cli_api_echo", default=_silent)


def _say(message: str, **_kwargs) -> None:
    """Report via the bound echo; colour kwargs from old typer.echo are ignored."""
    _echo_var.get()(message)


@contextmanager
def _using_echo(echo: Optional[Echo] = None):
    token = _echo_var.set(_resolve_echo(echo))
    try:
        yield
    finally:
        _echo_var.reset(token)


DIFFICULT_MISSING_MODULES: dict[str, str] = {}

try:
    import cookiecutter.exceptions
    import cookiecutter.main
    import cookiecutter.prompt
except ModuleNotFoundError:
    cookiecutter = None  # type: ignore
    DIFFICULT_MISSING_MODULES["cookiecutter"] = (
        "Could not import cookiecutter (used by cellpy new). Try installing it, "
        "for example by writing:\n\n         python -m pip install cookiecutter\n"
    )

try:
    import github
    from github import Github
except ModuleNotFoundError:
    github = None  # type: ignore
    Github = None  # type: ignore
    DIFFICULT_MISSING_MODULES["github"] = (
        "Could not import the github library (used by cellpy pull). Try installing "
        "it, for example by writing:\n\n         python -m pip install github\n"
    )

try:
    import sqlalchemy_access  # noqa: F401
except ModuleNotFoundError:
    DIFFICULT_MISSING_MODULES["sqlalchemy-access"] = (
        "Could not import the sqlalchemy_access library (usually used when reading "
        "arbin .res files on windows). If you need it, try installing it by writing:"
        "\n\n         python -m pip install sqlalchemy-access\n"
    )

try:
    import lmfit  # noqa: F401
except ModuleNotFoundError:
    DIFFICULT_MISSING_MODULES["lmfit"] = (
        "Could not import the lmfit library (used when fitting ocv rlx data)."
        " If you think you will need it, try installing it for example by writing:"
        "\n\n         python -m pip install lmfit\n"
    )

try:
    import jinja2_time  # noqa: F401
except ModuleNotFoundError:
    DIFFICULT_MISSING_MODULES["jinja2_time"] = (
        "Could not import the jinja2_time library (used by cellpy new)."
        " Try installing it, for example by writing:"
        "\n\n         python -m pip install jinja2_time\n"
    )


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
                _say(f"[cellpy] (setup) Created {o}")
            except FileExistsError:
                _say(f"[cellpy] (setup) {o} already exists.")
            except FileNotFoundError:
                _say(f"[cellpy] (setup) {o} not available.")
            except Exception as e:
                _say(f"[cellpy] (setup) WARNING! Could not create {o}.")
                logging.debug(e)
                _say("[cellpy] (setup) ...continuing anyway.")
        else:
            _say(f"[cellpy] (setup) Could not create {o}")
    return o

# -- setup file helpers --
def save_prm_file(prm_filename):
    """saves (writes) the prms to file"""
    prmreader._write_prm_file(prm_filename)


def dump_env_file(env_filename):
    """saves (writes) the env to file"""
    _say(f" dumping env file to {env_filename}")
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


# -- write toml --
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
        _say(f"[cellpy] (setup) dry-run: would write {toml_path}")
        return

    data = cellpy_config.get_config().model_dump_for_file()
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    config_loader.write_toml(toml_path, data)
    _say(f"[cellpy] (setup) wrote {toml_path}")

# -- migrate --
def migrate_config(
    src=None,
    dst=None,
    dry_run=False,
    force=False,
    *,
    echo=None,
):
    """One-time conversion of the legacy YAML .conf file to cellpy.toml.

    The old file is left untouched (it keeps working through the v2.0
    deprecation window); the generated TOML takes precedence once present.
    """
    with _using_echo(echo):
        _migrate_config_body(src, dst, dry_run, force)


def _migrate_config_body(src, dst, dry_run, force):
    from cellpy.config import loader as config_loader
    from cellpy.config import migrate as config_migrate

    if src is None:
        try:
            src = prmreader._get_prm_file()
        except Exception:
            src = None
        if src is None or not pathlib.Path(src).is_file():
            _say(
                "[cellpy] (setup migrate) no legacy config file found - "
                "nothing to migrate (run `cellpy setup` to create a fresh one)."
            )
            return
    src = pathlib.Path(src)

    toml_path = pathlib.Path(dst) if dst else config_loader.user_config_path()
    if toml_path.is_file() and not force:
        _say(
            f"[cellpy] (setup migrate) {toml_path} already exists "
            "- use --force to overwrite."
        )
        return

    _say(f"[cellpy] (setup migrate) source: {src}")
    _say(f"[cellpy] (setup migrate) target: {toml_path}")
    if dry_run:
        _say("[cellpy] (setup migrate) dry-run: not writing anything.")
        return

    toml_path.parent.mkdir(parents=True, exist_ok=True)
    config_migrate.convert_yaml_file_to_toml(src, toml_path)
    _say("[cellpy] (setup migrate) done - the old file is kept untouched.")

# -- update_paths through get_default_editor --
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
        _say(f" - default_dir: {default_dir}")
        _say(f" - custom_dir: {custom_dir}")
        _say(f" - relative_home: {relative_home}")

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
        _say(f" - base (h): {h}")

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
            _say(f"dry run (so I did not create {d})")

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
    _say(f"\n[cellpy] (setup) input {q}")
    _say(f"[cellpy] (setup) current: {p}")
    new_path = input("[cellpy] (setup) new value (press enter to keep) >>> ").strip()
    if not new_path:
        new_path = p
    return pathlib.Path(new_path)


def _ask_about_otherpath(q, p):
    _say(f"\n[cellpy] (setup) input {q}")
    _say(f"[cellpy] (setup) current: {p}")
    new_path = input("[cellpy] (setup) new value (press enter to keep) >>> ").strip()
    if not new_path:
        new_path = p
    return OtherPath(new_path)


def _ask_about_name(q, n):
    _say(f"\n[cellpy] (setup) input {q}")
    _say(f"[cellpy] (setup) current: {n}")
    new_name = input("[cellpy] (setup) new value (press enter to keep) >>> ").strip()
    if not new_name:
        new_name = n
    return new_name


def _check_import_cellpy():
    try:
        import cellpy  # noqa: F401
        from cellpy import log  # noqa: F401
        from cellpy.readers import cellreader  # noqa: F401

        return True
    except Exception:
        _say(" Failed to import cellpy")
        _say(" Severity: critical")
        return False


def _check_import_pyodbc():
    import platform

    from cellpy.parameters import prms

    ODBC = prms._odbc
    SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver

    use_subprocess = config.instruments.Arbin.use_subprocess
    detect_subprocess_need = config.instruments.Arbin.detect_subprocess_need
    _say(" This is needed for loading Arbin .res files")
    _say(" parsing prms")
    _say(
        " (from your configuration file if it exists, otherwise using defaults)"
    )
    _say(f" - ODBC: {ODBC}")
    _say(f" - SEARCH_FOR_ODBC_DRIVERS: {SEARCH_FOR_ODBC_DRIVERS}")
    _say(f" - use_subprocess: {use_subprocess}")
    _say(f" - detect_subprocess_need: {detect_subprocess_need}")
    _say(f" - stated office version: {config.instruments.Arbin.office_version}")

    _say(" checking system")
    is_posix = False
    is_macos = False
    if os.name == "posix":
        is_posix = True
        _say(" - running on posix")
    current_platform = platform.system()
    if current_platform == "Darwin":
        is_macos = True
        _say(" - running on a mac")

    python_version, os_version = platform.architecture()
    _say(f" - python version: {python_version}")
    _say(f" - os version: {os_version}")

    if not is_posix:
        if not config.instruments.Arbin.sub_process_path:
            sub_process_path = str(prms._sub_process_path)
        else:
            sub_process_path = str(config.instruments.Arbin.sub_process_path)
        _say(f" stated path to sub-process: {sub_process_path}")
        if not os.path.isfile(sub_process_path):
            _say(" - OBS! missing")

    if is_posix:
        _say(" checking existence of mdb-export")
        sub_process_path = "mdb-export"
        from subprocess import PIPE, run

        command = ["command", "-v", sub_process_path]

        try:
            _say(f" - trying to run {command}")
            result = run(
                command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True
            )
            if result.returncode == 0:
                _say(" - found it!")
                return True

            _say(f" - could not find {sub_process_path}")

            if is_macos:
                driver = "/usr/local/lib/libmdbodbc.dylib"
                _say(
                    f" looks like you are on a mac. Searching for suitable driver: {driver})"
                )
                if not os.path.isfile(driver):
                    _say(f" - could not find {driver}")
                    _say(
                        " ! If you want to load Arbin .res files you will have to install it manually."
                    )
                    _say(" - Try installing it with brew:\n")
                    _say("   brew install mdbtools")
                    return False
                _say(f" - found it: {driver}")
                return True
            else:
                _say(
                    " ! If you want to load Arbin .res files you will have to install it manually."
                )
                _say("   For example (for ubuntu):\n")
                _say("   sudp apt-get update")
                _say("   sudp apt-get install -y mdbtools")
            return False

        except AssertionError:
            _say(" - could not find any suitable driver")
            return False

    # not posix - checking for odbc drivers
    # 1) checking if you have defined one
    try:
        driver = config.instruments.Arbin.odbc_driver
        if not driver:
            raise AttributeError
        _say(" You have defined an odbc driver in your config file")
        _say(f" - driver: {driver}")
    except AttributeError:
        _say(" FYI: you have not defined any odbc_driver(s)")
        _say(
            " (The name of the driver from the configuration file is "
            "used as a backup when cellpy cannot locate a driver by itself)"
        )

    use_ado = False

    if ODBC == "ado":
        use_ado = True
        _say(" you stated that you prefer the ado loader")
        _say(" checking if adodbapi is installed")
        try:
            import adodbapi as dbloader
        except ImportError:
            use_ado = False
            _say(" Failed! Try setting pyodbc as your loader or install")
            _say(" adodbapi (http://adodbapi.sourceforge.net/)")

    if not use_ado:
        if ODBC == "pyodbc":
            _say(" you stated that you prefer the pyodbc loader")
            try:
                import pyodbc as dbloader
            except ImportError:
                _say(" Failed! Could not import it.")
                _say(" Try 'pip install pyodbc'")
                dbloader = None

        elif ODBC == "pypyodbc":
            _say(" you stated that you prefer the pypyodbc loader")
            try:
                import pypyodbc as dbloader  # type: ignore
            except ImportError:
                _say(" Failed! Could not import it.")
                _say(" try 'pip install pypyodbc'")
                _say(" or set pyodbc as your loader in your prm file")
                _say(" (and install it)")
                dbloader = None

    _say(" searching for odbc drivers")
    try:
        drivers = [
            driver
            for driver in dbloader.drivers()
            if "Microsoft Access Driver" in driver
        ]
        _say(f" Found these: {drivers}")
        driver = drivers[0]
        _say(f" - odbc driver: {driver}")
        return True

    except IndexError:
        logging.debug(" Unfortunately, it seems the list of drivers is emtpy.")
        _say(
            "\n Could not find any odbc-drivers suitable for .res-type files. "
            "Check out the homepage of pydobc for info on installing drivers"
        )
        _say(
            " One solution that might work is downloading "
            "the Microsoft Access database engine "
            "(in correct bytes (32 or 64)) "
            "from:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=13255"
        )
        _say(
            " Or install mdbtools and set it up (check the cellpy docs for help)"
        )
        _say("\n")
        return False


def _check_config_file():
    prm_file_name = _configloc()
    env_file_name = _envloc()

    if env_file_name is None:
        _say(" FYI! Could not locate the environment file")

    if prm_file_name is None:
        _say(" Could not find the config file")
        _say(" You can create one by running 'cellpy setup'")
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
            _say(f" - {k}: {value}")
            # splitting this into two if-statements to make it easier to debug if OtherPath changes
            if k in OTHERPATHS:
                print(f" skipping check for external {k} (for now)")
                # if not OtherPath(
                #     value
                # ).is_dir():  # Assuming OtherPath returns True if it is external.
                #     missing += 1
                #     _say("COULD NOT CONNECT!")
                #     _say(f"({value} is not a directory)")
            elif value and not pathlib.Path(value).is_dir():
                missing += 1
                _say(" COULD NOT CONNECT!")
                _say(f" ({value} is not a directory)")
            if not value:
                missing += 1
                _say(" MISSING")

        value = prm_paths.get("db_filename", None)
        _say(f" - db_filename: {value}")
        if not value:
            missing += 1
            _say(" MISSING")

        if missing:
            return False
        else:
            return True

    except Exception as e:
        _say(" Following error occurred:")
        _say(e)
        return False


def _check(dry_run=False, full_check=True):
    _say(" checking ".center(80, "="))
    if dry_run:
        _say("*** dry-run: skipping the test")
        return
    failed_checks = 0
    number_of_checks = 0

    def sub_check(check_type, check_func):
        failed = 0
        _say(f"[cellpy] * - Checking {check_type}")
        if check_func():
            _say("[cellpy] -> succeeded!")
        else:
            _say("f[cellpy] -> failed!!!!")
            failed = 1
        _say(80 * "-")
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
            _say(f"[cellpy] check raised an exception ({e})")
        number_of_checks += 1
    _say(" results ".center(80, "="))
    succeeded_checks = number_of_checks - failed_checks

    if failed_checks > 0:
        _say(
            "[cellpy] Some of the checks failed! This could potentially be a problem."
        )
        _say(f"[cellpy] Failed {failed_checks} out of {number_of_checks} checks.")
    else:
        _say(
            f"[cellpy] Succeeded {succeeded_checks} out of {number_of_checks} checks."
        )
    _say(80 * "=")


def _write_config_file(user_dir, dst_file, init_filename, dry_run):
    _say(" update configuration ".center(80, "-"))
    _say("[cellpy] (setup) Writing configurations to user directory:")
    _say(f"\n         {user_dir}\n")

    if os.path.isfile(dst_file):
        _say("[cellpy] (setup) File already exists!")
        _say("[cellpy] (setup) Keeping most of the old configuration parameters")
    try:
        if dry_run:
            _say(
                f"*** dry-run: skipping actual saving of {dst_file} ***")
        else:
            _say(f"[cellpy] (setup) Saving file ({dst_file})")
            save_prm_file(dst_file)

    except ConfigFileNotWritten:
        _say("[cellpy] (setup) Something went wrong! Could not write the file")
        _say(
            "[cellpy] (setup) Trying to write a file"
            + f"called {prmreader.DEFAULT_FILENAME} instead"
        )

        try:
            user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
            if dry_run:
                _say(
                    f"*** dry-run: skipping actual saving of {dst_file} ***",
                    color="red",
                )
            else:
                save_prm_file(dst_file)

        except ConfigFileNotWritten:
            _txt = "[cellpy] (setup) No, that did not work either.\n"
            _txt += "[cellpy] (setup) Well, guess you have to talk to the developers."
            _say(_txt)
    else:
        _say("[cellpy] (setup) Configuration file written!")
        _say(
            "[cellpy] (setup) OK! Now you can edit it. For example by "
            f"issuing \n\n         [your-favourite-editor] {init_filename}\n"
        )


def _write_env_file(user_dir, dst_file, dry_run):
    _say(" update configuration ".center(80, "-"))
    _say("[cellpy] (setup) Writing environment file:")
    _say(f"\n         {dst_file}\n")

    if os.path.isfile(dst_file):
        _say(f"[cellpy] (setup) Environment file {dst_file} already exists!")
        if not dry_run:
            return
    try:
        if dry_run:
            _say(
                f"*** dry-run: skipping actual saving of {dst_file} ***")
        else:
            _say(f"[cellpy] (setup) Saving file ({dst_file})")
            dump_env_file(dst_file)

    except ConfigFileNotWritten:
        _txt = "[cellpy] (setup) No, that did not work either.\n"
        _txt += "[cellpy] (setup) Well, guess you have to talk to the developers."
        _say(_txt)
    else:
        _say("[cellpy] (setup) Environment file written!")
        _say(
            "[cellpy] (setup) OK! Now you can edit it. For example by "
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

# -- dump_config_resolved --
def _dump_config_resolved():
    """Print resolved config values with per-field provenance (#454)."""
    from cellpy import config as cellpy_config

    data = cellpy_config.get_config().model_dump_for_file()
    provenance = cellpy_config.sources()
    _say("[cellpy] resolved configuration (value  # source-layer):")
    for section, fields in data.items():
        _say(f"\n[{section}]")
        if not isinstance(fields, dict):
            _say(f"  {fields!r}")
            continue
        for key, value in fields.items():
            layer = provenance.get(f"{section}.{key}", "default")
            _say(f"  {key} = {value!r}  # {layer}")

# -- pull clone/tests/examples --
def _clone_repo(directory, password):
    directory = pathlib.Path(directory)
    txt = "[cellpy] The plan is that this "
    txt += "[cellpy] cmd will pull (clone) the cellpy repo.\n"
    txt += "[cellpy] For now it only prints the link to the git-hub\n"
    txt += "[cellpy] repository:\n"
    txt += "[cellpy]\n"
    txt += "[cellpy] https://github.com/jepegit/cellpy.git\n"
    txt += "[cellpy]\n"
    _say(txt)


def _pull_tests(directory, pw=None):
    txt = (
        "[cellpy] (pull) Pulling tests from",
        " https://github.com/jepegit/cellpy.git",
    )
    _say(txt)
    _pull(gdirpath="tests", rootpath=directory, pw=pw)
    _pull(gdirpath="testdata", rootpath=directory, pw=pw)


def _pull_examples(directory, pw):
    txt = (
        "[cellpy] (pull) Pulling examples from",
        " https://github.com/jepegit/cellpy.git",
    )
    _say(txt)
    _pull(gdirpath="examples", rootpath=directory, pw=pw)

# -- version/configloc/envloc/dump_params --
def _version():
    version_text = "[cellpy] version: " + str(VERSION)
    _say(version_text)


def _configloc():
    _, config_file_name = prmreader.get_user_dir_and_dst()
    _say(f"[cellpy] -> {config_file_name}")
    if not os.path.isfile(config_file_name):
        _say("[cellpy] File does not exist!")
    else:
        return config_file_name


def _envloc():
    env_file_name = prmreader.get_env_file_name()
    _say(f"[cellpy] (from config) -> {env_file_name}")
    if not os.path.isfile(env_file_name):
        return
    return env_file_name


def _dump_params():
    _say("[cellpy] Running prmreader.info:\n")
    prmreader.info()


# -- github download helpers --
def _download_g_blob(name, local_path):
    import urllib.request

    dirs = local_path.parent
    if not dirs.is_dir():
        _say(f"[cellpy] (pull) creating dir: {dirs}")
        dirs.mkdir(parents=True)
    print(f"[cellpy] (pull) downloading blob: {name.download_url}")
    filename, headers = urllib.request.urlretrieve(
        name.download_url, filename=local_path
    )
    _say(f"[cellpy] (pull) downloaded blob: {filename}")


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
        _say(" DEV MODE ".center(80, "-"))
        u = _get_user_name()
        if pw == "ask":
            _say("   - ask for password")
            pw = _get_pw(pw)
        elif pw == "env":
            _say("   - check environ for password ")
            pw = _get_pw(pw)
            _say("   - got something")
            if pw is None:
                _say("   - only None")
                u = None

    g = Github(u, pw)
    try:
        repo = g.get_repo(REPO)
    except github.RateLimitExceededException:
        _say("   - rate limit exceeded")
        _say("   - waiting 60 seconds, and trying only once more")
        _say(
            "   - hint! you can check status directly using the github api, e.g. "
        )
        _say("     $ curl -i https://api.github.com/users/USERNAME")
        _say("   - press ctrl-c to abort")
        time.sleep(60)
        repo = g.get_repo(REPO)

    _say(f"[cellpy] (pull) pulling {gdirpath}")
    _say(f"[cellpy] (pull) -> {ndirpath}")

    if not ndirpath.is_dir():
        _say(f"[cellpy] (pull) creating dir: {ndirpath}")
        ndirpath.mkdir(parents=True)

    for gfile in _parse_g_dir(repo, gdirpath):
        gfilename = pathlib.Path(gfile.path)
        nfilename = rootpath / gfilename
        try:
            _download_g_blob(gfile, nfilename)
        except github.RateLimitExceededException:
            _say("   - rate limit exceeded")
            _say("   - waiting 60 seconds, and trying only once more")
            _say("   - press ctrl-c to abort")
            time.sleep(60)
            _download_g_blob(gfile, nfilename)

# -- templates --
def _get_default_template():
    template = "standard"
    try:
        template = config.batch.template
    except Exception:
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

# -- _new through _serve --
def _new(
    template: str,
    directory: PathLike | None = None,
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

    try:
        import cookiecutter.exceptions
        import cookiecutter.main
        import cookiecutter.prompt

    except ModuleNotFoundError:
        _say("Could not import cookiecutter.")
        _say("Try installing it, for example by writing:")
        _say("\npython -m pip install cookiecutter\n")
        return

    if list_:
        _say("\n[cellpy] batch templates")

        default_template = _get_default_template()
        local_templates = _read_local_templates()
        local_templates_path = config.paths.templatedir
        registered_templates = REGISTERED_TEMPLATES
        _say(f"[cellpy] - default: {default_template}")
        _say("[cellpy] - registered templates (on github):")
        for label, link in registered_templates.items():
            _say(f"\t\t{label:18s} {link}")

        if local_templates:
            _say(f"[cellpy] - local templates ({local_templates_path}):")
            for label, link in local_templates.items():
                _say(f"\t\t{label:18s} {link}")
        else:
            _say(f"[cellpy] - local templates ({local_templates_path}): none")

        return

    if project_dir is None or session_id is None:
        no_input = False

    if not template:
        template = _get_default_template()

    if lab:
        server = "lab"
    else:
        server = "notebook"

    _say(f"Template: {template}")
    if local_user_template:
        # forcing using local template
        templates = _read_local_templates()

        if not templates:
            _say(
                "You asked me to use a local template, but you have none. Aborting."
            )
            return
    else:
        templates = REGISTERED_TEMPLATES
        if local_templates := _read_local_templates():
            templates.update(local_templates)

    if template.lower() not in templates:
        _say("This template does not exist. Aborting.")
        return

    if directory is None:
        logging.debug("no dir given")
        directory = config.paths.notebookdir

    if not os.path.isdir(directory):
        _say("Sorry. This did not work as expected!")
        _say(f" - {directory} does not exist")
        return

    directory = pathlib.Path(directory)
    selected_project_dir = None

    if project_dir:
        selected_project_dir = directory / project_dir
        if not selected_project_dir.is_dir():
            if cookiecutter.prompt.read_user_yes_no(
                f"{project_dir} does not exist. Create?", "yes"
            ):
                os.mkdir(selected_project_dir)
                _say(f"Created {selected_project_dir}")

            else:
                selected_project_dir = None
                _say("Select another directory instead")
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
                _say(f"created {project_dir}")
            except FileExistsError:
                _say("OK - but this directory already exists!")
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
        _say("Sorry. This did not work as expected!")
        _say(" - cookiecutter refused to create the project")
        _say(e)

    if serve_:
        os.chdir(directory)
        _serve(server, executable)

    elif run_:
        _say("WARNING - experimental feature - use at your own risk")
        input("Press Enter to continue...")
        import importlib.util

        if importlib.util.find_spec("papermill") is None:
            _say(
                "[cellpy]: You need to install papermill for automatically execute the notebooks."
            )
            _say("[cellpy]: You can install it using pip like this:")
            _say(" >> pip install papermill")
            return
        new_existing_projects = os.listdir(selected_project_dir)
        our_new_projects = list(set(new_existing_projects) - set(existing_projects))

        if not len(our_new_projects):
            _say(
                "[cellpy]: Sorry, could not deiced what is the new project "
                "- so I don't dare to try to execute automatically."
            )
            return
        our_new_project = selected_project_dir / our_new_projects[0]

        run_project(our_new_project, echo=_echo_var.get())


def _get_author_name():
    """Get the name of the author."""
    try:
        import getpass

        author_name = getpass.getuser()
    except Exception as e:
        _say("Could not get the author name")
        _say(e)
        author_name = "unknown"
    return author_name


def _serve(server, executable=None):
    _say(f"serving with jupyter {server}")
    # TODO: search for jupyter and find the right one
    if executable is None:
        executable = "jupyter"
    subprocess.run([executable, server], check=True)
    _say("Finished serving.")



def setup_config(
    *,
    interactive: bool = False,
    not_relative: bool = False,
    dry_run: bool = False,
    reset: bool = False,
    root_dir=None,
    folder_name=None,
    test_user=None,
    silent: bool = False,
    no_deps: bool = False,
    echo: Optional[Echo] = None,
):
    """Write / refresh the user cellpy configuration (library form of ``cellpy setup``)."""
    with _using_echo(echo):
        _say("[cellpy] (setup)")
        _say(f"[cellpy] root-dir: {root_dir}")

        # notify of missing 'difficult' or optional modules
        if not no_deps:
            _say("[cellpy] checking dependencies")
            for m in DIFFICULT_MISSING_MODULES:
                _say(" [cellpy] WARNING! ".center(80, "-"))
                _say("[cellpy] missing dependencies:")
                _say(f"[cellpy] - {m}")
                _say(f"[cellpy] {DIFFICULT_MISSING_MODULES[m]}")
                _say(
                    "[cellpy] (you can skip this check by using the --no-deps option)"
                )
                _say(80 * "-")

        # generate variables
        init_filename = prmreader.create_custom_init_filename()
        user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
        env_file = prmreader.get_env_file_name()

        if dry_run:
            _say("Create custom init filename and get user_dir and destination")
            _say("Got the following parameters:")
            _say(f" - init_filename: {init_filename}")
            _say(f" - user_dir: {user_dir}")
            _say(f" - dst_file: {dst_file}")
            _say(f" - not_relative: {not_relative}")

        if root_dir and not interactive:
            _say("[cellpy] custom root-dir can only be used in interactive mode")
            _say("[cellpy] -> setting interactive mode")
            interactive = True

        if not root_dir:
            root_dir = user_dir
            # root_dir = pathlib.Path(os.getcwd())
        root_dir = pathlib.Path(root_dir)

        if dry_run:
            _say(f" - root_dir: {root_dir}")

        if test_user:
            _say(f"[cellpy] (setup) DEV-MODE test_user: {test_user}")
            init_filename = prmreader.create_custom_init_filename(test_user)
            user_dir = root_dir
            dst_file = get_dst_file(user_dir, init_filename)
            _say(f"[cellpy] (setup) DEV-MODE user_dir: {user_dir}")
            _say(f"[cellpy] (setup) DEV-MODE dst_file: {dst_file}")

        if not pathlib.Path(dst_file).is_file():
            _say(f"[cellpy] {dst_file} not found -> I will make one for you")
            reset = True

        if not pathlib.Path(env_file).is_file():
            _say(
                f"[cellpy] {env_file} not found -> I will make one (but you must edit it yourself)"
            )

        if interactive:
            _say(" interactive mode ".center(80, "-"))
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


# -- public facades (#651) ------------------------------------------------------


def show_info(
    *,
    version: bool = False,
    configloc: bool = False,
    params: bool = False,
    show_config: bool = False,
    check: bool = False,
    echo: Optional[Echo] = None,
) -> None:
    """Library form of ``cellpy info``."""
    with _using_echo(echo):
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


def config_path(*, echo: Optional[Echo] = None):
    """Return the user config file path (also echoes it)."""
    with _using_echo(echo):
        return _configloc()


def start_jupyter(
    *,
    lab: bool = False,
    directory=None,
    executable=None,
    echo: Optional[Echo] = None,
) -> None:
    """Library form of ``cellpy serve``."""
    with _using_echo(echo):
        if directory is None:
            directory = config.paths.notebookdir
        elif directory == "home":
            directory = pathlib.Path().home()
        elif directory == "here":
            directory = pathlib.Path(os.getcwd())

        if not os.path.isdir(directory):
            _say("Sorry. This did not work as expected!")
            _say(f" - {directory} does not exist")
            return

        server = "lab" if lab else "notebook"
        os.chdir(directory)
        _serve(server, executable=executable)


def edit_file(
    name=None,
    *,
    default_editor=None,
    debug: bool = False,
    silent: bool = False,
    echo: Optional[Echo] = None,
) -> None:
    """Library form of ``cellpy edit``."""
    with _using_echo(echo):
        key = None if name is None else name.lower()
        if key == "db":
            open_db_editor(debug=debug, silent=silent, echo=echo)
            return

        if key is not None and key not in ("env", "config"):
            _say("unknown file")
            return

        if key is None or key == "config":
            config_file = _configloc()
            if config_file is None:
                print("could not find the config file")
                return
            filename = str(pathlib.Path(config_file).resolve())
        elif key == "env":
            filename = _envloc()
            if filename is None:
                print("could not find the env file")
                return
        else:
            filename = name

        if default_editor is None:
            default_editor = _get_default_editor()

        args = [default_editor, filename]
        _say(f"[cellpy] (edit) Calling '{default_editor}'")
        try:
            subprocess.call(args)
        except Exception:
            _say("[cellpy] (edit) Failed!")
            _say(
                "[cellpy] (edit) Try 'cellpy edit -e notepad.exe' if you are on Windows"
            )


def pull_resources(
    *,
    tests: bool = False,
    examples: bool = False,
    clone: bool = False,
    directory=None,
    password=None,
    echo: Optional[Echo] = None,
) -> None:
    """Library form of ``cellpy pull``."""
    with _using_echo(echo):
        if directory is not None:
            _say(f"[cellpy] (pull) custom directory: {directory}")
        else:
            directory = pathlib.Path(config.paths.examplesdir)

        if password is not None:
            _say("DEV MODE: password provided")
        if clone:
            _clone_repo(directory, password)
        else:
            if tests:
                _pull_tests(directory, password)
            if examples:
                _pull_examples(directory, password)
            elif not tests:
                _say(
                    "[cellpy] (pull) Nothing selected for pulling. "
                    "Please select an option (--tests,--examples, -clone, ...) "
                )


def create_project(
    template=None,
    *,
    directory=None,
    project=None,
    experiment=None,
    local_user_template: bool = False,
    serve_: bool = False,
    run_: bool = False,
    lab: bool = False,
    jupyter_executable=None,
    list_: bool = False,
    echo: Optional[Echo] = None,
    **kwargs,
):
    """Library form of ``cellpy new``."""
    with _using_echo(echo):
        return _new(
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
            **kwargs,
        )
