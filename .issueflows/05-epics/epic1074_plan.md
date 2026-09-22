# Epic #1074: Agent summary-plots SAL cells 10–15 from local files

Anchor: https://github.com/jepegit/cellpy/issues/1074
Status: confirmed

## Goal

An agent with cellpy configured (and cellpy-mcp installed) can answer:
“summary-plot project SAL cells named `<date>_SAL<number>`, numbers 10–15.”

Done when both scenarios work without the user writing Python or naming folders:

- **Cellpy files present** under `config.paths.cellpydatadir`: only SAL 10–15
  are loaded and a cellpy summary plot is written.
- **None present:** the agent says so and offers a raw search (no silent
  crawl). After “yes”, it searches `config.paths.rawdatadir` (may be an
  `OtherPath`), reports hits, asks for metadata, then loads with the user’s
  mass ≈ 2.1 mg and nominal capacity ≈ 320 mAh/g and plots.

## Constraints

- **Local files first.** No BatBase, no #784, no #1072/#1073 session setup.
  Do not invent mass or nominal capacity.
- **Paths from config.** `cellpydatadir` / `rawdatadir` (see
  [this-project.md](../04-designs-and-guides/this-project.md) agent-docs rule:
  public surface changes update `docs/getting_started/agents.md` + root
  `AGENTS.md` in the same PR).
- **Reuse, do not replace.** `filefinder.find_in_raw_file_directory` /
  `OtherPath.rglob` ([otherpath-upath.md](../04-designs-and-guides/otherpath-upath.md));
  `cellpy.get(mass=…, nominal_capacity=…)`; MCP `load_cell` / `collect` /
  `render` ([plotting-collected.md](../04-designs-and-guides/plotting-collected.md)).
- **MCP sandbox today drops remote roots** ([mcp-check.md](../04-designs-and-guides/mcp-check.md),
  cellpy-mcp `sandbox.py`). Library find must still work on `OtherPath`.
  Teaching the sandbox to *load* remote raw is Stage 3, not a silent
  `pathlib` cast.
