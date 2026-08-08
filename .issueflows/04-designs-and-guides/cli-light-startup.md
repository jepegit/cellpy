# CLI light startup (#837, #839)

## Context

`cellpy` console entry is `cellpy.cli:cli`. Importing that module always runs
`cellpy/__init__.py` first. Eager readers + module-level optional-dep probes in
`cli_api` made `cellpy info --version` pay the full scientific stack (minutes
cold after conda-forge install; ~5 s warm). After #837, default **`setup`** still
called `_check()` (reader import) and probed optional extras unless `--no-deps`.

## Decision

- Keep package `__init__` symbols lazy (PEP 562) except `__version__` / logging.
- Defer `cli_api` from `cli.py` until a command runs.
- Probe optional deps (cookiecutter, github, lmfit, …) on demand, not at import.
- **Default `cellpy setup` is light (#839):** no `_check()`, no optional-deps probe.
  - Opt-in: `cellpy setup --check` (or `cellpy info --check`).
  - Opt-in: `cellpy setup --deps` (probe/report missing optional extras).
  - `--no-deps` is a deprecated no-op (probing is already off by default).
- Guard with `tests/test_cli_light_import.py` (subprocess + `sys.modules`).

## Still heavy (by design)

- `convert`, `run` (batch/readers)
- `info --check` / `setup --check`

## Alternatives

- Separate top-level entry module outside `cellpy` — rejected (more packaging churn).
- Soften only `cli_api` — insufficient; entry point still loads package init.
- Full `cli_api` light/config/data split — deferred (follow-up after #839 Phase A).
