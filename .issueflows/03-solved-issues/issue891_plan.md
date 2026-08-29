# Plan — #891: CLI feedback

## Goal

Make `cellpy <command>` output look and read like one deliberate program:
colour and a symbol column instead of a repeated `[cellpy]` prefix, one line per
real action instead of debug dumps, failures on stderr with sane exit codes, and
`--quiet` / `--verbose` / `--no-color` that actually work.

## Findings (what is wrong today)

Everything prints through `_say` in [cli_api.py](../../cellpy/cli_api.py), whose
docstring states the problem: *"colour kwargs from old typer.echo are ignored"*
(`cli_api.py:490`). `rich` is already a dependency but only Typer's **help**
renderer uses it — hence tidy boxed help screens and flat grey command output.

| # | Problem | Evidence |
| --- | --- | --- |
| 1 | Developer debug output shown to users | `setup --dry-run`: `Create custom init filename and get user_dir and destination`, `Got the following parameters:` + internal names (`init_filename`, `dst_file`, `not_relative`) |
| 2 | Raw Python reprs leak | `info --check`: `Found these: ['Microsoft Access Driver (*.mdb, *.accdb)']` |
| 3 | Stray dev prints in shipped paths | `print("RUNNING SOMETHING ELSE")`, `say("RUNNING LINUX")` (`cli_api.py:470-476`) |
| 4 | Same fact twice, two formats | `*** dry-run: skipping actual saving of X ***` then `[cellpy] (setup) dry-run: would write X (not written)` |
| 5 | Literal f-string bug in the **failure** message | `_say("f[cellpy] -> failed!!!!")` (`cli_api.py:1083`) |
| 6 | `--silent` does not silence | `cellpy setup --dry-run --silent` emits ~25 lines |
| 7 | Errors are not errors | `cellpy run` hand-rolls Typer's usage text to **stdout** (`cli.py:382-387`) while `convert` gets the real rendered error; nothing uses stderr; exit codes split `sys.exit(-1)` vs `typer.Exit(2)` |
| 8 | Hard-coded 80-column rules | `80 * "-"`, `" [cellpy] WARNING! ".center(80, "-")`, `=== results ===` |
| 9 | Apologetic / vague tone, typos | `Sorry. This did not work as expected!` ×3, `OK - but this directory already exists!`, `skipping check ... (for now)`, `could not deiced what is the new project` |
| 10 | No global switches | root command exposes only `--help` |
| 11 | Long jobs give no feedback | `run -j` prints `running journal X` then nothing — **deferred**, see Out of scope |

## Constraints

- **The CLI surface is a contract** ([test_cli_surface.py](../../tests/test_cli_surface.py)
  against `tests/data/cli_surface.json`). It pins commands and flags, **not**
  message text — so the copy work is free, but the new global flags require
  `uv run python dev/snapshot_cli_surface.py` in the *same* commit.
- `cli_api` functions are callable as a library with `echo=` and are **quiet by
  default** (`_silent`). That stays: the reporter becomes the default for the
  CLI entry points only, never for library callers.
- Do not restructure `cli.py` / `cli_api.py` beyond what the output work needs.
  No new commands, no renamed flags.
- Keep `_say` working — private helpers all over `cli_api` call it.
- Do not add progress bars / spinners in this issue.
- `rich` markup is a footgun on user data (a Windows path with `[` gets parsed):
  print with `markup=False` and pass styles as arguments.

### Prior art

- `_say` / `_using_echo` / `_echo_var` / `_resolve_echo` — `cli_api.py:486-500`.
  **Extend, do not replace:** `_say` keeps its signature; the bound echo gains
  levels.
- `_silent` default echo — keeps library calls quiet. **Unchanged.**
- Typer already renders usage errors well (`convert` proves it). **Delete the
  hand-rolled block in `run` and let Typer do it.**
- `tests/test_cli_api.py` asserts on a handful of message strings
  (`"number of batch-files located: N"`, `"does not exist"`,
  `"Could not import cookiecutter"`, `"Content of"` / `"No batch-files"`).
  Those move with the copy pass, in the same PR.
- `cellpy/libs/local_fastnda/cli.py` is a vendored third-party CLI. **Out of
  scope, do not touch.**

