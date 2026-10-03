# Issue #1076: Find cellpy or raw files by project and number range

Source: https://github.com/jepegit/cellpy/issues/1076

## Original issue text

## Context

Part of epic #1074 (agent summary-plots SAL cells 10–15 from local files). Stage 1 finder: list matching files from configured dirs. Empty results are data, not exceptions — Scenario 2 depends on that.

## Scope

Public `filefinder` function (name bikeshed in the issue plan; do not add a new top-level `cellpy.find_cells` unless the plan argues for it) that takes `kind` (`cellpy` | `raw`), `project`, inclusive `number_min` / `number_max`, and optional override roots.

Default roots come from `config.paths.cellpydatadir` or `config.paths.rawdatadir`. Walk with the existing `OtherPath` / `files_only` rglob used by `find_in_raw_file_directory` — do not reimplement a local-only `Path.rglob`. Filter with the #1075 parser.

Return a structured list of `{path, name, number}` (and kind). Zero matches is an empty list, not an error. Do not load cells, do not write files, do not search the other kind when the first is empty. Warn (existing #690 threshold) if the walk is huge.

Unit tests on a tmp tree; one OtherPath/local-equivalent test is enough if a remote fixture is not cheap.

## Acceptance criteria

- `kind="cellpy", project="SAL", 10..15` lists only those files under `cellpydatadir`.
- Same call on an empty dir returns `[]`.
- Number range is inclusive. Project token is case-insensitive.

Goal: `kind="cellpy", project="SAL", 10..15` lists only those files under `cellpydatadir`; same call on an empty dir returns `[]`.

Model: deep

Depends on: #1075

Part of epic #1074.
