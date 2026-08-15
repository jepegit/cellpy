"""Global flags, streams and exit codes (#891).

These drive the CLI the way a user or a script does — through the app — rather
than calling ``cli_api`` directly, because what is under test is the wiring:
which reporter a flag installs, which stream a message lands on, and what the
process exits with.
"""

from __future__ import annotations

import re

import pytest
from typer.testing import CliRunner

from cellpy import cli_ui
from cellpy.cli import cli
from cellpy.cli_ui import Level

runner = CliRunner()

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


# SGR parameters that set a colour: 30-49 (basic + extended selectors) and
# 90-107 (bright). Bold (1) and dim (2) are styling, not colour.
_COLOUR_PARAMS = set(range(30, 50)) | set(range(90, 108))


def plain(text: str) -> str:
    """What a human reads: the text with styling removed.

    Typer renders usage errors through rich, which highlights option tokens -
    ``--list`` reaches the terminal as ``-`` + escapes + ``-list``, so asserting
    on the raw capture passes only where rich happens not to colour (a legacy
    Windows console) and fails in CI.
    """
    return _ANSI.sub("", text)


def has_colour(text: str) -> bool:
    """True if anything is actually coloured.

    ``NO_COLOR`` makes rich drop colour while keeping bold and dim, so "no
    escape codes at all" would be the wrong bar for ``--no-color``.
    """
    for match in _ANSI.finditer(text):
        params = [int(p) for p in match.group()[2:-1].split(";") if p.isdigit()]
        if any(param in _COLOUR_PARAMS for param in params):
            return True
    return False


@pytest.fixture(autouse=True)
def fresh_reporter(monkeypatch):
    """Start each test without a reporter or colour decision left by another."""
    monkeypatch.delenv("NO_COLOR", raising=False)
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
    import cellpy

    result = runner.invoke(cli, ["--quiet", "info", "--version"])

    assert result.exit_code == 0, result.output
    assert cellpy.__version__ in plain(result.output)


# -- usage errors ----------------------------------------------------------


@pytest.mark.essential
def test_run_without_a_name_is_a_usage_error():
    """Was hand-rolled usage text on stdout with exit -1 (255)."""
    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 2
    assert "--list" in plain(result.output)


@pytest.mark.essential
def test_run_without_a_mode_is_a_usage_error():
    """Was a flag dump plus an apology, and a success exit code."""
    result = runner.invoke(cli, ["run", "some_batch"])

    assert result.exit_code == 2
    assert "--journal" in plain(result.output)


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
    assert "--list" in plain(result.stderr)


@pytest.mark.essential
def test_no_color_reaches_typers_own_error_rendering():
    """--no-color must cover the usage errors typer renders itself."""
    result = runner.invoke(cli, ["--no-color", "run"])

    assert result.exit_code == 2
    assert not has_colour(result.stderr)
    assert "--list" in plain(result.stderr)
