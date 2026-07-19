"""The library-first CLI API (#568, CLI plan Phase 0-1).

The point of the extraction is that a script can do what the command line does
without shelling out and scraping stdout. So these tests call the functions
directly and assert on **return values**, not on printed text.
"""

from __future__ import annotations

import logging

import pytest

from cellpy import cli_api, log

log.setup_logging(default_level=logging.DEBUG, testing=True)


# -- the API is usable without Click ---------------------------------------------


@pytest.mark.essential
def test_every_extracted_command_is_importable():
    """Reachable from Python, which was the whole point."""
    for name in (
        "convert",
        "run_journal",
        "run_journals",
        "run_from_db",
        "run_project",
        "list_journals",
        "open_db_editor",
    ):
        assert callable(getattr(cli_api, name)), name


@pytest.mark.essential
def test_calling_the_api_does_not_require_a_click_context():
    """A Click command function would raise outside a CLI invocation."""
    result = cli_api.list_journals("definitely_not_a_directory")
    assert result == []


# -- quiet by default ------------------------------------------------------------


@pytest.mark.essential
def test_the_api_is_quiet_by_default(capsys):
    """A library that prints uninvited is a nuisance in a notebook."""
    cli_api.list_journals("definitely_not_a_directory")
    captured = capsys.readouterr()
    assert "not found" not in captured.out


@pytest.mark.essential
def test_echo_makes_it_speak(capsys):
    cli_api.list_journals("definitely_not_a_directory", echo=print)
    captured = capsys.readouterr()
    assert "not found" in captured.out


@pytest.mark.essential
def test_the_cli_still_speaks(tmp_path):
    """The CLI passes click.echo, so terminal output is unchanged."""
    from click.testing import CliRunner

    from cellpy.cli import cli

    result = CliRunner().invoke(cli, ["run", "--list", str(tmp_path)])
    assert result.exit_code == 0
    assert "Content of" in result.output or "No batch-files" in result.output


# -- list_journals ----------------------------------------------------------------


@pytest.mark.essential
def test_list_journals_returns_the_paths(tmp_path):
    """Return the result instead of making callers scrape the output."""
    (tmp_path / "cellpy_batch_one.json").write_text("{}", encoding="utf-8")
    (tmp_path / "cellpy_batch_two.json").write_text("{}", encoding="utf-8")
    (tmp_path / "not_a_journal.txt").write_text("", encoding="utf-8")

    found = cli_api.list_journals(tmp_path)
    assert [path.name for path in found] == [
        "cellpy_batch_one.json",
        "cellpy_batch_two.json",
    ]


@pytest.mark.essential
def test_list_journals_counts_correctly(tmp_path, capsys):
    """The one deliberate behaviour change in the extraction.

    The original counted with a leftover `enumerate` index, so it reported one
    fewer file than it listed.
    """
    for name in ("cellpy_a.json", "cellpy_b.json", "cellpy_c.json"):
        (tmp_path / name).write_text("{}", encoding="utf-8")

    cli_api.list_journals(tmp_path)
    assert "number of batch-files located: 3" in capsys.readouterr().out


@pytest.mark.essential
def test_a_single_journal_is_not_reported_as_none(tmp_path, capsys):
    """The uglier half of the same bug: one file printed "No batch-files found"
    directly beneath the file it had just listed (0 is falsy)."""
    (tmp_path / "cellpy_only.json").write_text("{}", encoding="utf-8")

    found = cli_api.list_journals(tmp_path)
    output = capsys.readouterr().out
    assert len(found) == 1
    assert "No batch-files found" not in output
    assert "number of batch-files located: 1" in output


@pytest.mark.essential
def test_missing_directory_is_reported_not_raised(tmp_path):
    assert cli_api.list_journals(tmp_path / "nope") == []


# -- run_journal ------------------------------------------------------------------


@pytest.mark.essential
def test_run_journal_returns_none_for_a_missing_journal(tmp_path):
    """Missing input is an ordinary answer, not an exception."""
    assert cli_api.run_journal(tmp_path / "no_such_journal.json") is None


# -- convert ------------------------------------------------------------------------


@pytest.mark.essential
def test_convert_defaults_the_destination_beside_the_source(tmp_path, monkeypatch):
    """The naming rule the CLI has always used, now assertable directly."""
    captured = {}

    def fake_load(path, accept_old=False):
        class Result:
            file_version = 5
            data = object()

        captured["loaded"] = path
        return Result()

    def fake_save(data, path):
        captured["saved"] = path

    import cellpy.readers.cellpy_file as cellpy_file

    monkeypatch.setattr(cellpy_file, "load", fake_load)
    monkeypatch.setattr(cellpy_file, "save", fake_save)

    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    written = cli_api.convert(source)
    assert written.name == "old_cell_v8.h5"
    assert captured["saved"] == written
