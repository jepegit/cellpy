"""Library-first API behind the ``cellpy`` command line (CLI plan Phase 0–1).

What a command *does* and how it is *spelled* were the same code, so anything
the CLI could do was unreachable from a script: you either shelled out to
``cellpy run -j journal.json`` and parsed stdout, or you reimplemented it.

The logic lives here as ordinary typed functions, and ``cellpy.cli`` becomes
argument parsing that calls them. Nothing about the command line changes — this
is a move, not a redesign.

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
import importlib
import logging
import os
import pathlib
import platform
import subprocess
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from cellpy._version import __version__ as VERSION
from cellpy.utils.template_registry import REGISTERED_TEMPLATES

PathLike = Union[str, pathlib.Path]
Echo = Callable[[str], None]

REPO = "jepegit/cellpy"
REPO_URL = f"https://github.com/{REPO}.git"
USER = "jepegit"
GITHUB_PWD_VAR_NAME = "GD_PWD"
DEFAULT_EDITOR = "vim"
EDITORS = {"Windows": "notepad"}


class _LazyModule:
    """Attribute proxy that imports ``qualname`` on first use (#837)."""

    def __init__(self, qualname: str):
        self._qualname = qualname
        self._mod: Any = None

    def _load(self):
        if self._mod is None:
            self._mod = importlib.import_module(self._qualname)
        return self._mod

    def __getattr__(self, name: str):
        return getattr(self._load(), name)


# Keep call sites as ``config.*`` / ``prmreader.*`` without paying import cost
# for ``cellpy info --version``.
config = _LazyModule("cellpy.config")
prmreader = _LazyModule("cellpy.parameters.prmreader")

# Optional deps — probed on demand (see ``_probe_optional_deps``), not at import.
DIFFICULT_MISSING_MODULES: dict[str, str] = {}
cookiecutter = None  # type: ignore
github = None  # type: ignore
Github = None  # type: ignore
_optional_deps_probed = False


def _probe_optional_deps() -> None:
    """Import optional CLI extras once; record missing ones for setup messaging."""
    global cookiecutter, github, Github, _optional_deps_probed
    if _optional_deps_probed:
        return
    _optional_deps_probed = True
    try:
        import cookiecutter.exceptions  # noqa: F401
        import cookiecutter.main  # noqa: F401
        import cookiecutter.prompt  # noqa: F401
        import cookiecutter as _cookiecutter

        cookiecutter = _cookiecutter
    except ModuleNotFoundError:
        cookiecutter = None
        DIFFICULT_MISSING_MODULES["cookiecutter"] = (
            "Could not import cookiecutter (used by cellpy new). Try installing it, "
            "for example by writing:\n\n         python -m pip install cookiecutter\n"
        )
    try:
        import github as _github
        from github import Github as _Github

        github = _github
        Github = _Github
    except ModuleNotFoundError:
        github = None
        Github = None
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
        # was a bare print(), so it escaped both the echo contract and --silent
        say(str(result))
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
        # was a bare print(), so it escaped both the echo contract and --silent
        say(str(result))
    return result


def run_project(project: PathLike, *, echo: Optional[Echo] = None, **kwargs: Any) -> None:
    """Execute every notebook in a project folder with papermill."""
    say = _resolve_echo(echo)
    try:
        import papermill as pm  # type: ignore
    except ImportError:
        say(
            "papermill is needed to execute the notebooks automatically "
            "- install it with:  python -m pip install papermill"
        )
        return

    project_path = pathlib.Path(project)
    say(f"running the notebooks in {project_path}")
    for notebook in sorted(project_path.glob("*.ipynb")):
        say(f"running {notebook.name}")
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
        say(f"\nnumber of batch-files located: {len(found)}")
    else:
        say("No batch-files found in this directory.")
    return found


def open_db_editor(
    *, debug: bool = False, silent: bool = False, echo: Optional[Echo] = None
) -> None:
    """Open the cellpy database in the platform's spreadsheet application."""
    say = _resolve_echo(echo)

    db_path = pathlib.Path(config.paths.db_path) / config.paths.db_filename
    system = platform.system()
    if not silent:
        say(f"opening {db_path}")
    logging.debug("open_db_editor on %s (debug=%s)", system, debug)

    if system == "Windows":
        import os

        try:
            os.system(f'start excel "{str(db_path)}"')
        except Exception as exc:
            say(f"could not open {db_path} ({exc})")
        return

    if system not in ("Linux", "Darwin"):
        # untested territory; say so instead of shouting the platform name
        say(f"opening the database editor is untested on {system} - trying anyway")

    # not tested on any of these
    subprocess.check_call(["open", "-a", "Microsoft Excel", db_path])

# -- echo binder for moved CLI helpers (#651) -----------------------------------
# Public APIs take ``echo=`` and wrap work in ``_using_echo`` so private helpers
# can call ``_say`` without threading the callable through every signature.
# Quiet by default (same contract as ``convert`` / ``run_journal``).

_echo_var: ContextVar[Echo] = ContextVar("cellpy_cli_api_echo", default=_silent)


def _say(message: str, **_kwargs) -> None:
    """Report pre-formatted text via the bound echo.

    The transport for messages not yet converted to the `cli_ui`
    vocabulary (#891). Prefer ``_ui()`` for anything new.
    """
    _echo_var.get()(message)


def _debug(message: Any) -> None:
    """A diagnostic line: shown under ``--verbose``, hidden otherwise.

    The check helpers used to narrate every probe at full volume; the verdict
    is what a user needs, the narration is what they need when it goes wrong.
    """
    _ui().debug(str(message))


def _ui():
    """The active console reporter (see `cli_ui`).

    Commands that report structure - a check list, a verdict, a path with a
    note - use this instead of ``_say``, so what they print carries meaning
    (stream, colour, level) rather than being a string someone formatted by
    hand.

    A caller who passed no ``echo`` gets a reporter that prints nothing: these
    functions are a library first, and a library does not write to stdout
    because someone imported it.

    When the bound echo came from a reporter (``Reporter.as_echo`` /
    ``Reporter.payload``) that reporter is used, so a per-command ``--silent``
    or ``--debug`` adjusts this output as well as the ``_say`` lines.
    """
    from cellpy import cli_ui

    echo = _echo_var.get()
    if echo is _silent:
        return cli_ui.silent_reporter()
    bound = getattr(echo, "reporter", None) or getattr(echo, "__self__", None)
    if isinstance(bound, cli_ui.Reporter):
        return bound
    return cli_ui.current()


@contextmanager
def _using_echo(echo: Optional[Echo] = None):
    token = _echo_var.set(_resolve_echo(echo))
    try:
        yield
    finally:
        _echo_var.reset(token)


def _create_dir(path, confirm=True, parents=True, exist_ok=True):
    from cellpy.internals.otherpath import OtherPath

    if isinstance(path, OtherPath):
        if path.is_external:
            return path
    o = path.resolve()
    if not o.is_dir():
        o_parent = o.parent
        create_dir = True
        if confirm:
            if not o_parent.is_dir():
                create_dir = input(f"\n  {o_parent} does not exist. Create it? [y]/n > ")
                if not create_dir:
                    create_dir = True
                elif create_dir in ["y", "Y"]:
                    create_dir = True
                else:
                    create_dir = False

        ui = _ui()
        if create_dir:
            try:
                o.mkdir(parents=parents, exist_ok=exist_ok)
                ui.step(f"created {o}")
            except FileExistsError:
                _debug(f"{o} already exists")
            except FileNotFoundError:
                ui.warn("directory", f"{o} is not available")
            except Exception as e:
                ui.warn("directory", f"could not create {o}", hint="continuing anyway")
                logging.debug(e)
        else:
            ui.warn("directory", f"not created: {o}")
    return o

# -- setup file helpers --
def save_prm_file(prm_filename):
    """saves (writes) the prms to file"""
    prmreader._write_prm_file(prm_filename)


def dump_env_file(env_filename):
    """saves (writes) the env to file"""
    _debug(f"dumping env file to {env_filename}")
    prmreader._write_env_file(env_filename)


def get_package_prm_dir():
    """gets the folder where the cellpy package lives"""
    import cellpy.parameters

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
    """Report the optional modules that could not be imported."""
    _probe_optional_deps()
    ui = _ui()
    for m in DIFFICULT_MISSING_MODULES:
        ui.warn("missing module", m, hint=DIFFICULT_MISSING_MODULES[m])


# -- write toml --
def _write_toml_config_file(dst_file, dry_run, test_user=None):
    """Write the ``cellpy.toml`` twin generated from the config models.

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

    ui = _ui()
    if dry_run:
        ui.step(f"dry-run: would write {toml_path}")
        return

    data = cellpy_config.get_config().model_dump_for_file()
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    config_loader.write_toml(toml_path, data)
    ui.ok("cellpy.toml", str(toml_path))

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

    ui = _ui()

    if src is None:
        try:
            src = prmreader._get_prm_file()
        except Exception:
            src = None
        if src is None or not pathlib.Path(src).is_file():
            ui.warn(
                "migrate",
                "no legacy config file found - nothing to migrate",
                hint="cellpy setup writes a fresh cellpy.toml",
            )
            return
    src = pathlib.Path(src)

    toml_path = pathlib.Path(dst) if dst else config_loader.user_config_path()
    if toml_path.is_file() and not force:
        ui.warn(
            "migrate",
            f"{toml_path} already exists",
            hint="pass --force to overwrite it",
        )
        return

    ui.detail("source", str(src))
    ui.detail("target", str(toml_path))
    if dry_run:
        ui.step("dry-run: nothing written")
        return

    toml_path.parent.mkdir(parents=True, exist_ok=True)
    config_migrate.convert_yaml_file_to_toml(src, toml_path)
    ui.ok("migrated", str(toml_path))
    ui.hint("the legacy file is kept untouched")

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

    _debug(f"default_dir: {default_dir}")
    _debug(f"custom_dir: {custom_dir}")
    _debug(f"relative_home: {relative_home}")

    if custom_dir:
        reset = True
        if relative_home:
            h = h / custom_dir
        if not custom_dir.parts[-1] == default_dir:
            h = h / default_dir

    from cellpy.internals.otherpath import OtherPath

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

    _debug(f"base directory: {h}")

    if interactive:
        _ui().title("interactive setup - press enter to keep a suggested value")
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
            _ui().step(f"dry-run: would create {d}")

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


def _ask(q, current) -> str:
    """Ask for one setup value, showing the current one as the default (#891)."""
    ui = _ui()
    ui.blank()
    ui.step(q)
    ui.detail("current", str(current))
    return input("  > ").strip()


def _ask_about_path(q, p):
    return pathlib.Path(_ask(q, p) or p)


def _ask_about_otherpath(q, p):
    from cellpy.internals.otherpath import OtherPath

    return OtherPath(_ask(q, p) or p)


def _ask_about_name(q, n):
    return _ask(q, n) or n


@dataclass
class _CheckOutcome:
    """What one ``cellpy info --check`` line reports.

    The checks used to print their own verdict and a page of diagnostics.
    Returning the outcome instead lets the caller render it consistently -
    verdict row first, then its detail lines - and lets the diagnostics drop to
    ``--verbose`` where they belong.
    """

    ok: bool
    detail: str = ""
    hint: Optional[str] = None
    details: list = field(default_factory=list)

    def add(self, key: str, value: str, note: Optional[str] = None) -> None:
        """Record a key/value line to print underneath the verdict."""
        self.details.append((key, value, note))


def _as_outcome(result) -> _CheckOutcome:
    """Accept a bare bool from any check not yet returning an outcome."""
    if isinstance(result, _CheckOutcome):
        return result
    return _CheckOutcome(bool(result))


def _check_import_cellpy() -> _CheckOutcome:
    try:
        import cellpy  # noqa: F401
        from cellpy import log  # noqa: F401
        from cellpy.readers import cellreader  # noqa: F401

        return _CheckOutcome(True, "cellpy, log, cellreader")
    except Exception as exc:
        return _CheckOutcome(
            False,
            f"cannot import cellpy ({exc})",
            hint="reinstall cellpy, or check for a broken pyarrow/pandas install",
        )


def _check_import_pyodbc():
    import platform

    from cellpy.parameters import prms

    ODBC = prms._odbc
    SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver

    use_subprocess = config.instruments.Arbin.use_subprocess
    detect_subprocess_need = config.instruments.Arbin.detect_subprocess_need
    _debug(" This is needed for loading Arbin .res files")
    _debug(" parsing prms")
    _debug(
        " (from your configuration file if it exists, otherwise using defaults)"
    )
    _debug(f" - ODBC: {ODBC}")
    _debug(f" - SEARCH_FOR_ODBC_DRIVERS: {SEARCH_FOR_ODBC_DRIVERS}")
    _debug(f" - use_subprocess: {use_subprocess}")
    _debug(f" - detect_subprocess_need: {detect_subprocess_need}")
    _debug(f" - stated office version: {config.instruments.Arbin.office_version}")

    _debug(" checking system")
    is_posix = False
    is_macos = False
    if os.name == "posix":
        is_posix = True
        _debug(" - running on posix")
    current_platform = platform.system()
    if current_platform == "Darwin":
        is_macos = True
        _debug(" - running on a mac")

    python_version, os_version = platform.architecture()
    _debug(f" - python version: {python_version}")
    _debug(f" - os version: {os_version}")

    if not is_posix:
        if not config.instruments.Arbin.sub_process_path:
            sub_process_path = str(prms._sub_process_path)
        else:
            sub_process_path = str(config.instruments.Arbin.sub_process_path)
        _debug(f" stated path to sub-process: {sub_process_path}")
        if not os.path.isfile(sub_process_path):
            _debug(" - OBS! missing")

    if is_posix:
        _debug(" checking existence of mdb-export")
        sub_process_path = "mdb-export"
        from subprocess import PIPE, run

        command = ["command", "-v", sub_process_path]

        try:
            _debug(f" - trying to run {command}")
            result = run(
                command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True
            )
            if result.returncode == 0:
                _debug(" - found it!")
                return _CheckOutcome(True, f"{sub_process_path} on PATH")

            _debug(f" - could not find {sub_process_path}")

            if is_macos:
                driver = "/usr/local/lib/libmdbodbc.dylib"
                _debug(
                    f" looks like you are on a mac. Searching for suitable driver: {driver})"
                )
                if not os.path.isfile(driver):
                    _debug(f" - could not find {driver}")
                    _debug(
                        " ! If you want to load Arbin .res files you will have to install it manually."
                    )
                    _debug(" - Try installing it with brew:\n")
                    _debug("   brew install mdbtools")
                    return _CheckOutcome(
                        False,
                        "no mdbtools driver",
                        hint="brew install mdbtools",
                    )
                _debug(f" - found it: {driver}")
                return _CheckOutcome(True, driver)
            else:
                _debug(
                    " ! If you want to load Arbin .res files you will have to install it manually."
                )
                _debug("   For example (for ubuntu):\n")
                _debug("   sudp apt-get update")
                _debug("   sudp apt-get install -y mdbtools")
            return _CheckOutcome(
                False,
                "mdbtools not installed",
                hint="apt-get install mdbtools (see the docs for other systems)",
            )

        except AssertionError:
            _debug(" - could not find any suitable driver")
            return _CheckOutcome(False, "no suitable driver found")

    # not posix - checking for odbc drivers
    # 1) checking if you have defined one
    try:
        driver = config.instruments.Arbin.odbc_driver
        if not driver:
            raise AttributeError
        _debug(" You have defined an odbc driver in your config file")
        _debug(f" - driver: {driver}")
    except AttributeError:
        _debug(" FYI: you have not defined any odbc_driver(s)")
        _debug(
            " (The name of the driver from the configuration file is "
            "used as a backup when cellpy cannot locate a driver by itself)"
        )

    use_ado = False

    if ODBC == "ado":
        use_ado = True
        _debug(" you stated that you prefer the ado loader")
        _debug(" checking if adodbapi is installed")
        try:
            import adodbapi as dbloader
        except ImportError:
            use_ado = False
            _debug(" Failed! Try setting pyodbc as your loader or install")
            _debug(" adodbapi (http://adodbapi.sourceforge.net/)")

    if not use_ado:
        if ODBC == "pyodbc":
            _debug(" you stated that you prefer the pyodbc loader")
            try:
                import pyodbc as dbloader
            except ImportError:
                _debug(" Failed! Could not import it.")
                _debug(" Try 'pip install pyodbc'")
                dbloader = None

        elif ODBC == "pypyodbc":
            _debug(" you stated that you prefer the pypyodbc loader")
            try:
                import pypyodbc as dbloader  # type: ignore
            except ImportError:
                _debug(" Failed! Could not import it.")
                _debug(" try 'pip install pypyodbc'")
                _debug(" or set pyodbc as your loader in your prm file")
                _debug(" (and install it)")
                dbloader = None

    _debug(" searching for odbc drivers")
    try:
        drivers = [
            driver
            for driver in dbloader.drivers()
            if "Microsoft Access Driver" in driver
        ]
        _debug(f" Found these: {drivers}")
        driver = drivers[0]
        _debug(f" - odbc driver: {driver}")
        return _CheckOutcome(True, driver)

    except IndexError:
        logging.debug(" Unfortunately, it seems the list of drivers is emtpy.")
        _debug(
            "\n Could not find any odbc-drivers suitable for .res-type files. "
            "Check out the homepage of pydobc for info on installing drivers"
        )
        _debug(
            " One solution that might work is downloading "
            "the Microsoft Access database engine "
            "(in correct bytes (32 or 64)) "
            "from:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=13255"
        )
        _debug(
            " Or install mdbtools and set it up (check the cellpy docs for help)"
        )
        _debug("\n")
        return _CheckOutcome(
            False,
            "no odbc driver for .res files",
            hint="install the Microsoft Access Database Engine, or mdbtools",
        )


def _check_config_file():
    from cellpy.config.loader import active_config_file

    outcome = _CheckOutcome(True)
    prm_file_name = active_config_file().path
    env_file_name = prmreader.get_env_file_name()

    if env_file_name is None or not os.path.isfile(env_file_name):
        outcome.add("env file", str(env_file_name or "not set"), "not found")

    if prm_file_name is None:
        return _CheckOutcome(False, "no configuration file", hint="cellpy setup")

    # Check the *resolved* paths rather than re-parsing the file: those are the
    # ones cellpy will use, and it works for both cellpy.toml and legacy YAML
    # (the YAML reader cannot read TOML at all) -- see #851.
    from cellpy import config as cellpy_config

    try:
        prm_paths = cellpy_config.get_config().paths.model_dump()
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
        from cellpy.internals.otherpath import OtherPath
        from cellpy.parameters.internal_settings import OTHERPATHS

        missing = 0
        for k in required_dirs:
            value = prm_paths.get(k, None)
            if not value:
                missing += 1
                outcome.add(k, "not set", "missing")
                continue
            # OTHERPATHS lists the settings that *may* point somewhere remote,
            # not the ones that do - so ask the value itself. A local path in
            # one of those settings still gets checked, which is why a wrong
            # cellpydatadir used to be waved through as "external".
            if k in OTHERPATHS and OtherPath(value).is_external:
                # Verifying a remote path costs a connection; a wrong one is
                # reported properly by the load that needs it.
                outcome.add(k, str(value), "remote, not checked")
            elif not pathlib.Path(value).is_dir():
                missing += 1
                outcome.add(k, str(value), "not a directory")
            else:
                outcome.add(k, str(value))

        value = prm_paths.get("db_filename", None)
        if value:
            outcome.add("db_filename", str(value))
        else:
            missing += 1
            outcome.add("db_filename", "not set", "missing")

        if missing:
            outcome.ok = False
            outcome.detail = f"{missing} path(s) missing or unusable"
            outcome.hint = "cellpy edit config"
        else:
            outcome.detail = str(prm_file_name)
        return outcome

    except Exception as exc:
        return _CheckOutcome(False, f"could not read the configuration ({exc})")


def _check(dry_run=False, full_check=True) -> int:
    """Report what works and what does not, one line per check (#891).

    Returns:
        How many checks failed, so a caller can exit non-zero.
    """
    ui = _ui()
    if dry_run:
        ui.warn("dry run", "checks skipped")
        return 0

    ui.title(f"cellpy {VERSION} - checking your setup")

    checks = [
        ("imports", _check_import_cellpy),
        ("arbin .res support", _check_import_pyodbc),
    ]
    # Reading the config is not part of `setup`, which runs before there is one.
    if full_check:
        checks.append(("configuration", _check_config_file))

    failed = 0
    for label, check_func in checks:
        try:
            outcome = _as_outcome(check_func())
        except Exception as exc:
            outcome = _CheckOutcome(False, f"the check itself raised {exc!r}")
        if outcome.ok:
            ui.ok(label, outcome.detail)
        else:
            failed += 1
            ui.fail(label, outcome.detail, hint=outcome.hint)
        for key, value, note in outcome.details:
            ui.detail(key, value, note=note)

    ui.summary(len(checks) - failed, len(checks))
    return failed


def _write_config_file(user_dir, dst_file, init_filename, dry_run):
    """Write the user config file, reporting one line per real action (#891)."""
    from cellpy.exceptions import ConfigFileNotWritten

    ui = _ui()
    _debug(f"user directory: {user_dir}")

    if dry_run:
        ui.step(f"dry-run: would write {dst_file}")
        return

    if os.path.isfile(dst_file):
        _debug(f"{dst_file} exists - keeping the settings it already holds")

    try:
        save_prm_file(dst_file)
    except ConfigFileNotWritten:
        ui.warn(
            "configuration file",
            f"could not write {dst_file}",
            hint=f"retrying as {prmreader.DEFAULT_FILENAME}",
        )
        try:
            user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
            save_prm_file(dst_file)
        except ConfigFileNotWritten as exc:
            ui.fail(
                "configuration file",
                f"could not write {dst_file} ({exc})",
                hint="check the directory permissions, then report this at "
                "https://github.com/jepegit/cellpy/issues",
            )
            return

    ui.ok("configuration file", str(dst_file))
    ui.hint("edit it with:  cellpy edit config")


def _write_env_file(user_dir, dst_file, dry_run):
    """Write the ``.env_cellpy`` file, reporting one line per real action (#891)."""
    from cellpy.exceptions import ConfigFileNotWritten

    ui = _ui()

    if os.path.isfile(dst_file):
        if not dry_run:
            ui.ok("environment file", f"{dst_file} (kept)")
            return
        ui.step(f"dry-run: would keep {dst_file}")
        return

    if dry_run:
        ui.step(f"dry-run: would write {dst_file}")
        return

    try:
        dump_env_file(dst_file)
    except ConfigFileNotWritten as exc:
        ui.fail(
            "environment file",
            f"could not write {dst_file} ({exc})",
            hint="check the directory permissions, then report this at "
            "https://github.com/jepegit/cellpy/issues",
        )
        return

    ui.ok("environment file", str(dst_file))
    ui.hint("edit it with:  cellpy edit env")


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
    """Print resolved config values with per-field provenance."""
    from cellpy import config as cellpy_config

    data = cellpy_config.get_config().model_dump_for_file()
    provenance = cellpy_config.sources()
    ui = _ui()
    ui.payload("# resolved configuration (value  # source-layer)")
    for section, fields in data.items():
        ui.payload(f"\n[{section}]")
        if not isinstance(fields, dict):
            ui.payload(f"  {fields!r}")
            continue
        for key, value in fields.items():
            layer = provenance.get(f"{section}.{key}", "default")
            ui.payload(f"  {key} = {value!r}  # {layer}")

# -- pull clone/tests/examples --
def _clone_repo(directory, password):
    """``cellpy pull --clone`` has never cloned anything - say so plainly."""
    ui = _ui()
    ui.warn("--clone", "not implemented yet")
    ui.hint(f"clone it yourself:  git clone {REPO_URL}")


def _pull_tests(directory, pw=None):
    # was _say(tuple) - which printed the tuple repr, not the sentence
    _ui().step(f"pulling tests from {REPO_URL}")
    _pull(gdirpath="tests", rootpath=directory, pw=pw)
    _pull(gdirpath="testdata", rootpath=directory, pw=pw)


def _pull_examples(directory, pw):
    _ui().step(f"pulling examples from {REPO_URL}")
    _pull(gdirpath="examples", rootpath=directory, pw=pw)

# -- version/configloc/envloc/dump_params --
def _version():
    _ui().payload(f"cellpy {VERSION}")


def _configloc():
    """Report the config file cellpy actually reads (``None`` when there is none)."""
    from cellpy.config.loader import CONFIG_FILENAME, active_config_file

    ui = _ui()
    active = active_config_file()
    if active.path is None:
        _, config_file_name = prmreader.get_user_dir_and_dst()
        ui.fail("config", f"{config_file_name} does not exist", hint="cellpy setup")
        if active.project_path is not None:
            ui.detail("project config", str(active.project_path), note="takes precedence")
        return None

    ui.payload(f"config   {active.path}")
    if active.shadowed_legacy is not None:
        ui.detail(
            "legacy",
            str(active.shadowed_legacy),
            note=f"ignored, {CONFIG_FILENAME} wins",
        )
    if active.project_path is not None:
        ui.detail("project", str(active.project_path), note="takes precedence")
    return active.path


def _envloc():
    env_file_name = prmreader.get_env_file_name()
    ui = _ui()
    if not os.path.isfile(env_file_name):
        ui.fail("env", f"{env_file_name} does not exist", hint="cellpy setup")
        return
    ui.payload(f"env      {env_file_name}")
    return env_file_name


def _dump_params():
    prmreader.info()


# -- github download helpers --
def _download_g_blob(name, local_path):
    import urllib.request

    dirs = local_path.parent
    if not dirs.is_dir():
        _debug(f"creating {dirs}")
        dirs.mkdir(parents=True)
    _debug(f"downloading {name.download_url}")
    filename, headers = urllib.request.urlretrieve(
        name.download_url, filename=local_path
    )
    _ui().step(f"downloaded {filename}")


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

    ui = _ui()

    if pw is not None:
        _debug("dev mode: authenticating against github")
        u = _get_user_name()
        if pw == "ask":
            pw = _get_pw(pw)
        elif pw == "env":
            pw = _get_pw(pw)
            if pw is None:
                _debug("no password in the environment - falling back to anonymous")
                u = None

    _probe_optional_deps()
    g = Github(u, pw)
    try:
        repo = g.get_repo(REPO)
    except github.RateLimitExceededException:
        _rate_limited(ui)
        repo = g.get_repo(REPO)

    ui.step(f"pulling {gdirpath} -> {ndirpath}")

    if not ndirpath.is_dir():
        ui.step(f"creating {ndirpath}")
        ndirpath.mkdir(parents=True)

    for gfile in _parse_g_dir(repo, gdirpath):
        gfilename = pathlib.Path(gfile.path)
        nfilename = rootpath / gfilename
        try:
            _download_g_blob(gfile, nfilename)
        except github.RateLimitExceededException:
            _rate_limited(ui)
            _download_g_blob(gfile, nfilename)

    ui.ok("pulled", str(ndirpath))


def _rate_limited(ui) -> None:
    """Report a GitHub rate limit and wait once before retrying."""
    ui.warn(
        "github rate limit",
        "waiting 60 seconds, then trying once more (ctrl-c to abort)",
        hint="check your quota with:  curl -i https://api.github.com/users/USERNAME",
    )
    time.sleep(60)

# -- templates --
def _get_default_template():
    template = "standard"
    try:
        template = config.batch.template
    except Exception:
        logging.debug("You dont have any default template defined in you .conf file")
    return template


def _template_location(entry) -> str:
    """Where a registered template lives.

    The registry stores ``(location, cookie_subdirectory)``; only the location
    means anything to a user reading ``cellpy new --list``.
    """
    if isinstance(entry, (tuple, list)):
        return str(entry[0])
    return str(entry)


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
        The `cellpy.cli_api.list_templates` dictionary when ``list_`` is True,
        else None.
    """

    try:
        import cookiecutter.exceptions
        import cookiecutter.main
        import cookiecutter.prompt

    except ModuleNotFoundError:
        _ui().fail(
            "cookiecutter",
            "Could not import cookiecutter.",
            hint="python -m pip install cookiecutter",
        )
        return

    ui = _ui()

    if list_:
        templates = list_templates()

        ui.title("batch templates")
        ui.detail("default", str(templates["default"]))
        ui.blank()
        ui.step("registered (on github)")
        for label, link in templates["registered"].items():
            ui.detail(label, link)
        ui.step(f"local ({templates['templatedir']})")
        if templates["local"]:
            for label, link in templates["local"].items():
                ui.detail(label, link)
        else:
            ui.detail("none", "-")

        return templates

    if project_dir is None or session_id is None:
        no_input = False

    if not template:
        template = _get_default_template()

    if lab:
        server = "lab"
    else:
        server = "notebook"

    ui.step(f"template: {template}")
    if local_user_template:
        # forcing using local template
        templates = _read_local_templates()

        if not templates:
            ui.fail(
                "template",
                "no local templates found",
                hint=f"put a cellpy_cookie_*.zip in {config.paths.templatedir}",
            )
            return
    else:
        templates = REGISTERED_TEMPLATES
        if local_templates := _read_local_templates():
            templates.update(local_templates)

    if template.lower() not in templates:
        ui.fail(
            "template",
            f"no template named {template!r}",
            hint="cellpy new --list to see the known ones",
        )
        return

    if directory is None:
        logging.debug("no dir given")
        directory = config.paths.notebookdir

    if not os.path.isdir(directory):
        ui.fail(
            "notebook directory",
            f"{directory} does not exist",
            hint="cellpy setup, or pass --directory",
        )
        return

    directory = pathlib.Path(directory)
    selected_project_dir = None

    if project_dir:
        selected_project_dir = directory / project_dir
        if not selected_project_dir.is_dir():
            if no_input or cookiecutter.prompt.read_user_yes_no(
                f"{project_dir} does not exist. Create?", "yes"
            ):
                os.mkdir(selected_project_dir)
                ui.step(f"created {selected_project_dir}")

            else:
                selected_project_dir = None
                ui.step("pick another directory instead")
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
                ui.step(f"created {project_dir}")
            except FileExistsError:
                ui.step(f"{project_dir} already exists - using it")
        selected_project_dir = directory / project_dir

    # get a list of all folders
    existing_projects = os.listdir(selected_project_dir)

    os.chdir(selected_project_dir)
    import cellpy as _cellpy

    cellpy_version = _cellpy.__version__

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
        ui.fail("project", f"cookiecutter refused to create the project ({e})")

    if serve_:
        os.chdir(directory)
        _serve(server, executable)

    elif run_:
        ui.warn("--run", "experimental - use at your own risk")
        input("  press enter to continue > ")
        import importlib.util

        if importlib.util.find_spec("papermill") is None:
            ui.fail(
                "papermill",
                "needed to execute the notebooks automatically",
                hint="python -m pip install papermill",
            )
            return
        new_existing_projects = os.listdir(selected_project_dir)
        our_new_projects = list(set(new_existing_projects) - set(existing_projects))

        if not len(our_new_projects):
            ui.fail(
                "project",
                "could not tell which project is the new one, so nothing was run",
                hint="run the notebooks yourself, or start from an empty directory",
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
        logging.debug("could not get the author name: %s", e)
        author_name = "unknown"
    return author_name


def _serve(server, executable=None):
    _ui().step(f"serving with jupyter {server}")
    # TODO: search for jupyter and find the right one
    if executable is None:
        executable = "jupyter"
    subprocess.run([executable, server], check=True)
    _ui().step("stopped serving")



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
    deps: bool = False,
    no_deps: bool = False,
    check: bool = False,
    echo: Optional[Echo] = None,
):
    """Write / refresh the user cellpy configuration (library form of ``cellpy setup``).

    Args:
        deps: When True, probe optional CLI extras (cookiecutter, lmfit, …)
            and print tips for any that are missing. Default False (#839).
        no_deps: Deprecated no-op kept for old scripts (#839). Ignored.
        check: When True, run the import/config sanity checks (may load
            ``cellreader``). Default False; use ``cellpy info --check`` or
            ``cellpy setup --check`` (#839).
    """
    with _using_echo(echo):
        ui = _ui()
        ui.title(f"cellpy {VERSION} - setting up")

        if no_deps and not deps:
            ui.warn(
                "--no-deps",
                "deprecated no-op",
                hint="dependency probing is off by default; use --deps to turn it on",
            )

        # Optional extras — opt-in only so default setup stays off the heavy stack (#839).
        if deps:
            _probe_optional_deps()
            ui.step("checking dependencies")
            for m in DIFFICULT_MISSING_MODULES:
                ui.warn("missing dependency", m, hint=DIFFICULT_MISSING_MODULES[m])

        # generate variables
        init_filename = prmreader.create_custom_init_filename()
        user_dir, dst_file = prmreader.get_user_dir_and_dst(init_filename)
        env_file = prmreader.get_env_file_name()

        # The parameter dump was the loudest thing `setup --dry-run` printed and
        # the least useful to a user; it is developer detail, so it lives at
        # --verbose now (#891).
        _debug(f"init_filename: {init_filename}")
        _debug(f"user_dir: {user_dir}")
        _debug(f"dst_file: {dst_file}")
        _debug(f"not_relative: {not_relative}")

        if root_dir and not interactive:
            ui.warn(
                "--root-dir",
                "only has an effect in interactive mode",
                hint="continuing in interactive mode",
            )
            interactive = True

        if not root_dir:
            root_dir = user_dir
            # root_dir = pathlib.Path(os.getcwd())
        root_dir = pathlib.Path(root_dir)
        _debug(f"root_dir: {root_dir}")

        if test_user:
            init_filename = prmreader.create_custom_init_filename(test_user)
            user_dir = root_dir
            dst_file = get_dst_file(user_dir, init_filename)
            _debug(f"test user {test_user}: user_dir={user_dir} dst_file={dst_file}")

        if not pathlib.Path(dst_file).is_file():
            ui.step(f"no configuration file yet - writing {dst_file}")
            reset = True

        if not pathlib.Path(env_file).is_file():
            ui.step(f"no environment file yet - writing {env_file}")

        if interactive:
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

        if check:
            _check(dry_run=dry_run, full_check=interactive)


# -- public facades (#651) ------------------------------------------------------


def show_info(
    *,
    version: bool = False,
    configloc: bool = False,
    params: bool = False,
    show_config: bool = False,
    check: bool = False,
    echo: Optional[Echo] = None,
) -> int:
    """Library form of ``cellpy info``.

    Returns:
        The number of failed checks (always 0 unless ``check`` is set), so the
        CLI can exit non-zero when the setup is broken.
    """
    with _using_echo(echo):
        complete_info = True
        failed = 0
        if check:
            complete_info = False
            failed = _check()
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
        return failed


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
            _ui().fail(
                "notebook directory",
                f"{directory} does not exist",
                hint="cellpy setup, or pass --directory",
            )
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

        ui = _ui()
        if key is not None and key not in ("env", "config"):
            ui.fail("edit", f"unknown file {name!r}", hint="try: config, env or db")
            return

        if key is None or key == "config":
            config_file = _configloc()
            if config_file is None:
                ui.fail("config file", "not found", hint="cellpy setup")
                return
            filename = str(pathlib.Path(config_file).resolve())
        elif key == "env":
            filename = _envloc()
            if filename is None:
                ui.fail("environment file", "not found", hint="cellpy setup")
                return
        else:
            filename = name

        if default_editor is None:
            default_editor = _get_default_editor()

        args = [default_editor, filename]
        ui.step(f"opening {filename} with {default_editor}")
        try:
            subprocess.call(args)
        except Exception as exc:
            ui.fail(
                "editor",
                f"could not start {default_editor} ({exc})",
                hint="name one yourself, e.g. cellpy edit -e notepad.exe",
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
            _debug(f"custom directory: {directory}")
        else:
            directory = pathlib.Path(config.paths.examplesdir)

        if password is not None:
            _debug("dev mode: password provided")
        if clone:
            _clone_repo(directory, password)
        else:
            if tests:
                _pull_tests(directory, password)
            if examples:
                _pull_examples(directory, password)
            elif not tests:
                _ui().fail(
                    "pull",
                    "nothing selected",
                    hint="pick one of --tests, --examples or --clone",
                )


def list_templates() -> dict:
    """The batch templates ``cellpy new`` knows about, as data.

    The library form of ``cellpy new --list``: enough to name every template,
    say which one is the default, and tell registered from local apart without
    reaching for private helpers.

    Returns:
        dict: ``default`` (the template used when none is given), ``registered``
        (the GitHub-hosted templates as ``{name: location}``), ``local`` (the
        same shape for templates found in the template directory), and
        ``templatedir`` (where the local ones are looked up).

    Example:
        >>> templates = list_templates()
        >>> templates["default"] in templates["registered"]
        True
    """
    return {
        "default": _get_default_template(),
        "registered": {
            label: _template_location(entry)
            for label, entry in REGISTERED_TEMPLATES.items()
        },
        "local": {
            label: _template_location(entry)
            for label, entry in _read_local_templates().items()
        },
        "templatedir": str(config.paths.templatedir),
    }


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


# ----------------------- mcp ----------------------------------------
#
# `cellpy mcp` is a *shim*. The MCP server lives in a separate distribution,
# `cellpy-mcp`, and cellpy deliberately does not depend on it: the MCP Python
# SDK is young and moving (2.0 renamed `FastMCP` to `MCPServer` and ships two
# `Context` classes with different attributes), and a long-lived network-facing
# process is a security surface a data library should not carry. Keeping the
# server out means it can move at the SDK's pace instead of cellpy's release
# cadence — while the entry point still lives where people look for it.
#
# So cellpy gains a command, not a dependency. What that costs is a contract:
#
#   cellpy_mcp.__version__
#   cellpy_mcp.serve(root=None)                      -> None (blocks on stdio)
#   cellpy_mcp.install(root=None, client=None, dry_run=False) -> str
#
# `status` is the exception and is implemented here, because its whole job is
# to answer "is it installed?" — a question that cannot be delegated to the
# thing whose absence is the answer.

#: The distribution to install, and the module it provides. Different strings
#: on purpose: `pip install cellpy-mcp` gives you `import cellpy_mcp`, and a
#: hint that prints the wrong one sends people to a 404.
MCP_DISTRIBUTION = "cellpy-mcp"
MCP_MODULE = "cellpy_mcp"


def _import_mcp():
    """The server package, or ``None`` after reporting how to install it."""
    import importlib

    try:
        return importlib.import_module(MCP_MODULE)
    except ImportError:
        _ui().fail(
            "mcp",
            f"{MCP_DISTRIBUTION} is not installed.",
            hint=f"python -m pip install {MCP_DISTRIBUTION}",
        )
        return None


def mcp_serve(root=None, echo: Optional[Echo] = None):
    """Run the MCP server over stdio. Returns true when it could not start.

    This blocks: an MCP client spawns it as a subprocess and talks to it over
    stdin/stdout, so there is nothing to background and nothing to connect to.
    Running it by hand is mostly useful for seeing that it starts.
    """
    with _using_echo(echo):
        module = _import_mcp()
        if module is None:
            return True
        # Nothing is printed on the way up: stdout *is* the protocol channel,
        # and a friendly banner on it is a parse error at the other end.
        module.serve(root=root)
        return False


def mcp_install(
    root=None,
    client: Optional[str] = None,
    dry_run: bool = False,
    echo: Optional[Echo] = None,
):
    """Register the server with a chat client. Returns true on failure."""
    with _using_echo(echo):
        module = _import_mcp()
        if module is None:
            return True

        ui = _ui()
        try:
            where = module.install(root=root, client=client, dry_run=dry_run)
        except Exception as exc:  # noqa: BLE001 - the reason belongs on screen
            ui.fail("mcp install", str(exc))
            return True

        ui.ok("registered" if not dry_run else "would register", str(where))
        if not dry_run:
            ui.hint("restart the client to pick it up")
        return False


def mcp_status(echo: Optional[Echo] = None):
    """Report whether the server is installed, and what it would serve.

    Answers the three questions someone actually has when a chat client says
    it cannot see cellpy: is the package there, which cellpy would it use, and
    which directory would it be allowed to read.
    """
    import importlib
    import importlib.metadata

    with _using_echo(echo):
        from cellpy import __version__ as cellpy_version

        ui = _ui()
        ui.title("cellpy mcp")

        try:
            module = importlib.import_module(MCP_MODULE)
        except ImportError:
            ui.detail("server", "not installed")
            ui.detail("cellpy", cellpy_version)
            ui.hint(f"python -m pip install {MCP_DISTRIBUTION}")
            # Not an error: "not installed" is a true and useful answer, and a
            # non-zero exit would make `cellpy mcp status` unscriptable as the
            # check it exists to be.
            return False

        try:
            version = importlib.metadata.version(MCP_DISTRIBUTION)
        except importlib.metadata.PackageNotFoundError:
            # Importable but not installed as a distribution — an editable
            # checkout on the path. Worth saying rather than guessing.
            version = getattr(module, "__version__", "unknown (not installed)")

        ui.detail("server", version)
        ui.detail("cellpy", cellpy_version)
        describe = getattr(module, "describe", None)
        if callable(describe):
            for key, value in describe().items():
                ui.detail(key, str(value))
        return False
