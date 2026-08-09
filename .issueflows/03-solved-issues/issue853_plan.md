# Plan: #853 report project cellpy.toml in --configloc

## Goal

`cellpy info --configloc` names a project-level `cellpy.toml` when one exists
and states that it outranks the user file.

## Constraints

- Reuse `find_project_config_file` / `LoadOptions.project_config_file`; no second
  discovery path.
- `edit config` still opens the user file.
- Reporting only; load precedence unchanged.

### Prior art

- `ActiveConfigFile` / `active_config_file` (#851)
- `_configloc` in `cli_api.py`
- `docs/getting_started/configuration.md` "Where is my config?"

## Approach

1. Add `project_path` to `ActiveConfigFile`; resolve via same rules as
   `load_config` (skip when equal to user path).
2. `_configloc` prints the project notice when set.
3. Tests in `test_config.py` + CLI smoke; docs line.

## Files to touch

- `cellpy/config/loader.py`
- `cellpy/cli_api.py`
- `tests/test_config.py`, `tests/test_cellpy_cmd.py`
- `docs/getting_started/configuration.md`
- HISTORY

## Test strategy

`uv run pytest tests/test_config.py tests/test_cellpy_cmd.py -q -k configloc`

## Open questions

None — keep edit-config on user file (issue suggestion).
