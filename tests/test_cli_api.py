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
    """The CLI passes typer.echo, so terminal output is unchanged."""
    from typer.testing import CliRunner

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


@pytest.fixture
def fake_cellpy_file(monkeypatch):
    """Stub the file layer and record which writer was asked for."""
    captured = {}

    def fake_load(path, accept_old=False):
        class Result:
            file_version = 5
            data = object()

        captured["loaded"] = path
        return Result()

    def fake_save_v8(data, path):
        captured["saved"] = path
        captured["writer"] = "v8"

    def fake_save_v9(data, path, **kwargs):
        captured["saved"] = path
        captured["writer"] = "v9"

    import cellpy.readers.cellpy_file as cellpy_file
    from cellpy.readers.cellpy_file import v9 as cellpy_file_v9

    monkeypatch.setattr(cellpy_file, "load", fake_load)
    monkeypatch.setattr(cellpy_file, "save", fake_save_v8)
    monkeypatch.setattr(cellpy_file_v9, "save", fake_save_v9)
    return captured


@pytest.mark.essential
def test_convert_defaults_the_destination_beside_the_source(
    tmp_path, fake_cellpy_file
):
    """Names the output after the target format, beside the source."""
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    written = cli_api.convert(source)
    assert written.name == "old_cell_v9.cellpy"
    assert fake_cellpy_file["saved"] == written


@pytest.mark.essential
def test_convert_defaults_to_v9(tmp_path, fake_cellpy_file):
    """v9 is what CellpyCell.save writes, so it is what convert produces."""
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    cli_api.convert(source)
    assert fake_cellpy_file["writer"] == "v9"


@pytest.mark.essential
def test_convert_can_still_target_v8(tmp_path, fake_cellpy_file):
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    written = cli_api.convert(source, to="v8")
    assert fake_cellpy_file["writer"] == "v8"
    assert written.name == "old_cell_v8.h5"


@pytest.mark.essential
def test_convert_rejects_an_unknown_target(tmp_path, fake_cellpy_file):
    """Better than quietly writing the default format the user did not ask for."""
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    with pytest.raises(ValueError, match="unknown conversion target"):
        cli_api.convert(source, to="v10")
    assert "writer" not in fake_cellpy_file


@pytest.mark.essential
def test_convert_honours_an_explicit_destination(tmp_path, fake_cellpy_file):
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")
    target = tmp_path / "somewhere_else.cellpy"

    written = cli_api.convert(source, target)
    assert written == target


@pytest.mark.essential
@pytest.mark.parametrize(
    "destination, expected_writer",
    [
        ("out.h5", "v8"),
        ("out.hdf5", "v8"),
        ("out.cellpy", "v9"),
        ("out.zip", "v9"),
    ],
)
def test_convert_infers_the_format_from_the_destination_suffix(
    tmp_path, fake_cellpy_file, destination, expected_writer
):
    """`convert old.h5 new.h5` must not put a v9 zip inside a .h5 file.

    Same rule CellpyCell.save already uses, so the two agree.
    """
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    cli_api.convert(source, tmp_path / destination)
    assert fake_cellpy_file["writer"] == expected_writer


@pytest.mark.essential
def test_an_explicit_target_beats_the_suffix(tmp_path, fake_cellpy_file):
    source = tmp_path / "old_cell.h5"
    source.write_bytes(b"")

    cli_api.convert(source, tmp_path / "out.h5", to="v9")
    assert fake_cellpy_file["writer"] == "v9"


@pytest.mark.essential
@pytest.mark.parametrize("target", ["v9", "v8"])
def test_convert_really_upgrades_a_legacy_file(tmp_path, target):
    """The tests above stub the file layer; this one does not.

    A legacy v5 cellpy-file goes in, and the result has to load again with the
    cycles and rows intact — which is the only thing a user of `cellpy convert`
    actually cares about.
    """
    import pathlib
    import shutil

    from cellpy import cellreader
    from tests import fdv

    legacy = pathlib.Path(fdv.cellpy_file_path_v5)
    if not legacy.is_file():
        pytest.skip(f"missing legacy fixture {legacy}")

    work = tmp_path / legacy.name
    shutil.copy(legacy, work)

    written = cli_api.convert(work, to=target)
    assert written.is_file()
    assert written.suffix == (".cellpy" if target == "v9" else ".h5")

    reloaded = cellreader.CellpyCell().load(written)
    assert len(reloaded.get_cycle_numbers()) > 0
    assert len(reloaded.data.raw) > 0
