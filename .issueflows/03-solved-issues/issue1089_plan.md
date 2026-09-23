# Issue #1089 plan

## Goal

After an explicit `find_cells(..., kind="raw")`, the agent lists matching raw
files (local path or remote URI), gets `needs_metadata: ["mass",
"nominal_capacity"]`, and for allowed paths can `load_cell` with the user’s
mass/nom_cap then `collect`+`render` a summary plot.

## Constraints

- Two repos: tool + tests in `cellpy-mcp`; docs + tracker on `jepegit/cellpy`.
- `kind="cellpy"` still never searches raw (`offer_raw` only).
- Do not widen the pathlib sandbox to `/`.
- Do not invent mass or nominal capacity.
- No new finder in cellpy (`find_by_project` already walks `OtherPath`).
- `load_cell` already forwards `mass_mg` and `nominal_capacity` (#1088).

### Prior art

- MCP `find_cells` (`cellpy_mcp/cells.py`) — `kind` already includes `"raw"`,
  but a remote `rawdatadir` returns `{found: 0, remote: true}` without calling
  the finder; local hits are filtered through `sandbox.resolve`.
- `sandbox._is_local_dir` / `default_roots` — remote URI roots are dropped
  (pathlib cannot contain them). Documented in `docs/getting_started/mcp.md`
  “Roots”.
- `filefinder.find_by_project` (`cellpy/readers/filefinder.py`) — walks
  `OtherPath` via `find_in_raw_file_directory`.
- `otherpath-upath.md` — remote reads copy to local temp; loaders never speak
  SSH. Supported schemes `ssh` / `sftp` / `scp`.
- MCP `load_cell` — `sandbox.resolve` then `cellpy.get`; mass + nom_cap
  pass-through.
- Agent prompt: `docs/getting_started/agent_prompts.md` SAL 10–15 (Scenario 1
  only today).
- Toolbox: `check_rtd_latest_links.py` if the prompt’s `<!-- agent-doc -->`
  URL stays on `mcp.md`.

## Approach

**Recommended remote policy: (a), prefix-checked — not (b).** Scenario 2 says
raw *may* be `OtherPath` and the agent must report hits **and** load. (b)
(refuse load) would fail that lab. Safety: never add `/` as a pathlib root;
only accept a remote URI whose scheme+prefix matches configured
`rawdatadir` or `cellpydatadir`. Invented `scp://evil/…` stays refused.
`cellpy.get` already copies remote → temp.

**cellpy-mcp — `find_cells`**

1. Keep `kind` in `{cellpy, raw}` only. No second tool.
2. `kind=cellpy` + remote `cellpydatadir`: unchanged honesty
   (`found: 0`, `offer_raw: true`, do not walk).
3. `kind=raw`: always call `find_by_project` (local or remote). Local hits
   still go through `sandbox.resolve` (drop outside roots). Remote hits
   skip pathlib resolve; return the URI string from the finder.
4. `kind=raw` result always includes
   `needs_metadata: ["mass", "nominal_capacity"]` (even when empty, so the
   agent does not guess). `offer_raw` is false. `remote` true when
   `rawdatadir` is a URI.

**cellpy-mcp — `load_cell`**

5. If `path` has a remote scheme: allow only when it is under the configured
   `rawdatadir` / `cellpydatadir` URI prefix; pass `filename=` to
   `cellpy.get` without `Path.resolve`. Else `Refused` naming the configured
   remote root.
6. Local paths unchanged (`sandbox.resolve`). Mass / nom_cap unchanged.
7. Existing `collect` + `render` finish the plot; no new plot tool.

**cellpy docs**

8. `mcp.md`: `kind=raw`, `needs_metadata`, prefix-checked remote load; update
   Roots so “URIs are dropped” is no longer absolute for *listing/load of
   configured remotes*.
9. `agent_prompts.md` SAL: Scenario 2 — ask before raw; `kind=raw`; use
   `needs_metadata`; then `load_cell` with user mass/nom_cap; collect; render.
10. One line in `agents.md` / `AGENTS.md` if they still say empty raw is
    “honest found 0” only.

## Files to touch

- `cellpy-mcp/src/cellpy_mcp/cells.py` — raw listing + prefix-checked remote load
- `cellpy-mcp/src/cellpy_mcp/sandbox.py` — small helper for “configured remote
  prefix?” (keep pathlib `resolve` local-only)
- `cellpy-mcp/tests/test_cell_tools.py` — raw local + `needs_metadata`; remote
  list; prefix allow/deny on `load_cell`
- `cellpy-mcp/README.md` — `find_cells` / `load_cell` rows
- `docs/getting_started/mcp.md`, `agent_prompts.md`, maybe `agents.md` / `AGENTS.md`
- `HISTORY.md` (cellpy close)

## Test strategy

- cellpy-mcp: `uv run pytest`. Monkeypatch `find_by_project` and
  `config.paths.*` (same `raising=False` pattern as #1080). No live SFTP.
- cellpy: `uv run pytest -m essential` (docs/HISTORY only). Run
  `check_rtd_latest_links.py` after zensical if the prompt URL changes.

## Open questions

1. **Remote load (a) vs refuse (b).** Plan assumes **(a) prefix-checked**.
   Reply **(b)** if you want list-only remotes and put load under Later.
   Default on Accept: (a).
