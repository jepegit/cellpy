# Issue #960 — plan: setup writes `cellpy.toml` only

## Goal

`cellpy setup` must write (or refresh) `cellpy.toml`, not the legacy YAML
`.cellpy_prms_*.conf`.

## Constraints

- Existing `.conf` files keep working through the loader fallback; `cellpy setup migrate` stays the one-time converter.
- Do not reset paths on every re-run: “config exists” must look at `cellpy.toml` (and treat a leftover `.conf` as already-set-up).
- Docs already claim setup writes TOML (`docs/getting_started/configuration.md`).

### Prior art

- `_write_toml_config_file` / `_write_config_file` in `cellpy/cli_api.py` — setup currently calls both (dual-write leftover from #454).
- `config.loader.user_config_path` / `CONFIG_FILENAME` — canonical TOML location.
- `config.loader.active_config_file` — toml before legacy YAML (#851).
- `tests/test_cellpy_cmd.py::test_cli_setup` — dry-run counts three “would write” lines (conf, toml, env).
- `tests/test_cellpy_cmd.py::test_cli_setup_creates_dirs_and_files` — asserts the `.conf` was written.

## Approach

1. Stop calling `_write_config_file` from `setup_config` (interactive and silent).
2. Resolve the TOML path the same way `_write_toml_config_file` does (`test_user` → next to the old dst; else `user_config_path()`).
3. Set `reset` when **neither** that TOML nor the legacy dst `.conf` exists.
4. Drop `_write_config_file` if it has no remaining callers.
5. Update the setup tests so they require TOML and forbid a new `.conf`.

## Files to touch

- `cellpy/cli_api.py` — stop legacy write; existence check uses TOML.
- `tests/test_cellpy_cmd.py` — dry-run count 2; create-files asserts toml, not conf.
- `HISTORY.md` — unreleased bullet (close).

## Test strategy

`uv run pytest -m essential` plus `tests/test_cellpy_cmd.py` setup tests.

## Open questions

None — the issue names the leftover dual-write.
