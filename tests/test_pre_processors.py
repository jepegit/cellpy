"""Loader pre-processors (#560).

``remove_empty_lines`` used to open its input with the *platform default*
encoding. That made a real Maccor file (``maccor_002.txt``, whose Description
line carries a 0xFF byte) load on Windows and raise a bare
``UnicodeDecodeError`` on Linux — a class of bug that is invisible to anyone
developing on one platform, and that no test caught because nothing loaded that
file.
"""

from __future__ import annotations

import pytest

from cellpy.readers.instruments.processors.pre_processors import remove_empty_lines


@pytest.mark.essential
def test_a_non_utf8_byte_does_not_stop_the_file_from_loading(tmp_path):
    """The regression: 0xFF is not valid UTF-8 and must not be fatal.

    This pre-processor only strips blank lines. It has no business rejecting a
    file over one undecodable byte in a header comment.
    """
    source = tmp_path / "vendor.txt"
    source.write_bytes(b"Name:\tcell-1\r\nDescription\ttest \xff\xff\r\n\r\ndata\t1\r\n")

    out = remove_empty_lines(source)

    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, f"expected the blank line dropped, got {lines}"
    assert lines[0] == "Name:\tcell-1"
    assert lines[2] == "data\t1"


@pytest.mark.essential
def test_blank_lines_are_removed_and_content_preserved(tmp_path):
    source = tmp_path / "vendor.txt"
    source.write_text("a\n\n\nb\n   \nc\n", encoding="utf-8")

    out = remove_empty_lines(source)

    assert out.read_text(encoding="utf-8").splitlines() == ["a", "b", "c"]


@pytest.mark.essential
def test_the_source_file_is_not_modified(tmp_path):
    """It writes a new file; the vendor's own file must survive untouched."""
    source = tmp_path / "vendor.txt"
    original = b"a\r\n\r\nb\r\n"
    source.write_bytes(original)

    remove_empty_lines(source)

    assert source.read_bytes() == original


@pytest.mark.essential
def test_a_missing_file_is_reported_clearly(tmp_path):
    with pytest.raises(IOError, match="Could not find the file"):
        remove_empty_lines(tmp_path / "nope.txt")
