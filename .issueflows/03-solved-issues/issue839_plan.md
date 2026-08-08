# Issue #839 — plan

## Goal

Keep non-data CLI verbs (especially default `cellpy setup`) off the reader stack and optional-dep probes, extending the #837 light-bootstrap contract without slowing `convert` / `run` / explicit checks.

## Constraints

- Patch-stream UX/perf; not Stage 5.
- `info --check` stays a full sanity path (may import `cellreader`).
- `convert` / `run` may stay heavy.
- Prefer small behavioral flips + tests over a large `cli_api` rewrite in the first cut.
- Match existing Typer CLI surface style; document any flag changes in help + design note.

### Prior art

- [#837](https://github.com/jepegit/cellpy/issues/837) / [`cli-light-startup.md`](../04-designs-and-guides/cli-light-startup.md): lazy `__init__`, `_CliApiProxy`, deferred `_probe_optional_deps` at *import*; `tests/test_cli_light_import.py`.
- [`setup_config`](../../../cellpy/cli_api.py) / [`_check`](../../../cellpy/cli_api.py) / [`_check_import_cellpy`](../../../cellpy/cli_api.py): setup always calls `_check` at end; probes when `not no_deps`.
- CLI flag today: `--no-deps` (default probe **on**). Help text says “Don't install…” but code only **reports** missing optional imports.
- Tests: `tests/test_cellpy_cmd.py` setup/info coverage; extend `test_cli_light_import.py` pattern.
- Toolbox: no CLI import helper in `00-tools/` (reuse subprocess pattern from #837).

## Approach

**Phase A — behavior (this PR, required)**

1. **Setup check opt-in**
   - Remove unconditional `_check(...)` from the end of `setup_config`.
   - Add `check: bool = False` to `setup_config` + Typer `--check` on `setup`.
   - When `check=True`, call existing `_check` (same as today).
   - `info --check` unchanged.

2. **Optional-deps probe opt-in**
   - Default: do **not** call `_probe_optional_deps()` during setup.
   - Add `--deps` (opt-in probe / messaging). Keep `--no-deps` as a deprecated no-op (or hidden alias) so old scripts do not break; document the flip.
   - Recommended API: `deps: bool = False` in `setup_config`; CLI `--deps` sets it. `--no-deps` accepted but ignored (warn once or mention in help).

3. **Regression tests**
   - Subprocess test: `setup --silent --dry-run` (or equivalent that does not need real home writes) does **not** leave `cellpy.readers.cellreader` in `sys.modules`.
   - Subprocess or unit: default setup does not call probe (assert `lmfit` / `sqlalchemy_access` absent if that is how probe is detected — or spy/`_optional_deps_probed`).
   - `setup --check` **does** import cellreader (or at least runs `_check_import_cellpy` successfully).
   - `info --check` still works (existing test).

4. **Docs**
   - Update `cli-light-startup.md` with the new contract (setup light by default; checks/deps opt-in).
   - Brief warm timing note on PR/issue comment.

**Phase B — structure (same PR only if small; else follow-up issue)**

- Defer full `cli_api` split (light/config/data modules) unless Phase A lands cleanly with leftover budget.
- Optional stretch: lighter `info --configloc` without full `prmreader` — **out of Phase A** unless trivial; call out in Open questions.

## Files to touch

| Path | Change |
|---|---|
| [`cellpy/cli.py`](../../../cellpy/cli.py) | `--check`, `--deps`; deprecate/keep `--no-deps` |
| [`cellpy/cli_api.py`](../../../cellpy/cli_api.py) | `setup_config(check=..., deps=...)`; no default `_check` / probe |
| [`tests/test_cli_light_import.py`](../../../tests/test_cli_light_import.py) | setup-without-check + deps defaults |
| [`tests/test_cellpy_cmd.py`](../../../tests/test_cellpy_cmd.py) | help/flag smoke if needed |
| [`.issueflows/04-designs-and-guides/cli-light-startup.md`](../04-designs-and-guides/cli-light-startup.md) | contract update |

## Test strategy

- `uv run pytest tests/test_cli_light_import.py tests/test_cellpy_cmd.py tests/test_cli_api.py -q`
- Essential gate at close: `uv run pytest -m essential`
- Manual: warm `cellpy setup --silent --dry-run` vs `cellpy setup --check --silent --dry-run`

## Open questions

1. **Deps flag flip:** adopt `--deps` (default off) and keep `--no-deps` as deprecated no-op? **Recommend yes.**
2. **`cli_api` split + light configloc in this PR?** **Recommend no** — Phase A only; file follow-up if wanted after merge.
3. **Should interactive setup still run `_check` by default?** **Recommend no** — same opt-in `--check` for both interactive and silent (predictable). Confirm?
