# Plan: #1111 Fails on check

## Goal

Make `cellpy info --check` exit 0 when only optional Arbin `.res` tooling
is missing, so scheduled Windows pip CI (and Windows users without Access
ODBC) are not treated as a broken install.

## Constraints

- Keep #891 contract: a **broken core setup** still exits non-zero
  (imports / configuration).
- Align with [#938 instrument availability](../04-designs-and-guides/instrument-availability.md):
  missing mdbtools/ODBC is optional capability, not an install failure.
- No CI-only paper-over (`|| true` / `continue-on-error`) — fix product
  semantics so scripts and CI share one meaning.
- Out of scope: scheduled linux/macos pytest `matplotlib` ImportError
  (separate red jobs; not this issue).

### Prior art

- `_CheckOutcome` / `_check` / `show_info` in `src/cellpy/cli_api.py` —
  three checks; any `ok=False` increments `failed` → CLI `typer.Exit(1)`.
- `cli_ui.Reporter.warn` / `.fail` / `.summary` already exist.
- `tests/test_cli_info.py` — pins exit code + labels; fixture
  `one_failing_check` currently stubs **arbin** failure to assert exit 1
  (must move to a hard check after this change).
- Design: `instrument-availability.md` (#938), `cli-light-startup.md`
  (`info --check` opt-in).
- Toolbox: nothing applicable.

## Approach

1. Add `required: bool = True` on `_CheckOutcome`.
2. In `_check`: if `not outcome.ok` and `not outcome.required` →
   `ui.warn(label, …)` and **do not** increment `failed`; hard fails stay
   `ui.fail` + count. Summary still `passed_hard of total` with exit based
   on hard failures only (advisory rows visible as warnings).
3. Make `_check_import_pyodbc` return outcomes with `required=False` on
   every soft miss path (no mdbtools / no ODBC driver / etc.). Success
   paths stay `ok=True` (required irrelevant).
4. Leave imports + configuration as required.
5. Update tests:
   - `one_failing_check` → stub a **required** check (e.g. imports or
     configuration) for exit-1 coverage.
   - New: arbin soft-fail → exit 0, warn text present, summary still
     honest (e.g. not “3 of 3” if we count advisory separately — prefer
     “2 of 3 checks passed” with warn row, exit 0; or “3 of 3” with one
     warn — **recommend**: keep `passed/total` for hard+soft rows that
     are `ok`, warn rows neither pass nor fail the count → show
     `N of M checks passed` where M includes advisory; exit 0 when no
     hard fails. Exact wording: match current summary helper; document
     in test).
6. No workflow YAML change required for the Windows check step once
   product exits 0.

## Files to touch

| Path | Change |
|---|---|
| `src/cellpy/cli_api.py` | `required` on `_CheckOutcome`; `_check` soft path; pyodbc outcomes `required=False` on miss |
| `tests/test_cli_info.py` | Retarget hard-fail fixture; add soft-arbin exit-0 test |
| `.issueflows/04-designs-and-guides/` (short note) | Optional one-liner under cli-light or new tiny note linking #1111 |

## Test strategy

- `uv run pytest tests/test_cli_info.py -m essential`
- Manual: `uv run cellpy info --check` (local already green with mdbtools);
  monkeypatched soft-fail covered by unit test.
- Evidence for CI: after merge, next scheduled `pip install (windows)`
  should pass the check step (other job failures may remain).

## Open questions

None blocking — recommended defaults above. If you prefer advisory to
still print as `x` (fail glyph) but exit 0, say so; otherwise use `warn`.