- **Huge trees.** Do not walk a whole shared projects root by default
  (issue #690). Prefer the configured dir; optional `project_dir=` subdirectory
  later (#691), not this epic.
- **Two repos.** Plan and GitHub children live on `jepegit/cellpy`. Library
  PRs are here; MCP PRs are in `cellpy/cellpy-mcp` and link back to the child.
- **Number range is inclusive** (10 and 15 both match). Project token is
  case-insensitive (`SAL` / `sal`). Pattern is `<date>_<project><number>` plus
  optional suffix (e.g. `_cc.cellpy`).

## Stage 1 — Find by project and number range

Retire the naming and config-path risk before any agent tool exists. Empty
results are data, not exceptions — Scenario 2 depends on that.

- Goal: library can list matching cellpy or raw paths from config, including
  `OtherPath`, without loading files or crawling raw when asked for cellpy.

### Issue: Parse `<date>_<project><number>` cell filenames

- Spec: Add a small helper (home: `cellpy.readers.filefinder`, already in the
  sanctioned `cellpy.filefinder` surface) that takes a filename or stem and a
  project token and returns the integer run number, or `None` if the stem does
  not match `<date>_<project><number>` with an optional trailing suffix
  (`_cc`, instrument tag, extension). Match the project token
  case-insensitively. Examples that must work: `20240922_SAL12`,
  `20240922_SAL12_cc.cellpy`, `20240922_sal15.res`. Examples that must miss:
  `20240922_SAL9` when asking for project `BAT`, `notes_SAL12.txt` if the
  date prefix is required, `20240922_SALAMANDER12` when the token is `SAL`
  (do not treat a longer word as `SAL`). Tests only — no I/O, no config.
- Goal: given a stem and project token, get a run number or a clear miss.
- Model: fast
- Depends on: none
- yolo: yes — mechanical parser, isolated tests, no product surface change
- Published: #1075

### Issue: Find cellpy or raw files by project and number range

- Spec: Public `filefinder` function (name bikeshed in the issue plan; do not
  add a new top-level `cellpy.find_cells` unless the plan argues for it)
  that takes `kind` (`cellpy` | `raw`), `project`, inclusive `number_min` /
  `number_max`, and optional override roots. Default roots come from
  `config.paths.cellpydatadir` or `config.paths.rawdatadir`. Walk with the
  existing `OtherPath` / `files_only` rglob used by
  `find_in_raw_file_directory` — do not reimplement a local-only `Path.rglob`.
  Filter with the Stage 1 parser. Return a structured list of `{path, name,
  number}` (and kind). Zero matches is an empty list, not an error. Do not
  load cells, do not write files, do not search the other kind when the first
  is empty. Warn (existing #690 threshold) if the walk is huge. Unit tests
  on a tmp tree; one OtherPath/local-equivalent test is enough if a remote
  fixture is not cheap.
- Goal: `kind="cellpy", project="SAL", 10..15` lists only those files under
  `cellpydatadir`; same call on an empty dir returns `[]`.
- Model: deep
- Depends on: stage 1 issue 1
- yolo: no — public API, OtherPath walk, empty-vs-error contract
- Published: #1076

## Stage 2 — Scenario 1 through the agent

The library can find; the agent still cannot. Add one MCP tool that lists
matches from configured dirs and **stops**. Existing `load_cell` / `collect` /
`render` finish the plot. No raw crawl in this stage.

- Goal: with local `.cellpy` files on disk, an agent completes Scenario 1
  without the user naming a folder.

### Issue: MCP find_cells tool (no silent raw crawl)

- Spec: In `cellpy-mcp`, add a tool (suggested `find_cells`) that calls the
  Stage 1 finder. Inputs: `project`, `number_min`, `number_max`, `kind`
  defaulting to `cellpy`. Output: handles/facts only — count, names, numbers,
  paths the sandbox may read. If `kind=cellpy` and the list is empty, return
  `{found: 0, offer_raw: true}` (or equivalent) and **do not** search
  `rawdatadir`. If `cellpydatadir` is a remote URI, say so (`remote: true`,
  reason) rather than pretending the sandbox can walk it. Update
  `docs/getting_started/agents.md` / MCP chapter and add a short agent-prompt
  snippet for “summary-plot SAL 10–15” that uses find → load → collect →
  render. Implement in the `cellpy-mcp` repo; this GitHub issue stays the
  tracker on `jepegit/cellpy`.
- Goal: MCP `find_cells(project="SAL", 10, 15)` returns the matching local
  cellpy files, or a structured empty + `offer_raw` — never a raw listing.
- Model: default
- Depends on: stage 1 issue 2
- yolo: no — tool contract and sandbox/remote honesty
- Published: #1080

## Stage 3 — Scenario 2: offer raw, then rough-view load

Only after Stage 2’s empty shape exists. Two small issues so the mechanical
`nominal_capacity` pass-through is not stuck behind OtherPath design.

- Goal: “no cellpy files” → user says search raw → hits + “need metadata” →
  user gives ~2.1 mg and ~320 mAh/g → load + summary plot.

### Issue: Pass nominal_capacity through MCP load_cell

- Spec: `cellpy.get` already accepts `nominal_capacity`. MCP `load_cell`
  only forwards `mass_mg`. Add an optional `nominal_capacity` (and pass
  through as `nominal_capacity=`, same units story as `cellpy.get`: number
  uses cellpy units, string may carry a unit). Return the applied value and
  whether it was supplied (mirror `mass_was_supplied`). Do not default a
  lab-looking capacity. Tests in cellpy-mcp. No finder work.
- Goal: `load_cell(..., mass_mg=2.1, nominal_capacity=320)` reaches
  `cellpy.get`; omitting it leaves cellpy’s default.
- Model: fast
- Depends on: none
- yolo: yes — one-parameter pass-through, existing get() contract

### Issue: MCP raw search after confirm, including OtherPath

- Spec: Extend `find_cells` (or add `find_raw_files`) so raw is searched
  **only** when the caller sets `kind=raw` (or an explicit confirm flag).
  Use the Stage 1 finder so `rawdatadir` may be `OtherPath`. Report hits
  (names, numbers, path/URI). Include a structured `needs_metadata: ["mass",
  "nominal_capacity"]` so the agent asks instead of guessing. If the URI is
  remote, either (a) return the URIs and load via `cellpy.get`/`OtherPath`
  without widening the pathlib sandbox to `/`, or (b) refuse load with a
  message that names the remote root — pick (a) if a narrow “this path came
  from `config.paths.rawdatadir`” allowance is safe; otherwise (b) and put
  remote *load* under Later. Local raw must load with the user’s mass and
  nom_cap and then `collect`+`render` a summary plot. Prompt/docs: the
  Scenario 2 dialogue. Implement in `cellpy-mcp`; tracker on this repo.
- Goal: after an explicit raw ask, the agent lists matching raw files, says
  it needs mass and nominal capacity, and (for local raw) plots a rough view
  once those are given.
- Model: deep
- Depends on: stage 2 issue 1; stage 3 issue 1
- yolo: no — confirm-gated crawl, OtherPath vs sandbox

## Later (unstaged)

- Remote raw *load* if Stage 3 chose refuse-and-report only.
- Project-scoped raw walk (#691) when `rawdatadir` is a shared projects root.
- Replayable Python for this session (belongs with #1072, not here).
- Replacing user-supplied mass/nom_cap with BatBase metadata (#784 / #1073).
- Hard-link this prompt into the #1064 agent-prompt catalog if the snippet
  should live on RTD latest.
