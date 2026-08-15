"""The CLI's output vocabulary (#891).

``cli_ui`` decides three things a user notices immediately: whether output is
coloured, which symbols it can print, and how much of it appears. Each of those
is a decision about *someone else's* terminal, so they are tested against
injected streams rather than the one running pytest.
"""

from __future__ import annotations

import io

import pytest

from cellpy.cli_ui import (
    ASCII_SYMBOLS,
    UNICODE_SYMBOLS,
    Level,
    Reporter,
    color_enabled,
    make_reporter,
    supports_unicode,
)


class _Stream(io.StringIO):
    """A StringIO that answers the questions rich asks of a real stream."""

    def __init__(self, encoding: str = "utf-8", tty: bool = False):
        super().__init__()
        self._encoding = encoding
        self._tty = tty

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return self._encoding

    def isatty(self) -> bool:
        return self._tty


@pytest.fixture
def plain_env(monkeypatch):
    """Neutralise the ambient terminal environment for colour decisions."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)


@pytest.fixture
def streams():
    return _Stream(), _Stream()


def _reporter(streams, **kwargs) -> Reporter:
    out, err = streams
    return Reporter(stdout=out, stderr=err, **kwargs)


# -- symbols ----------------------------------------------------------------


@pytest.mark.essential
def test_unicode_symbols_when_the_stream_can_encode_them(plain_env, streams):
    assert _reporter(streams).symbols is UNICODE_SYMBOLS


@pytest.mark.essential
def test_ascii_symbols_on_a_legacy_code_page(plain_env):
    """A cp1252 console cannot print ✓ - fall back instead of crashing."""
    out, err = _Stream(encoding="cp1252"), _Stream()
    reporter = Reporter(stdout=out, stderr=err)

    assert reporter.symbols is ASCII_SYMBOLS
    reporter.ok("imports", "cellpy")
    printed = out.getvalue()
    assert ASCII_SYMBOLS.ok in printed
    assert UNICODE_SYMBOLS.ok not in printed


@pytest.mark.essential
def test_supports_unicode_is_false_without_an_encoding():
    assert supports_unicode(io.StringIO()) is False


# -- colour -----------------------------------------------------------------


@pytest.mark.essential
def test_no_colour_when_the_stream_is_not_a_terminal(plain_env, streams):
    reporter = _reporter(streams)
    reporter.ok("imports", "cellpy")

    assert "\x1b[" not in streams[0].getvalue()


@pytest.mark.essential
def test_no_color_environment_variable_wins(plain_env, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "")  # presence is the signal, not the value
    assert color_enabled(_Stream(tty=True)) is False


@pytest.mark.essential
def test_dumb_terminal_gets_no_colour(plain_env, monkeypatch):
    monkeypatch.setenv("TERM", "dumb")
    assert color_enabled(_Stream(tty=True)) is False


@pytest.mark.essential
def test_a_terminal_gets_colour(plain_env):
    assert color_enabled(_Stream(tty=True)) is True


@pytest.mark.essential
def test_explicit_color_flag_overrides_detection(plain_env, streams):
    reporter = _reporter(streams, color=True)
    reporter.ok("imports", "cellpy")

    assert "\x1b[" in streams[0].getvalue()


# -- streams ----------------------------------------------------------------


@pytest.mark.essential
def test_failures_go_to_stderr_and_successes_to_stdout(plain_env, streams):
    out, err = streams
    reporter = _reporter(streams)

    reporter.ok("imports", "cellpy")
    reporter.fail("configuration", "no cellpy.toml found", hint="run  cellpy setup")

    assert "imports" in out.getvalue()
    assert "configuration" not in out.getvalue()
    assert "configuration" in err.getvalue()
    assert "hint: run  cellpy setup" in err.getvalue()


# -- levels -----------------------------------------------------------------


@pytest.mark.essential
def test_quiet_keeps_problems_and_drops_progress(plain_env, streams):
    out, err = streams
    reporter = _reporter(streams, level=Level.QUIET)

    reporter.title("checking your setup")
    reporter.step("writing cellpy.toml")
    reporter.ok("imports", "cellpy")
    reporter.detail("rawdatadir", "/data/raw")
    reporter.summary(3, 3)
    reporter.warn("legacy .conf found")
    reporter.fail("configuration", "missing")

    printed = out.getvalue()
    for silenced in (
        "checking your setup",
        "writing cellpy.toml",
        "imports",
        "rawdatadir",
        "checks passed",
    ):
        assert silenced not in printed, silenced
    # Problems are not progress: both survive --quiet, on their own streams.
    assert "legacy .conf found" in printed
    assert "configuration" in err.getvalue()


@pytest.mark.essential
def test_quiet_still_prints_requested_payload(plain_env, streams):
    """`cellpy info --version` under --quiet must still answer."""
    reporter = _reporter(streams, level=Level.QUIET)
    reporter.payload("2.1.2")

    assert "2.1.2" in streams[0].getvalue()


@pytest.mark.essential
def test_debug_only_appears_under_verbose(plain_env, streams):
    out, _ = streams
    _reporter(streams).debug("dst_file=/tmp/x")
    assert out.getvalue().strip() == ""

    verbose_out = _Stream()
    Reporter(stdout=verbose_out, stderr=_Stream(), level=Level.VERBOSE).debug(
        "dst_file=/tmp/x"
    )
    assert "dst_file=/tmp/x" in verbose_out.getvalue()


@pytest.mark.essential
def test_make_reporter_prefers_quiet_over_verbose():
    assert make_reporter(quiet=True, verbose=True).level is Level.QUIET
    assert make_reporter(verbose=True).level is Level.VERBOSE
    assert make_reporter().level is Level.NORMAL


# -- rendering --------------------------------------------------------------


@pytest.mark.essential
def test_user_data_is_never_parsed_as_markup(plain_env, streams):
    """A path with brackets is data. rich must print it, not interpret it."""
    out, _ = streams
    reporter = _reporter(streams)

    reporter.ok("cellpydatadir", r"C:\data\[bold]run[/bold]")

    printed = out.getvalue()
    assert "[bold]run[/bold]" in printed


@pytest.mark.essential
def test_rules_follow_the_terminal_width(plain_env, streams):
    out, _ = streams
    reporter = _reporter(streams)

    reporter.rule()

    line = out.getvalue().strip("\n")
    assert len(line) == reporter.width
    assert line != "-" * 80 or reporter.width == 80


@pytest.mark.essential
def test_summary_reports_the_score(plain_env, streams):
    out, _ = streams
    _reporter(streams).summary(2, 3)

    assert "2 of 3 checks passed" in out.getvalue()


@pytest.mark.essential
def test_detail_lines_align_under_their_parent(plain_env, streams):
    out, _ = streams
    reporter = _reporter(streams)

    reporter.ok("configuration", "cellpy.toml")
    reporter.detail("rawdatadir", "/data/raw", note="remote, not checked")

    lines = out.getvalue().splitlines()
    assert lines[0].startswith("  ")
    assert lines[1].startswith("      ")
    assert "(remote, not checked)" in lines[1]


# -- compatibility ----------------------------------------------------------


@pytest.mark.essential
def test_as_echo_prints_preformatted_messages(plain_env, streams):
    out, _ = streams
    echo = _reporter(streams).as_echo()

    echo("[cellpy] (setup) not converted yet")

    assert "[cellpy] (setup) not converted yet" in out.getvalue()


@pytest.mark.essential
def test_as_echo_is_silent_when_quiet(plain_env, streams):
    out, _ = streams
    _reporter(streams, level=Level.QUIET).as_echo()("noise")

    assert out.getvalue().strip() == ""
