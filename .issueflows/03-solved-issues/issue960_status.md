# Issue #960 status

- [x] Done

## What's done

- `cellpy setup` writes `cellpy.toml` only; dropped `_write_config_file`.
- Existence check uses TOML (legacy `.conf` still counts as already-set-up).
- Tests: dry-run writes toml+env; create-files asserts no new `.conf`.
- Docs: `configuration.md`, `AGENTS.md` smoke note, test-registry.

## Remaining work

- None.
