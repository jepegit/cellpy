# Plan — issue #454 (Stage 1.9)

The heavy lifting (TOML writer, YAML→TOML converter, provenance registry,
`model_dump_for_file` with secrets excluded) already landed with the parallel
config stack (#452). This issue is CLI wiring:

1. **`cellpy setup`** becomes a click *group* with
   `invoke_without_command=True` — the classic invocation and all its options
   keep working unchanged (folder creation logic untouched), and after writing
   the legacy conf it now also writes the **`cellpy.toml` twin** generated
   from the resolved `CellpyConfig` models (`_write_toml_config_file`).
   In test-user (DEV) mode the TOML lands next to the legacy conf, never in
   the real platform config dir.
2. **`cellpy setup migrate`** — new subcommand: auto-detects the legacy conf
   via the existing prmreader discovery (or takes `--src`), converts with
   `cellpy.config.migrate.convert_yaml_file_to_toml` to the platform
   user-config path (or `--dst`); refuses to overwrite without `--force`;
   `--dry-run` supported; the old file is left untouched (it keeps working
   through the v2.0 window).
3. **`cellpy info --config`** — prints the resolved configuration
   (secrets excluded) with per-field provenance from
   `cellpy.config.sources()` (`key = value  # source-layer`).
4. **Tests** in `tests/test_cellpy_cmd.py`: setup writes a parseable TOML twin
   whose sections ⊆ the model fields and excludes secrets; migrate converts
   the fixture conf and refuses a second run without `--force`; info --config
   exits 0 with provenance markers and no secrets section.
