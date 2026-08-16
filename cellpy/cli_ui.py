"""Console reporting for the cellpy CLI (#891).

One small vocabulary for everything the CLI says, so output stops being a mix
of ``[cellpy] (setup)`` prefixes, hand-drawn 80-column rules and bare
``print()`` calls:

    >>> ui = Reporter()
    >>> ui.title("cellpy 2.1.2 - checking your setup")
    >>> ui.ok("odbc driver", "Microsoft Access Driver")
    >>> ui.fail("configuration", "no cellpy.toml found")
    >>> ui.hint("run  cellpy setup")
    >>> ui.summary(2, 3)

Rules of the house:

* **Failures go to stderr**, everything else to stdout, so ``cellpy ... > out``
  keeps the errors on the terminal.
* **Colour is automatic**: off when the stream is not a terminal, when
  ``NO_COLOR`` is set, when ``TERM=dumb``, or when the caller passes
  ``color=False``. Piped output stays plain and greppable.
* **Symbols degrade to ASCII** when the stream encoding cannot represent them
  (legacy Windows code pages), decided by probing the stream rather than
  guessing from the platform.
* **User data is never markup**: messages are rendered as ``rich`` ``Text``
  objects, so a Windows path full of ``[`` is printed, not parsed.

``rich`` is imported lazily so that merely importing this module stays cheap
(#837 keeps ``cellpy info --version`` off the heavy import path).
"""

from __future__ import annotations

import enum
import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional, TextIO

__all__ = [
    "ASCII_SYMBOLS",
    "Level",
    "Reporter",
    "Symbols",
    "UNICODE_SYMBOLS",
    "color_enabled",
    "current",
    "make_reporter",
    "set_reporter",
    "supports_unicode",
    "using_reporter",
]

# Layout constants. The label column is wide enough for the longest label the
# CLI uses today ("cellpydatadir", "odbc driver", ...) with room to spare; a
# longer label simply pushes its detail right instead of being truncated.
LABEL_WIDTH = 20
INDENT = "  "
DETAIL_INDENT = "      "
# ``INDENT + symbol + space`` is 4 columns; the detail indent is 6. Narrowing
# the key column by the difference lines both value columns up.
DETAIL_KEY_WIDTH = LABEL_WIDTH - (len(DETAIL_INDENT) - len(INDENT) - 2)

STYLE_OK = "green"
STYLE_WARN = "yellow"
STYLE_FAIL = "red"
STYLE_DIM = "dim"
STYLE_HINT = "cyan"
STYLE_TITLE = "bold"


class Level(enum.IntEnum):
    """How much the CLI says.

    ``QUIET`` still reports problems and still prints explicitly requested
    payload (``cellpy info --version``) - it silences progress, not answers.
    """

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2


@dataclass(frozen=True)
class Symbols:
    """The symbol column. Every symbol is one character wide, so rows align."""

    ok: str
    warn: str
    fail: str
    step: str
    rule: str


UNICODE_SYMBOLS = Symbols(ok="✓", warn="!", fail="✗", step="·", rule="─")
ASCII_SYMBOLS = Symbols(ok="+", warn="!", fail="x", step="-", rule="-")


