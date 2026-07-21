"""Auto delimiter detection has to cope with short files.

``find_delimiter_and_start`` samples a window of lines and splits it into a
possible-header part and a data part. The old arithmetic tied the split point
to the *nominal* window size (``checking_length_whole - checking_length_header``)
rather than the number of lines actually read, so any file shorter than that
window left the data slice empty and detection died with a bare
``IndexError: list index out of range`` - naming neither the file nor the
cause.

A short vendor file is normal: a truncated run, a quick sanity export, a small
test fixture. These tests pin that a header line plus a single data row is
enough to detect the delimiter, and that a file where detection genuinely
cannot succeed raises a typed :class:`~cellpy.exceptions.LoaderError` that names
the file. Regression for the synthetic-parity fixtures that had to be 300 rows
to dodge the bug (#560 / PR #602).
"""

from __future__ import annotations

import pytest

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.base import find_delimiter_and_start

# the parameters the AutoLoader (base.py / custom.py) actually calls with; this
# pairing (header 100, whole 200) is where the reported failure lived.
AUTO_HEADER, AUTO_WHOLE = 100, 200


def _write_delimited(path, n_rows, sep=";", n_cols=6, preamble=0):
    """A header row plus ``n_rows`` data rows, optionally behind a preamble."""
    lines = [f"# preamble line {k}" for k in range(preamble)]
    lines.append(sep.join(f"col{c}" for c in range(n_cols)))
    for r in range(n_rows):
        lines.append(sep.join(str(r * n_cols + c) for c in range(n_cols)))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# 1 is the floor the fix promises (header + one data row); 100/150 straddle the
# old header=100 threshold that failed at 101 total lines.
@pytest.mark.parametrize("n_rows", [1, 2, 5, 20, 100, 101, 150])
@pytest.mark.parametrize("sep", [";", "\t", ",", "|"])
def test_short_files_detect_the_delimiter(tmp_path, n_rows, sep):
    source = _write_delimited(tmp_path / "short.csv", n_rows, sep=sep)

    separator, first_index, _ = find_delimiter_and_start(
        source,
        checking_length_header=AUTO_HEADER,
        checking_length_whole=AUTO_WHOLE,
        check_encoding=False,
    )

    assert separator == sep
    # the header row carries the same delimiter count as the data rows here, so
    # it is the first matching line.
    assert first_index == 0


@pytest.mark.parametrize("n_rows", [1, 2, 5, 20])
def test_short_files_with_a_preamble_locate_the_header(tmp_path, n_rows):
    source = _write_delimited(tmp_path / "preamble.csv", n_rows, preamble=3)

    separator, first_index, _ = find_delimiter_and_start(
        source,
        checking_length_header=AUTO_HEADER,
        checking_length_whole=AUTO_WHOLE,
        check_encoding=False,
    )

    assert separator == ";"
    # the three preamble lines carry no delimiters, so the header row - the
    # first line whose count matches the data - sits at index 3.
    assert first_index == 3


def test_single_header_and_data_line_is_enough(tmp_path):
    """The floor the fix promises: one header line, one data line."""
    source = tmp_path / "minimal.csv"
    source.write_text("a;b;c\n1;2;3\n", encoding="utf-8")

    separator, first_index, _ = find_delimiter_and_start(
        source, checking_length_header=AUTO_HEADER, check_encoding=False
    )

    assert separator == ";"
    assert first_index == 0


def test_empty_file_raises_typed_error_naming_the_file(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")

    with pytest.raises(LoaderError) as excinfo:
        find_delimiter_and_start(source, check_encoding=False)

    assert str(source) in str(excinfo.value)


def test_file_without_a_delimiter_raises_typed_error_naming_the_file(tmp_path):
    source = tmp_path / "single_column.csv"
    source.write_text("voltage\n3.1\n3.2\n3.3\n", encoding="utf-8")

    with pytest.raises(LoaderError) as excinfo:
        find_delimiter_and_start(source, check_encoding=False)

    assert str(source) in str(excinfo.value)
