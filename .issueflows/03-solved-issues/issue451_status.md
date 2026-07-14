# Status — issue #451 (Stage 1.6)

- [x] Done

## 2026-07-15

- Re-pinned `cellpycore==0.2.0` (the Stage-1 additive release: core#115–#118)
  and delegated the duplicated converter bodies to `cellpycore.units`:
  `get_converter_to_specific`, `nominal_capacity_as_absolute`,
  `to_cellpy_unit` → `convert_value`, `unit_scaler_from_raw` →
  `calculate_scaler`, and `_make_summary`'s inline current-factor pint math →
  `calculate_current_conversion_factor` (also renamed the summary call to the
  non-deprecated `specific_conversion_factors` kwarg).
- Fixed three Stage 1.8 M2 leftovers found by the full-suite run (all
  pre-existing on master, not caused by the delegation):
  1. `dbreader.DbSheetCols` called `dataclasses.asdict` on the pydantic
     `config.db_cols` → `model_dump()`.
  2. `log.setup_logging` shadowed the `config` module with the logging.json
     dict, breaking `config.paths.filelogdir` — module aliased to
     `cellpy_config`. This was also the test-pollution source behind the
     order-dependent `total_time_at_low_voltage` failures.
  3. `PathsConfig` now has `validate_assignment=True` (config plan §3.1) so
     string assignments re-run Path/OtherPath coercion; the Path serializers
     are additionally defensive. Fixes `cellpy info --params` crashing after
     batch runs (PydanticSerializationError).
- Full suite: **581 passed, 0 failed** (previously 9 failures on master).
