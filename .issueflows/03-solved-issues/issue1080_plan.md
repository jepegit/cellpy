# Issue #1080 plan

## Goal

An MCP client can call `find_cells(project="SAL", 10, 15)` and get matching
local `.cellpy` files, or `{found: 0, offer_raw: true}` — never a raw listing.
Existing `load_cell` / `collect` / `render` finish Scenario 1.

## Constraints

- Two repos: tool in `cellpy-mcp`; docs + this tracker on `jepegit/cellpy`.
- Do not search `rawdatadir` when `kind` is `cellpy` (even if empty).
- Sandbox stays local-only. Remote `cellpydatadir` → `remote: true` + reason,
  no pretend walk. Remote *load* is Stage 3 / Later.
- Handles/facts only — no file bytes.
- `find_by_project` is on cellpy `master` (#1079) but not a released pin yet.
  Do not bump `cellpy>=` to an unreleased version.

### Prior art

- `cellpy.filefinder.find_by_project` (#1076) — call it; do not re-walk.
- MCP `list_cells` is **session** only (already loaded). New tool is disk find.
- `sandbox.default_roots` / `_is_local_dir` — reuse for remote honesty.
- `tests/test_cell_tools.py` `drive` harness — same pattern.
- Agent prompts live in cellpy `docs/getting_started/agent_prompts.md` (#1064).

## Approach

**cellpy-mcp** (branch `1080-mcp-find-cells` on that repo):

1. Tool `find_cells(project, number_min, number_max, kind="cellpy")`.
2. If `kind` not in `cellpy`/`raw` → `Refused`.
3. If `kind=cellpy` and `config.paths.cellpydatadir` is a remote URI →
   `{found: 0, remote: true, reason: "…"}` and stop.
4. Else call `filefinder.find_by_project(...)`. If the attribute is missing
   (old cellpy), `Refused` naming #1076 / `find_by_project`.
5. Filter returned paths through `sandbox.resolve` (drop anything outside
   roots; do not crash the whole list).
6. Empty + `kind=cellpy` → `{found: 0, offer_raw: true, cells: []}`.
   Hits → `{found: N, offer_raw: false, cells: [{name, number, path}]}`.
   `kind=raw` may list raw (Stage 3 will add `needs_metadata`); this stage
   still must not auto-switch from cellpy-empty to raw.

**cellpy** (this worktree):

- `docs/getting_started/mcp.md` — document `find_cells`.
- `docs/getting_started/agent_prompts.md` — SAL 10–15: find → load → collect
  → render (`<!-- agent-doc: … -->` + latest URL if that page’s convention
  requires it).
- One line in `agents.md` / `AGENTS.md` if the MCP tool list is mirrored.

## Files to touch

- `cellpy-mcp/src/cellpy_mcp/cells.py` — register `find_cells`
- `cellpy-mcp/tests/test_cell_tools.py` — empty/`offer_raw`, hits, remote
- `docs/getting_started/mcp.md`, `agent_prompts.md`, maybe `agents.md` / `AGENTS.md`
- `HISTORY.md` (cellpy close); cellpy-mcp changelog if they have one

## Test strategy

- cellpy-mcp: `uv run pytest` (existing essential mark on cell-tool tests).
  Monkeypatch `find_by_project` so tests do not need a released cellpy.
- cellpy: no new library tests; docs checker if the new prompt gets an
  `agent-doc` comment (`00-tools/check_rtd_latest_links.py` after zensical).

## Open questions

None that block. `kind=raw` on this tool is allowed but unused by Scenario 1;
Stage 3 will extend the empty-cellpy dialogue.
