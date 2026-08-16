# Issue #891 — status

- [x] Done

## What's done

- Survey of the current CLI output recorded in
  [issue891_plan.md](issue891_plan.md) (11 numbered defects with evidence).
- Plan accepted 2026-08-15: restrained visual treatment (colour + symbols, no
  panels/tables), global `--quiet` / `--verbose` / `--no-color` included,
  long-job progress deferred.
- **PR 1 — `cellpy/cli_ui.py` reporter + tests.** The output vocabulary
  (`title` / `ok` / `warn` / `fail` / `step` / `detail` / `hint` / `rule` /
  `summary` / `payload` / `debug`), automatic colour, ASCII symbol fallback,
  stderr for failures, `Level` gating, and an `as_echo()` seam for incremental
  migration. Nothing is wired to a command yet, so there is no user-visible
  change and no HISTORY entry.

- **PR 2 — global flags, streams, exit codes.** Root callback installs the
  reporter from `--quiet` / `-q`, `--verbose`, `--no-color`; per-command
  `--silent` / `--debug` adjust one invocation via `Reporter.with_level`.
  `cellpy run` raises real usage errors (stderr, exit 2) instead of hand-made
  usage text and a flag dump; `convert` reports a bad `--to` on stderr.
  `info` echoes as payload so `--quiet` cannot silence an answer. The surface
  snapshot now describes the **root** command too, so global options are under
  the same contract as everything else.

- **PR 3 — `info` / `info --check`.** Checks return a `_CheckOutcome` (verdict,
  short detail, hint, detail lines) instead of printing their own banner and
  narration, so the caller renders them consistently and the probe output drops
  to `--verbose`. `info --check` exits 1 when a check fails. A remote-capable
  path setting holding a local value is now actually checked. `cli_api._ui()`
  returns a silent reporter when no `echo` was passed, keeping the
  library-quiet contract; `Reporter` resolves its streams lazily so capture and
  redirection work.

- **PR 4 — `setup`.** The parameter dump (`init_filename` / `user_dir` /
  `dst_file` / `not_relative` / `root_dir`, the DEV-MODE lines and the
  `_update_paths` dry-run trace) dropped to `--verbose` via `_debug`; each file
  is stated once (`dry-run: would write X` / `would keep X`), the 80-column
  rules and `[cellpy] (setup)` prefixes are gone, and the interactive prompts
  use the reporter. `--silent` is now passed to `_echo`, and `_ui()` follows
  the reporter behind the bound echo (`Reporter.as_echo` tags it), so a
  per-command `--silent` / `--debug` reaches structured output too — that was
  the actual reason `--silent` printed 25 lines.

- **PR 5 — copy pass.** `edit`, `new`, `pull`, `serve`, `setup migrate`,
  `open_db_editor` and the github helpers moved onto the reporter vocabulary.
  Removed: `RUNNING LINUX` / `RUNNING SOMETHING ELSE`, the apology strings, the
  hard-coded rules, and the bare `print()` calls that bypassed `echo=` (and so
  `--silent`). Fixed on the way: `_pull_tests` / `_pull_examples` passed a
  *tuple* to `_say` (printed as a repr), `cellpy new --list` printed
  `('url', None)` template tuples, and `cellpy pull` with nothing selected /
  `cellpy edit <unknown>` complained but exited 0 — both are now Typer usage
  errors (stderr, exit 2). The `f[cellpy] -> failed!!!!` literal and the
  `deiced` typo are gone (the first had already been removed in PR 3).

## Remaining work

- [x] Register the new essential tests in
      [test-registry.md](../04-designs-and-guides/test-registry.md) (deferred
      from PR 1 while #912 held uncommitted rows there; done in PR 2).

## Notes

- PR 1 was built while a concurrent session held uncommitted #912 work in the
  same checkout, so it committed only its own paths and deferred the
  `test-registry.md` rows. #912 has since merged (#914) and the rows landed in
  PR 2.
- The surface snapshot gained a `root` entry in PR 2. It is additive: the
  existing `commands` list and every per-command assertion are unchanged, and
  no subcommand's parameters moved when the root callback was added.
- PR 4/5 changed no commands and no flags, so the surface snapshot did not need
  regenerating. Pinned message strings in `tests/test_cli_api.py` and
  `tests/test_cellpy_cmd.py` moved with the copy, as planned.
- Out of scope and still open: progress feedback for long `cellpy run` batch
  jobs (plan defect 11).
