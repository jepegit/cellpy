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
    """Make the odbc check fail, without needing a machine that lacks it."""
    monkeypatch.setattr(
        cli_api,
        "_check_import_pyodbc",
        lambda: cli_api._CheckOutcome(
            False, "no odbc driver", hint="install mdbtools"
        ),
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
    assert "no odbc driver" in plain(result.output)
    assert "install mdbtools" in plain(result.output)


@pytest.mark.essential
def test_a_passing_check_exits_zero(every_check_passes):
    result = runner.invoke(cli, ["info", "--check"])

    assert result.exit_code == 0, plain(result.output)
    assert "3 of 3 checks passed" in plain(result.output)


@pytest.mark.essential
def test_failures_reach_stderr(one_failing_check):
    """A broken setup must survive `cellpy info --check > report.txt`."""
    result = runner.invoke(cli, ["info", "--check"])

    assert "no odbc driver" in plain(result.stderr)


@pytest.mark.essential
def test_quiet_reports_only_what_is_broken(one_failing_check):
    """--quiet drops the passing rows and keeps the problem."""
    result = runner.invoke(cli, ["--quiet", "info", "--check"])
    output = plain(result.output)

    assert "no odbc driver" in output
    assert "checks passed" not in output
    assert "imports" not in output


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
