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

- **PR 2 — global flags, streams, exit codes.** Root callback installs the
  reporter from `--quiet` / `-q`, `--verbose`, `--no-color`; per-command
  `--silent` / `--debug` adjust one invocation via `Reporter.with_level`.
  `cellpy run` raises real usage errors (stderr, exit 2) instead of hand-made
  usage text and a flag dump; `convert` reports a bad `--to` on stderr.
  `info` echoes as payload so `--quiet` cannot silence an answer. The surface
  snapshot now describes the **root** command too, so global options are under
  the same contract as everything else.

## Remaining work

- [ ] PR 3 — `info` / `info --check`.
- [ ] PR 4 — `setup` (drop the parameter dump, make `--silent` real).
- [ ] PR 5 — copy pass over the remaining commands; fix the `f[cellpy]` literal
      and the `deiced` typo; remove the stray `print()` calls.
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
