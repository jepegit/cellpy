# Issue #891 — status

- [ ] Done

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

## Remaining work

- [ ] PR 2 — global flags (`--quiet` / `--verbose` / `--no-color`), failures to
      stderr, exit codes 0/1/2, delete the hand-rolled usage block in `run`;
      regenerate `tests/data/cli_surface.json` in the same commit.
- [ ] PR 3 — `info` / `info --check`.
- [ ] PR 4 — `setup` (drop the parameter dump, make `--silent` real).
- [ ] PR 5 — copy pass over the remaining commands; fix the `f[cellpy]` literal
      and the `deiced` typo; remove the stray `print()` calls.
- [ ] Register the new essential tests in
      [test-registry.md](../04-designs-and-guides/test-registry.md). Deferred
      out of PR 1 only because the concurrent #912 session has uncommitted rows
      in that file; staging it would have swept their work into this commit.
      Rows to add (`tests/test_cli_ui.py`, essential/always, code under test
      `cli_ui.Reporter`, issue #891) plus
      `test_cli_light_import.py::test_importing_cli_ui_does_not_import_rich`.

## Notes

- A concurrent session is working #912 in this same checkout. PR 1 commits only
  `cellpy/cli_ui.py`, `tests/test_cli_ui.py`,
  `tests/test_cli_light_import.py` and these `.issueflows` docs; the #912
  changes to `cellpy/readers/cellpy_file/v9.py`, `tests/test_cellpy_file_v9.py`
  and `HISTORY.md` are left untouched in the working tree.
