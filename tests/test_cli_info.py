"""What ``cellpy info`` and ``cellpy info --check`` report (#891).

The check list used to be banner soup: ``=== checking ===``, a page of probe
narration per check, ``f[cellpy] -> failed!!!!`` (the ``f`` was a typo that
reached users), and a verdict that never reached the exit code. These tests
pin the parts a user or a script depends on.
"""

from __future__ import annotations

import re

import pytest
from typer.testing import CliRunner

import cellpy
from cellpy import cli_api, cli_ui
from cellpy.cli import cli

runner = CliRunner()

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(text: str) -> str:
    return _ANSI.sub("", text)


@pytest.fixture(autouse=True)
def fresh_reporter(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    with cli_ui.using_reporter(None):
        yield


@pytest.fixture
def one_failing_check(monkeypatch):
    """Make a *required* check fail (imports), without needing a broken install.

    Arbin ``.res`` support is advisory (#1111): soft-failing it must not drive
    the exit-code tests below.
    """
    monkeypatch.setattr(
        cli_api,
        "_check_import_cellpy",
        lambda: cli_api._CheckOutcome(
            False, "cannot import cellpy", hint="reinstall cellpy"
        ),
    )


@pytest.fixture
def soft_arbin_fail(monkeypatch):
    """Missing Arbin tooling warns but must not fail the process (#1111)."""
    monkeypatch.setattr(
        cli_api,
        "_check_import_pyodbc",
        lambda: cli_api._CheckOutcome(
            False,
            "no odbc driver for .res files",
            hint="install the Microsoft Access Database Engine, or mdbtools",
            required=False,
        ),
    )
    # Keep the other two green so only the soft check is off.
    monkeypatch.setattr(
        cli_api,
        "_check_import_cellpy",
        lambda: cli_api._CheckOutcome(True, "fine"),
    )
    monkeypatch.setattr(
        cli_api,
        "_check_config_file",
        lambda: cli_api._CheckOutcome(True, "fine"),
    )


@pytest.fixture
def every_check_passes(monkeypatch):
    """Stub all three checks green.

    Whether a real machine passes them depends on what is installed and
    configured - CI has no user config file, so the configuration check fails
    there quite correctly. A test about the *exit code* must not depend on it.
    """
    for name in (
        "_check_import_cellpy",
        "_check_import_pyodbc",
        "_check_config_file",
    ):
        monkeypatch.setattr(
            cli_api, name, lambda: cli_api._CheckOutcome(True, "fine")
        )


# -- info -------------------------------------------------------------------


@pytest.mark.essential
def test_version_is_the_program_and_the_number():
    result = runner.invoke(cli, ["info", "--version"])

    assert result.exit_code == 0
    assert plain(result.output).strip() == f"cellpy {cellpy.__version__}"


@pytest.mark.essential
def test_info_reports_the_config_file_it_actually_reads():
    result = runner.invoke(cli, ["info", "--configloc"])

    assert result.exit_code == 0
    assert "config" in plain(result.output)


# -- info --check -----------------------------------------------------------


@pytest.mark.essential
def test_check_lists_one_line_per_check_and_a_verdict():
    result = runner.invoke(cli, ["info", "--check"])
    output = plain(result.output)

    for label in ("imports", "arbin .res support", "configuration"):
        assert label in output, label
    assert "checks passed" in output


@pytest.mark.essential
def test_check_does_not_shout_or_draw_banners():
    """No `=== checking ===`, no 80-column rules, no `failed!!!!`."""
    output = plain(runner.invoke(cli, ["info", "--check"]).output)

    assert "=" * 20 not in output
    assert "-" * 20 not in output
    assert "!!!!" not in output
    assert "f[cellpy]" not in output


@pytest.mark.essential
def test_check_keeps_the_probe_narration_for_verbose():
    """The diagnostics are useful when a check fails - and only then."""
    normal = plain(runner.invoke(cli, ["info", "--check"]).output)
    verbose = plain(runner.invoke(cli, ["--verbose", "info", "--check"]).output)

    assert len(verbose.splitlines()) > len(normal.splitlines())
    assert "checking system" in verbose or "parsing prms" in verbose
    assert "parsing prms" not in normal


@pytest.mark.essential
def test_a_failing_check_exits_non_zero(one_failing_check):
    """`cellpy info --check` is worth scripting, so it has to fail loudly."""
    result = runner.invoke(cli, ["info", "--check"])

    assert result.exit_code == 1
    assert "cannot import cellpy" in plain(result.output)
    assert "reinstall cellpy" in plain(result.output)


@pytest.mark.essential
def test_a_passing_check_exits_zero(every_check_passes):
    result = runner.invoke(cli, ["info", "--check"])

    assert result.exit_code == 0, plain(result.output)
    assert "3 of 3 checks passed" in plain(result.output)


@pytest.mark.essential
def test_soft_arbin_miss_exits_zero(soft_arbin_fail):
    """Missing optional Arbin .res tooling must not red-fail CI (#1111)."""
    result = runner.invoke(cli, ["info", "--check"])
    output = plain(result.output)

    assert result.exit_code == 0, output
    assert "no odbc driver for .res files" in output
    assert "2 of 3 checks passed" in output


@pytest.mark.essential
def test_failures_reach_stderr(one_failing_check):
    """A broken setup must survive `cellpy info --check > report.txt`."""
    result = runner.invoke(cli, ["info", "--check"])

    assert "cannot import cellpy" in plain(result.stderr)


@pytest.mark.essential
def test_quiet_reports_only_what_is_broken(one_failing_check):
    """--quiet drops the passing rows and keeps the problem."""
    result = runner.invoke(cli, ["--quiet", "info", "--check"])
    output = plain(result.output)

    assert "cannot import cellpy" in output
    assert "checks passed" not in output
    # Soft/ok rows are suppressed; the failing required label still shows.
    assert "arbin .res support" not in output


# -- the check helpers ------------------------------------------------------


@pytest.mark.essential
def test_a_check_that_raises_is_reported_not_propagated(monkeypatch):
    def boom():
        raise RuntimeError("probe exploded")

    monkeypatch.setattr(cli_api, "_check_import_cellpy", boom)
    result = runner.invoke(cli, ["info", "--check"])

    assert result.exit_code == 1
    assert "probe exploded" in plain(result.output)


@pytest.mark.essential
def test_a_local_path_in_a_remote_capable_setting_is_still_checked(monkeypatch):
    """`cellpydatadir` may be remote, so it used to be waved through entirely.

    A local path in one of those settings is checkable, and a wrong one should
    be reported rather than excused as "external".
    """
    from cellpy import config as cellpy_config

    real = cellpy_config.get_config()
    broken = real.paths.model_dump()
    broken["cellpydatadir"] = "/definitely/not/a/directory"

    # Delegate everything except the one dump we want to poison, so the rest of
    # the config (env_file, ...) keeps working.
    class _Paths:
        def __getattr__(self, name):
            return getattr(real.paths, name)

        def model_dump(self):
            return broken

    class _Config:
        paths = _Paths()

        def __getattr__(self, name):
            return getattr(real, name)

    monkeypatch.setattr(cellpy_config, "get_config", lambda: _Config())

    outcome = cli_api._check_config_file()
    assert outcome.ok is False
    assert "missing or unusable" in outcome.detail
