# Issue #837: perf(cli) cold-start / slow `info --version`

- [x] Done

## What's done

- Lazy `cellpy/__init__.py` (PEP 562) — required because entry point `cellpy.cli` always loads package init.
- `cellpy/cli.py`: `_CliApiProxy` defers `cli_api` until a command runs.
- `cellpy/cli_api.py`: lazy `config`/`prmreader`; deferred optional-dep probes; VERSION via `cellpy._version`.
- Regression: `tests/test_cli_light_import.py` (essential; subprocess).
- Design note: `.issueflows/04-designs-and-guides/cli-light-startup.md`.
- Essential suite green at close; HISTORY `[Unreleased]` bullet.

## Remaining work

- None.
