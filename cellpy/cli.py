"""Typer CLI adapters — thin wrappers around ``cellpy.cli_api``."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any, Callable, Optional

import typer

from cellpy import cli_ui

cli = typer.Typer(
    name="cellpy",
    help="cellpy - command line interface.",
    # Click did not offer these, and the CLI surface is a contract (#569).
    add_completion=False,
)

setup_app = typer.Typer()


@cli.callback()
def main(
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Only report problems and output you asked for.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Report extra detail."),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Never colour the output (NO_COLOR is honoured too).",
        ),
    ] = False,
) -> None:
    """cellpy - command line interface."""
    if no_color:
        # Typer renders usage errors through its own rich console, which our
        # reporter knows nothing about. NO_COLOR is the switch both honour, so
        # setting it keeps the promise for every line the process prints.
        os.environ["NO_COLOR"] = "1"
    cli_ui.set_reporter(
        cli_ui.make_reporter(quiet=quiet, verbose=verbose, no_color=no_color)
    )


def _echo(
    *, silent: bool = False, debug: bool = False, payload: bool = False
) -> Callable[[str], None]:
    """The reporter's echo for this invocation.

    A per-command ``--silent`` / ``--debug`` adjusts only this command, leaving
    the reporter the global flags installed alone.

    ``payload`` marks a command whose whole output *is* the answer the user
    asked for (``cellpy info``): those lines survive ``--quiet``, because
    silencing progress must not silence the answer.
    """
    reporter = cli_ui.current()
    if silent:
        reporter = reporter.with_level(cli_ui.Level.QUIET)
    elif debug:
        reporter = reporter.with_level(cli_ui.Level.VERBOSE)
    if payload:
        return reporter.payload
    return reporter.as_echo()


class _CliApiProxy:
    """Defer ``cellpy.cli_api`` import until a command actually runs (#837)."""

    _mod: Any = None

    def _load(self):
        if self._mod is None:
            from cellpy import cli_api as _cli_api

            self._mod = _cli_api
        return self._mod

    def __getattr__(self, name: str):
        return getattr(self._load(), name)


cli_api = _CliApiProxy()


# ----------------------- setup --------------------------------------


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
    deps: Annotated[
        bool,
        typer.Option(
            "--deps",
            help="Probe optional extras (cookiecutter, lmfit, …) and report missing ones.",
        ),
    ] = False,
    no_deps: Annotated[
        bool,
        typer.Option(
            "--no-deps",
            help="Deprecated no-op: optional dependency probing is off by default.",
            hidden=True,
        ),
    ] = False,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Run import/config sanity checks after setup (may load the reader stack).",
        ),
    ] = False,
):
    """This will help you to set up cellpy."""
    if ctx.invoked_subcommand is not None:
        return
    cli_api.setup_config(
        interactive=interactive,
        not_relative=not_relative,
        dry_run=dry_run,
        reset=reset,
        root_dir=root_dir,
        folder_name=folder_name,
        test_user=test_user,
        silent=silent,
        deps=deps,
        no_deps=no_deps,
        check=check,
        echo=_echo(),
    )


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
    cli_api.migrate_config(
        src=src, dst=dst, dry_run=dry_run, force=force, echo=_echo()
    )


# Re-exports used by tests / callers that imported helpers from cellpy.cli
def get_package_prm_dir():
    return cli_api.get_package_prm_dir()


def _write_toml_config_file(dst_file, dry_run, test_user=None):
    """Shim for tests that still call ``cli._write_toml_config_file``."""
    with cli_api._using_echo(typer.echo):
        return cli_api._write_toml_config_file(dst_file, dry_run, test_user=test_user)


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
    cli_api.edit_file(
        name,
        default_editor=default_editor,
        debug=debug,
        silent=silent,
        echo=_echo(silent=silent, debug=debug),
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
    cli_api.show_info(
        version=version,
        configloc=configloc,
        params=params,
        show_config=show_config,
        check=check,
        # `info` answers a question; every line is payload, so --quiet keeps it.
        echo=_echo(payload=True),
    )


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
        cli_api.list_journals(None if name == "NONE" else name, echo=_echo())
        return

    if name == "NONE":
        # Typer renders this as a real usage error on stderr, exit code 2 -
        # the same treatment `cellpy convert` already gets for a bad path.
        raise typer.BadParameter("give a NAME to run, or --list to see them.")

    ui = cli_ui.current()
    if silent:
        ui = ui.with_level(cli_ui.Level.QUIET)
    elif debug:
        ui = ui.with_level(cli_ui.Level.VERBOSE)
    ui.debug(f"debug mode on (running {name})")

    if cellpy_project:
        cli_api.run_project(name, echo=ui.as_echo())
    elif journal:
        cli_api.run_journal(
            name,
            debug=debug,
            silent=silent,
            raw=raw,
            cellpyfile=cellpyfile,
            minimal=minimal,
            nom_cap=nom_cap,
            echo=ui.as_echo(),
        )
    elif folder:
        cli_api.run_journals(
            name,
            debug=debug,
            silent=silent,
            raw=raw,
            cellpyfile=cellpyfile,
            minimal=minimal,
            echo=ui.as_echo(),
        )
    elif key:
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
            echo=ui.as_echo(),
        )
    else:
        # Was a flag dump plus "sorry, I am not allowed to run this on my own",
        # printed to stdout with a success exit code.
        raise typer.BadParameter(
            "say what to run with NAME: --journal, --key, --folder "
            "or --cellpy-project."
        )


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
    cli_api.pull_resources(
        tests=tests,
        examples=examples,
        clone=clone,
        directory=directory,
        password=password,
        echo=_echo(),
    )


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
    cli_api.create_project(
        template,
        directory=directory,
        project=project,
        experiment=experiment,
        local_user_template=local_user_template,
        serve_=serve_,
        run_=run_,
        lab=lab,
        jupyter_executable=jupyter_executable,
        list_=list_,
        echo=_echo(),
    )


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
    cli_api.start_jupyter(
        lab=lab, directory=directory, executable=executable, echo=_echo()
    )


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
        cli_api.convert(old_h5, new_h5, to=to, echo=_echo())
    except ValueError as exc:
        # A rejected --to is a usage error: stderr, exit 2 (was stdout, exit 2).
        cli_ui.current().fail("convert", str(exc))
        raise typer.Exit(code=2)


if __name__ == "__main__":
    cli_api.show_info(check=True, echo=_echo())
