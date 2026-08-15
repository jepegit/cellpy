"""Global flags, streams and exit codes (#891).

These drive the CLI the way a user or a script does — through the app — rather
than calling ``cli_api`` directly, because what is under test is the wiring:
which reporter a flag installs, which stream a message lands on, and what the
process exits with.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cellpy import cli_ui
from cellpy.cli import cli
from cellpy.cli_ui import Level

runner = CliRunner()


@pytest.fixture(autouse=True)
def fresh_reporter():
    """Each test starts without a reporter installed by an earlier one."""
    with cli_ui.using_reporter(None):
        yield


# -- global flags map to levels --------------------------------------------


@pytest.mark.parametrize(
    "argv, expected",
    [
        ([], Level.NORMAL),
        (["--quiet"], Level.QUIET),
        (["-q"], Level.QUIET),
        (["--verbose"], Level.VERBOSE),
        # Asking for silence and noise at once resolves to silence.
        (["--quiet", "--verbose"], Level.QUIET),
    ],
)
@pytest.mark.essential
def test_global_flags_install_the_matching_level(argv, expected):
    result = runner.invoke(cli, argv + ["info", "--version"])

    assert result.exit_code == 0, result.output
    assert cli_ui.current().level is expected


@pytest.mark.essential
def test_no_color_disables_colour():
    result = runner.invoke(cli, ["--no-color", "info", "--version"])

    assert result.exit_code == 0, result.output
    assert "\x1b[" not in result.output


@pytest.mark.essential
def test_quiet_still_answers_a_question():
    """`info` is payload: --quiet silences progress, never the answer."""
    result = runner.invoke(cli, ["--quiet", "info", "--version"])

    assert result.exit_code == 0, result.output
    assert "version" in result.output


# -- usage errors ----------------------------------------------------------


@pytest.mark.essential
def test_run_without_a_name_is_a_usage_error():
    """Was hand-rolled usage text on stdout with exit -1 (255)."""
    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 2
    assert "--list" in result.output


@pytest.mark.essential
def test_run_without_a_mode_is_a_usage_error():
    """Was a flag dump plus an apology, and a success exit code."""
    result = runner.invoke(cli, ["run", "some_batch"])

    assert result.exit_code == 2
    assert "--journal" in result.output


@pytest.mark.essential
def test_run_list_still_works_without_a_name(tmp_path, monkeypatch):
    """NAME stays optional: making it required would break `run --list`."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, ["run", "--list"])

    assert result.exit_code == 0, result.output


@pytest.mark.essential
def test_usage_errors_go_to_stderr():
    """A script doing `cellpy run > out` must still see the error."""
    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 2
    assert result.stdout.strip() == ""
    assert "--list" in result.stderr
