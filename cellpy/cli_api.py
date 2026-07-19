"""Library-first API behind the ``cellpy`` command line (CLI plan Phase 0–1, #568).

What a command *does* and how it is *spelled* were the same code, so anything
the CLI could do was unreachable from a script: you either shelled out to
``cellpy run -j journal.json`` and parsed stdout, or you reimplemented it.

The logic lives here as ordinary typed functions, and ``cellpy.cli`` becomes
argument parsing that calls them. Nothing about the command line changes — this
is a move, not a redesign — and it makes the eventual Click→Typer cutover (#569)
a re-spelling rather than a rewrite.

**Output.** These functions are quiet by default, as a library should be. Each
takes an ``echo`` callable; the CLI passes ``click.echo``, so the terminal
output is byte-identical to before, while a script that calls
``cli_api.run_journal(...)`` gets silence unless it asks otherwise::

    from cellpy import cli_api
    cli_api.run_journal("my_experiment.json")            # quiet
    cli_api.run_journal("my_experiment.json", echo=print)  # chatty
"""

from __future__ import annotations

import pathlib
import platform
import subprocess
from typing import Any, Callable, Optional, Union

import cellpy.config as config

PathLike = Union[str, pathlib.Path]
Echo = Callable[[str], None]


def _silent(_message: str) -> None:
    """Default ``echo``: a library does not print unless asked to."""


def _resolve_echo(echo: Optional[Echo]) -> Echo:
    return echo if echo is not None else _silent


# -- convert --------------------------------------------------------------------


def convert(
    source: PathLike,
    destination: Optional[PathLike] = None,
    *,
    echo: Optional[Echo] = None,
) -> pathlib.Path:
    """Upgrade a legacy cellpy-file to the current v8 HDF5 layout.

    Args:
        source: the old cellpy file.
        destination: where to write. Defaults to ``<name>_v8<suffix>`` beside
            the source, which is what the CLI has always done.
        echo: progress reporter; quiet by default.

    Returns:
        The path written.
    """
    say = _resolve_echo(echo)

    from cellpy.readers.cellpy_file import load as cellpy_file_load
    from cellpy.readers.cellpy_file import save as cellpy_file_save

    old_path = pathlib.Path(source)
    if destination is None:
        new_path = old_path.with_name(f"{old_path.stem}_v8{old_path.suffix}")
    else:
        new_path = pathlib.Path(destination)

    say(f"[cellpy] (convert) loading {old_path}")
    result = cellpy_file_load(old_path, accept_old=True)
    say(f"[cellpy] (convert) saving v{result.file_version} -> v8 as {new_path}")
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
