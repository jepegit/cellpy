# Issue #1089: MCP raw search after confirm, including OtherPath

Source: https://github.com/jepegit/cellpy/issues/1089

## Original issue text

## Context

Part of epic #1074 (agent summary-plots SAL cells 10–15 from local files). Stage 3 Scenario 2: no cellpy files → user says search raw → hits + need metadata → user gives mass/nom_cap → load + summary plot.

## Scope

Extend `find_cells` (or add `find_raw_files`) so raw is searched **only** when the caller sets `kind=raw` (or an explicit confirm flag). Use `filefinder.find_by_project` so `rawdatadir` may be an `OtherPath`. Report hits (names, numbers, path/URI). Include a structured `needs_metadata: ["mass", "nominal_capacity"]` so the agent asks instead of guessing.

If the URI is remote, either (a) return the URIs and load via `cellpy.get`/`OtherPath` without widening the pathlib sandbox to `/`, or (b) refuse load with a message that names the remote root — pick (a) if a narrow “this path came from `config.paths.rawdatadir`” allowance is safe; otherwise (b) and put remote *load* under Later.

Local raw must load with the user’s mass and nom_cap (`load_cell` from #1088) and then `collect`+`render` a summary plot. Prompt/docs: the Scenario 2 dialogue.

Implement in `cellpy-mcp`; this GitHub issue stays the tracker on `jepegit/cellpy`.

## Acceptance criteria

- After an explicit raw ask, the agent lists matching raw files, says it needs mass and nominal capacity, and (for local raw) plots a rough view once those are given.

Goal: after an explicit raw ask, the agent lists matching raw files, says it needs mass and nominal capacity, and (for local raw) plots a rough view once those are given.

Model: deep

Depends on: #1080, #1088

Part of epic #1074.