## Approach

### New module `cellpy/cli_ui.py`

A thin reporter over `rich.console.Console` (rich already handles TTY
detection, `NO_COLOR`, and legacy Windows consoles):

```python
ui = Reporter(level=Level.NORMAL, color=None)   # color=None -> auto

ui.title("cellpy 2.1.2 - checking your setup")
ui.ok("odbc driver", "Microsoft Access Driver (*.mdb, *.accdb)")
ui.fail("configuration", "no cellpy.toml found")
ui.hint("run  cellpy setup")
ui.detail("rawdatadir", "scp://.../projects", note="remote, not checked")
ui.step("writing cellpy.toml")
ui.warn("legacy .conf found", hint="cellpy setup migrate")
ui.rule()                    # terminal width, not 80
ui.summary(passed=3, total=3)
```

Vocabulary (the whole visual language — nothing else gets invented ad hoc):

| Call | Renders | Colour | Stream |
| --- | --- | --- | --- |
| `title` | plain heading + blank line | default, bold | stdout |
| `ok` | `  ✓ label   detail` | green symbol | stdout |
| `warn` | `  ! label   detail` | yellow symbol | stdout |
| `fail` | `  ✗ label   detail` | red symbol | **stderr** |
| `step` | `  · doing thing` | dim | stdout |
| `detail` | `      key   value   (note)` aligned | dim key | stdout |
| `hint` | `      hint: …` | cyan | follows its parent |
| `rule` | width-aware horizontal rule | dim | stdout |

- **Symbols:** unicode when the stream encoding can encode them, ASCII
  (`v` / `!` / `x` / `-`) when it cannot. Decided by probing `stream.encoding`,
  not by guessing the platform.
- **Colour off** when: `--no-color`, `NO_COLOR` set (any value), stdout is not a
  TTY, or `TERM=dumb`. Piped output stays plain and greppable.
- **Levels:** `QUIET` (failures only, plus explicitly-requested payload such as
  `info --version`), `NORMAL`, `VERBOSE`.

### Global flags

Add a root Typer callback carrying `--quiet/-q`, `--verbose`, `--no-color`.
**No `-v` short flag** — `info -v` already means `--version`, and reusing it
across levels would be a trap. Per-command `--silent` maps to `QUIET` and
`--debug` to `VERBOSE` (+ DEBUG logging), so those existing flags finally mean
something.

### Exit codes

`0` success · `1` runtime failure · `2` usage error (Typer's own). Drop
`sys.exit(-1)`, which surfaces as 255.

## Staging (one PR each, off `master`)

1. **`cli_ui` reporter + tests.** Nothing wired yet; no user-visible change.
2. **Global flags, streams, exit codes.** Root callback + snapshot regen; map
   `--silent` / `--debug`; failures to stderr; delete the hand-rolled usage
   block in `run`.
3. **`info` / `info --check`.** Banner soup → aligned check list with a summary
   line; no raw list reprs.
4. **`setup`.** Kill the parameter dump, one line per action, single dry-run
   statement, `--silent` genuinely silent.
5. **Copy pass.** Remaining commands (`edit`, `new`, `pull`, `serve`,
   `convert`, `run --list`), the `f[cellpy]` and `deiced` bugs, the stray
   `print()` calls, and the apology strings. Update the pinned strings in
   `tests/test_cli_api.py`.

## Tests

- New `tests/test_cli_ui.py`: colour suppressed under `NO_COLOR` / non-TTY;
  ASCII fallback when the stream cannot encode `✓`; level gating (`QUIET` hides
  `ok`/`step`, keeps `fail`); `fail` goes to stderr.
- `tests/test_cli_api.py`: updated assertions for the rewritten messages.
- `tests/test_cli_surface.py`: regenerated snapshot in PR 2 only, so the surface
  change is visible in review.
- `uv run pytest -m essential` green before each PR.

## Out of scope

- Progress feedback for long `cellpy run` batch jobs → follow-up issue.
- rich `Table` / `Panel` layouts (explicitly ruled out this round).
- Restructuring `cli.py` / `cli_api.py`; new commands or renamed flags.
- `cellpy/libs/local_fastnda/cli.py` (vendored).
- Library-side logging configuration (`cellpy.log`).