def supports_unicode(stream: Any) -> bool:
    """True when ``stream`` can encode the unicode symbol set."""
    encoding = getattr(stream, "encoding", None)
    if not encoding:
        return False
    probe = "".join(
        (
            UNICODE_SYMBOLS.ok,
            UNICODE_SYMBOLS.fail,
            UNICODE_SYMBOLS.step,
            UNICODE_SYMBOLS.rule,
        )
    )
    try:
        probe.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def color_enabled(stream: Any, *, color: Optional[bool] = None) -> bool:
    """Decide colour for ``stream``; ``color`` (from ``--no-color``) wins."""
    if color is not None:
        return bool(color)
    # https://no-color.org - presence is the signal, whatever the value.
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    isatty = getattr(stream, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except ValueError:  # closed stream
        return False


class Reporter:
    """Renders the CLI's output vocabulary.

    Args:
        level: how much to say (see :class:`Level`).
        color: force colour on/off; ``None`` (default) decides per stream.
        stdout / stderr: streams to write to (defaults to the real ones);
            injectable so tests can capture without touching global state.
    """

    def __init__(
        self,
        *,
        level: Level = Level.NORMAL,
        color: Optional[bool] = None,
        stdout: Optional[TextIO] = None,
        stderr: Optional[TextIO] = None,
        enabled: bool = True,
    ) -> None:
        self.level = Level(level)
        self._color = color
        # A disabled reporter writes nowhere at any level - what a library call
        # gets when the caller did not ask for output (``cli_api`` is quiet by
        # default, and that includes failures).
        self.enabled = enabled
        # Streams stay unresolved when not injected: pytest's capsys, Click's
        # CliRunner and a plain shell redirect all swap sys.stdout *after* a
        # reporter may have been built, and a reporter that captured the old
        # object would write into the void.
        self._stdout = stdout
        self._stderr = stderr
        self._out_console: Any = None
        self._err_console: Any = None

    # -- plumbing ------------------------------------------------------

    def _stream(self, *, err: bool = False) -> Any:
        if err:
            return self._stderr if self._stderr is not None else sys.stderr
        return self._stdout if self._stdout is not None else sys.stdout

    @property
    def symbols(self) -> Symbols:
        """Unicode where the current stdout can encode it, else ASCII."""
        return (
            UNICODE_SYMBOLS
            if supports_unicode(self._stream())
            else ASCII_SYMBOLS
        )

    def _console(self, *, err: bool = False) -> Any:
        stream = self._stream(err=err)
        cached = self._err_console if err else self._out_console
        # Reuse only while it still points at the stream in force.
        if cached is not None and cached.file is stream:
            return cached
        from rich.console import Console

        enabled = color_enabled(stream, color=self._color)
        console = Console(
            file=stream,
            # force_terminal so colour survives a captured stream when the
            # caller explicitly asked for it; no_color strips it otherwise.
            force_terminal=True if enabled else False,
            no_color=not enabled,
            highlight=False,  # rich would colour numbers/paths on its own
            markup=False,
            emoji=False,
            soft_wrap=True,
        )
        if err:
            self._err_console = console
        else:
            self._out_console = console
        return console

    def _text(self) -> Any:
        from rich.text import Text

        return Text()

    def _visible(self, minimum: Level) -> bool:
        return self.level >= minimum

    def _write(self, text: Any, *, err: bool = False) -> None:
        if not self.enabled:
            return
        self._console(err=err).print(text)

    @property
    def is_verbose(self) -> bool:
        """For callers that want to emit extra detail under ``--verbose``."""
        return self.level >= Level.VERBOSE

    @property
    def width(self) -> int:
        return int(self._console().width)

    # -- vocabulary ----------------------------------------------------

    def title(self, message: str) -> None:
        """A heading for a command that is about to report several things."""
        if not self._visible(Level.NORMAL):
            return
        text = self._text()
        text.append(message, style=STYLE_TITLE)
        self._write(text)
        self.blank()

    def ok(self, label: str, detail: Optional[str] = None) -> None:
        """Something worked."""
        if not self._visible(Level.NORMAL):
            return
        self._write(self._row(self.symbols.ok, STYLE_OK, label, detail))

    def warn(
        self, label: str, detail: Optional[str] = None, *, hint: Optional[str] = None
    ) -> None:
        """Something is off but the command carries on. Survives ``--quiet``."""
        self._write(self._row(self.symbols.warn, STYLE_WARN, label, detail))
        if hint:
            self._hint_line(hint)

    def fail(
        self, label: str, detail: Optional[str] = None, *, hint: Optional[str] = None
    ) -> None:
        """Something failed. Goes to stderr and survives ``--quiet``."""
        self._write(self._row(self.symbols.fail, STYLE_FAIL, label, detail), err=True)
        if hint:
            self._hint_line(hint, err=True)

    def step(self, message: str) -> None:
        """One real action, as it happens ("writing cellpy.toml")."""
        if not self._visible(Level.NORMAL):
            return
        self._write(self._row(self.symbols.step, STYLE_DIM, message, None))

    def detail(self, key: str, value: str, *, note: Optional[str] = None) -> None:
        """An aligned key/value line under whatever was just reported."""
        if not self._visible(Level.NORMAL):
            return
        text = self._text()
        text.append(DETAIL_INDENT)
        # Narrower key column, so detail values land in the same column as the
        # detail of the ok/warn/fail row they sit under.
        text.append(_pad(key, DETAIL_KEY_WIDTH), style=STYLE_DIM)
        text.append(value)
        if note:
            text.append(f"  ({note})", style=STYLE_DIM)
        self._write(text)

    def hint(self, message: str) -> None:
        """What the user should do next."""
        if not self._visible(Level.NORMAL):
            return
        self._hint_line(message)

    def rule(self, title: Optional[str] = None) -> None:
        """A horizontal rule at terminal width - never a hard-coded 80."""
        if not self._visible(Level.NORMAL):
            return
        width = max(self.width, 10)
        char = self.symbols.rule
        if title:
            label = f" {title} "
            fill = max(width - len(label), 2)
            left = fill // 2
            line = char * left + label + char * (fill - left)
        else:
            line = char * width
        text = self._text()
        text.append(line, style=STYLE_DIM)
        self._write(text)

    def summary(self, passed: int, total: int, *, unit: str = "checks") -> None:
        """The one-line verdict that closes a multi-check command."""
        if not self._visible(Level.NORMAL):
            return
        self.blank()
        text = self._text()
        text.append(INDENT)
        style = STYLE_OK if passed == total else STYLE_FAIL
        text.append(f"{passed} of {total} {unit} passed", style=style)
        self._write(text)

    def blank(self) -> None:
        if not self._visible(Level.NORMAL):
            return
        self._write(self._text())

    def payload(self, message: str) -> None:
        """Output the user explicitly asked for (a version, a config dump).

        Printed verbatim at every level, including ``--quiet``: silencing
        progress must not silence the answer to the question.
        """
        text = self._text()
        text.append(message)
        self._write(text)

    def debug(self, message: str) -> None:
        """Internal detail; only under ``--verbose``."""
        if not self._visible(Level.VERBOSE):
            return
        text = self._text()
        text.append(DETAIL_INDENT)
        text.append(message, style=STYLE_DIM)
        self._write(text)

    def with_level(self, level: Level) -> "Reporter":
        """A copy that says more (or less), keeping colour and streams.

        Lets a per-command ``--silent`` / ``--debug`` adjust one invocation
        without mutating the reporter the rest of the process shares.
        """
        return Reporter(
            level=level,
            color=self._color,
            stdout=self._stdout,
            stderr=self._stderr,
            enabled=self.enabled,
        )

    # -- compatibility -------------------------------------------------

    def as_echo(self) -> Callable[[str], None]:
        """An ``Echo``-compatible callable for messages not yet converted.

        ``cli_api`` reports through ``_say`` / ``echo=``; binding this lets the
        conversion happen message by message instead of in one sweep. Text
        arrives pre-formatted, so it is printed as payload.
        """

        def echo(message: str = "") -> None:
            if not self._visible(Level.NORMAL):
                return
            self.payload(message)

        # Whoever holds the echo can find the reporter behind it, so a
        # per-command ``--silent`` / ``--debug`` reaches structured output
        # (``cli_api._ui()``) too and not only the ``_say`` lines (#891).
        echo.reporter = self
        return echo

    # -- internals -----------------------------------------------------

    def _row(
        self, symbol: str, style: str, label: str, detail: Optional[str]
    ) -> Any:
        text = self._text()
        text.append(INDENT)
        text.append(symbol, style=style)
        text.append(" ")
        text.append(_pad(label) if detail else label)
        if detail:
            text.append(detail, style=STYLE_DIM)
        return text

    def _hint_line(self, message: str, *, err: bool = False) -> None:
        text = self._text()
        text.append(DETAIL_INDENT)
        text.append("hint: ", style=STYLE_HINT)
        text.append(message)
        self._write(text, err=err)


def _pad(value: str, width: int = LABEL_WIDTH) -> str:
    """Left-align in a column, keeping at least two spaces after a long value."""
    return value.ljust(width) if len(value) < width else value + "  "


# The reporter the CLI is currently speaking through. A ContextVar rather than
# a plain global, matching ``cli_api._echo_var``, so concurrent work cannot
# steal each other's verbosity.
_reporter_var: ContextVar[Optional[Reporter]] = ContextVar(
    "cellpy_cli_reporter", default=None
)


def silent_reporter() -> Reporter:
    """A reporter that prints nothing, for library calls that asked for quiet."""
    return Reporter(enabled=False)


def current() -> Reporter:
    """The active reporter, defaulting to a plain one on first use."""
    reporter = _reporter_var.get()
    if reporter is None:
        reporter = Reporter()
        _reporter_var.set(reporter)
    return reporter


def set_reporter(reporter: Optional[Reporter]) -> Optional[Reporter]:
    """Install ``reporter`` as the active one (``None`` resets to default)."""
    _reporter_var.set(reporter)
    return reporter


@contextmanager
def using_reporter(reporter: Optional[Reporter]) -> Iterator[Optional[Reporter]]:
    """Scope a reporter, restoring the previous one afterwards (tests)."""
    token = _reporter_var.set(reporter)
    try:
        yield reporter
    finally:
        _reporter_var.reset(token)


def make_reporter(
    *,
    quiet: bool = False,
    verbose: bool = False,
    no_color: bool = False,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> Reporter:
    """Build a :class:`Reporter` from CLI-shaped flags.

    ``quiet`` wins over ``verbose`` - asking for silence and noise at once is
    a user mistake, not a reason to be noisy.
    """
    if quiet:
        level = Level.QUIET
    elif verbose:
        level = Level.VERBOSE
    else:
        level = Level.NORMAL
    return Reporter(
        level=level,
        color=False if no_color else None,
        stdout=stdout,
        stderr=stderr,
    )
