# Issue #839: perf(cli): keep more commands off the reader stack after light bootstrap

Source: https://github.com/jepegit/cellpy/issues/839

## Original issue text

## Problem / context

#837 made CLI bootstrap light (`cellpy --help`, `info --version` no longer load
`cellreader` / optional CLI probes). Several common verbs still pay the heavy
stack when the user did not ask for data:

- `cellpy setup` always ends with `_check()` → imports `cellreader`
- `setup` also probes optional deps (lmfit / sqlalchemy_access / …) unless `--no-deps`
- `info --configloc` / `--params` / `--config` go through `prmreader` (not readers, but still weighty)
- All real commands share one `cli_api` blob

Install/first-use UX still hurts on `setup` after conda install even when version is fast.

Related: #837, design note `.issueflows/04-designs-and-guides/cli-light-startup.md`.

## Spec

Make more non-data CLI commands stay in the light path:

1. **Setup:** do not run `_check()` / full reader import by default; opt-in via
   `setup --check` and/or keep full sanity on `info --check` only.
2. **Optional-deps probe:** do not import lmfit/sqlalchemy_access/… unless the
   user asked (`--deps` / explicit messaging path), not on every setup.
3. **Split CLI API by weight** (or equivalent lazy per-command modules):
   - light: version, configloc, edit, serve, list journals
   - config: setup, migrate, info --config/--params
   - data: convert, run (batch/readers) — may stay heavy
4. **Optional:** lighter path for printing config location without full `prmreader`.
5. Extend the #837-style subprocess/`sys.modules` guard to cover the newly light
   commands (at least `setup` without `--check`, and `info --configloc` if made light).

## Acceptance criteria

- [ ] `cellpy setup` (silent / non-interactive, no `--check`) does not import
      `cellpy.readers.cellreader` (subprocess regression).
- [ ] Optional-dep probes are not run on default setup unless explicitly requested.
- [ ] `info --check` (and any new `setup --check`) still exercise the reader import check.
- [ ] `convert` / `run` behavior unchanged (still load data stack when invoked).
- [ ] Design note updated (`cli-light-startup.md` or follow-on) with the new contract.
- [ ] Warm timings for light commands clearly better than pre-change setup path
      (document briefly on the issue/PR).

## Out of scope

- Making `convert` / `run` / `info --check` fast (they should load readers).
- Broader package-layout / plotting import refactor beyond CLI command paths.
- Stage 5 feature work.
