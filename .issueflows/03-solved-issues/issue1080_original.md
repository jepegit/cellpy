# Issue #1080: MCP find_cells tool (no silent raw crawl)

Source: https://github.com/jepegit/cellpy/issues/1080

## Original issue text

## Context

Part of epic #1074 (agent summary-plots SAL cells 10–15 from local files). Stage 2: the library can find (`filefinder.find_by_project`, #1076); the agent still cannot. Add one MCP tool that lists matches from configured dirs and **stops**. Existing `load_cell` / `collect` / `render` finish the plot. No raw crawl in this stage.

## Scope

In `cellpy-mcp`, add a tool (suggested `find_cells`) that calls `filefinder.find_by_project`. Inputs: `project`, `number_min`, `number_max`, `kind` defaulting to `cellpy`. Output: handles/facts only — count, names, numbers, paths the sandbox may read.

If `kind=cellpy` and the list is empty, return `{found: 0, offer_raw: true}` (or equivalent) and **do not** search `rawdatadir`. If `cellpydatadir` is a remote URI, say so (`remote: true`, reason) rather than pretending the sandbox can walk it.

Update `docs/getting_started/agents.md` / MCP chapter and add a short agent-prompt snippet for “summary-plot SAL 10–15” that uses find → load → collect → render.

Implement in the `cellpy-mcp` repo; this GitHub issue stays the tracker on `jepegit/cellpy`.

## Acceptance criteria

- MCP `find_cells(project="SAL", 10, 15)` returns the matching local cellpy files, or a structured empty + `offer_raw` — never a raw listing.

Goal: MCP `find_cells(project="SAL", 10, 15)` returns the matching local cellpy files, or a structured empty + `offer_raw` — never a raw listing.

Model: default

Depends on: #1076

Part of epic #1074.
