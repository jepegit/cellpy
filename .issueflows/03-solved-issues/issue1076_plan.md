# Issue #1076 plan

## Goal

`filefinder` can list cellpy or raw files for a project token and inclusive
number range from configured dirs (including `OtherPath`). Empty is `[]`,
never an error and never a crawl of the other kind.

## Constraints

- No BatBase, no MCP, no `cellpy.get` / load.
- Do not add top-level `cellpy.find_cells`.
- Reuse `find_in_raw_file_directory` + `parse_project_run_number` (#1075).
- Do not walk a huge shared root without the existing #690 warning.
- Public surface: one sentence in `docs/getting_started/agents.md` + root
  `AGENTS.md` (this-project agent-docs rule).

### Prior art

- `filefinder.parse_project_run_number` — filter after the walk.
- `filefinder.find_in_raw_file_directory` — `OtherPath.rglob(..., files_only=True)`,
  #690 warn, empty-dir log. Call it; do not reimplement `Path.rglob`.
- `filefinder.search_for_files` — one `run_name`, not a range. Coexist.
- MCP sandbox (cellpy-mcp) is Stage 2. Out of scope.
- Toolbox: none for this walk.

## Approach

Add `filefinder.find_by_project(project, number_min, number_max, *, kind="cellpy", root=None)`.

1. `kind` must be `"cellpy"` or `"raw"`; else `ValueError`.
2. Default `root`: `config.paths.cellpydatadir` or `config.paths.rawdatadir`.
3. Walk via `find_in_raw_file_directory(raw_file_dir=root, extension=…)`.
   For `cellpy`, pass `config.file_names.cellpy_file_extension`. For `raw`,
   pass no extension (any file; the parser is the filter).
4. Keep paths whose `parse_project_run_number(name, project)` is not `None`
   and lies in `[number_min, number_max]` inclusive.
5. Return a list of dicts `{path, name, number, kind}`, sorted by
   `(number, name)`. Zero matches → `[]`.
6. Do not consult the other configured dir. Do not load or write.

## Files to touch

- `cellpy/readers/filefinder.py` — `find_by_project`
- `tests/test_filefinder.py` — tmp-tree tests (empty, range, wrong kind,
  `OtherPath` of a local dir)
- `docs/getting_started/agents.md` + `AGENTS.md` — one finder sentence
- `HISTORY.md` — close

## Test strategy

`uv run pytest tests/test_filefinder.py` plus `uv run pytest -m essential`.
New tests marked essential: tmp tree with SAL 9–16; `kind="cellpy", 10..15`
returns only 10–15; empty dir `[]`; `kind="raw"` does not pick `.cellpy`
when they live only under the cellpy root; unknown `kind` raises.

## Open questions

None that block coding. Name `find_by_project` is the bikeshed default;
say so on Revise if you want another.
