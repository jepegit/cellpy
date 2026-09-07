# Issue #938 plan (yolo aborted)

## Goal

Named errors for missing `mdb-export` / ODBC, plus `list_instruments` reporting unavailable loaders, plus an absolute default `examplesdir`.

## Why yolo stopped

Not a single small change. Three independent deliverables:

1. `arbin_res`: `shutil.which("mdb-export")` → typed error naming `mdbtools`.
2. Public `list_instruments` shape: add `available` / `reason` (and keep importing loaders that fail on `libodbc.so.2`).
3. Comment: default `examplesdir` must be home-absolute (overlaps #960).

Run `/iflow-plan` / `/iflow-build` on #938 (or split) instead of yolo.

## Constraints

### Prior art

- `list_instruments()` in `cellpy/readers/data_structures.py` (quiet listing; import failures omitted)
- `InstrumentFactory._is_expected_discovery_skip` / `create_all(quiet=True)`
- `OptionalDependencyError` (#937 / `legacy-files`)
- Plot `registry.families()` availability pattern (#868)
