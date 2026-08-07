# CLI light startup (#837)

## Context

`cellpy` console entry is `cellpy.cli:cli`. Importing that module always runs
`cellpy/__init__.py` first. Eager readers + module-level optional-dep probes in
`cli_api` made `cellpy info --version` pay the full scientific stack (minutes
cold after conda-forge install; ~5 s warm).

## Decision

- Keep package `__init__` symbols lazy (PEP 562) except `__version__` / logging.
- Defer `cli_api` from `cli.py` until a command runs.
- Probe optional deps (cookiecutter, github, lmfit, …) on demand, not at import.
- Guard with `tests/test_cli_light_import.py` (subprocess + `sys.modules`).

## Alternatives

- Separate top-level entry module outside `cellpy` — rejected (more packaging churn).
- Soften only `cli_api` — insufficient; entry point still loads package init.
