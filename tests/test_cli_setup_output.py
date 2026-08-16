"""What ``cellpy setup`` says, and to whom (#891, PR 4/5).

The old ``setup`` narrated its own internals: a parameter dump of
``init_filename`` / ``dst_file`` / ``not_relative``, the same dry-run fact in
two formats, and ``--silent`` that silenced the questions but not the ~25 lines
of output.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cellpy import cli, cli_api, cli_ui, config, prmreader


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """A throwaway user directory, so setup never touches the real one."""
    monkeypatch.setattr(prmreader, "get_user_dir", lambda: tmp_path)
    monkeypatch.setattr(config.paths, "env_file", tmp_path / ".env_cellpy")
    return tmp_path


@pytest.mark.essential
def test_setup_does_not_dump_its_own_parameters(isolated_home):
    result = CliRunner().invoke(
        cli.cli, ["setup", "--dry-run", "--silent", "--test_user", "quiet_user"]
    )
    assert result.exit_code == 0
    for leak in ("init_filename", "dst_file", "not_relative", "Got the following"):
        assert leak not in result.output


@pytest.mark.essential
def test_setup_silent_is_actually_silent(isolated_home):
    """``--silent`` used to stop the questions but keep every line (#891)."""
    result = CliRunner().invoke(
        cli.cli, ["setup", "--dry-run", "--silent", "--test_user", "quiet_user"]
    )
    assert result.exit_code == 0
    assert result.output.strip() == ""


@pytest.mark.essential
def test_setup_verbose_keeps_the_developer_detail(isolated_home):
    """The parameter dump is not deleted, it is demoted to --verbose."""
    result = CliRunner().invoke(
        cli.cli,
        ["--verbose", "setup", "--dry-run", "--test_user", "loud_user"],
    )
    assert result.exit_code == 0
    assert "init_filename" in result.output
    assert "dst_file" in result.output


@pytest.mark.essential
def test_setup_states_a_dry_run_fact_once(isolated_home):
    """It used to say "skipping actual saving of X" *and* "would write X"."""
    result = CliRunner().invoke(
        cli.cli, ["setup", "--dry-run", "--test_user", "dry_user"]
    )
    assert result.exit_code == 0
    assert "skipping actual saving" not in result.output
    # one line per file it would write: the conf, the toml and the env file
    assert result.output.count("dry-run: would write") == 3


@pytest.mark.essential
def test_a_per_command_silent_reaches_the_structured_output():
    """``_ui()`` must follow the echo's reporter, not the global one (#891)."""
    quiet = cli_ui.Reporter(level=cli_ui.Level.QUIET)
    with cli_ui.using_reporter(cli_ui.Reporter(level=cli_ui.Level.NORMAL)):
        with cli_api._using_echo(quiet.as_echo()):
            assert cli_api._ui() is quiet


@pytest.mark.essential
def test_a_library_call_without_an_echo_stays_silent():
    assert not cli_api._ui().enabled


@pytest.mark.essential
def test_edit_reports_an_unknown_file_on_stderr(capsys):
    cli_api.edit_file("nonsense", echo=print)
    captured = capsys.readouterr()
    assert "unknown file" in captured.err
    assert captured.out == ""


@pytest.mark.essential
@pytest.mark.parametrize(
    "argv", [["pull"], ["edit", "nonsense"]], ids=["pull", "edit"]
)
def test_a_usage_error_exits_two(argv):
    """These printed a complaint and exited 0, so a script saw success (#891)."""
    result = CliRunner().invoke(cli.cli, argv)
    assert result.exit_code == 2
