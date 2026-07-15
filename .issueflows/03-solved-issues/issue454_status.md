# Status — issue #454 (Stage 1.9)

- [x] Done

## 2026-07-15

- `cellpy setup` is now a click group (`invoke_without_command=True`) — the
  classic invocation, options, and folder-creation flow are unchanged, and it
  additionally writes the `cellpy.toml` twin generated from the resolved
  `CellpyConfig` models (`_write_toml_config_file`; secrets excluded;
  DEV-mode writes next to the legacy conf, never the platform config dir).
- New `cellpy setup migrate`: auto-detects the legacy conf (or `--src`),
  converts via `cellpy.config.migrate.convert_yaml_file_to_toml` to the
  platform user-config path (or `--dst`); `--dry-run`; refuses overwrite
  without `--force`; old file left untouched.
- New `cellpy info --config`: resolved values with per-field provenance
  (`key = value  # source-layer`), secrets excluded.
- Tests in `tests/test_cellpy_cmd.py` (TOML twin generation + dry-run guard +
  subcommand registration; migrate conversion of the packaged default conf +
  overwrite refusal; info --config provenance markers).
- Full suite: **584 passed, 0 failed**.
