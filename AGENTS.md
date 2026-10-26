<!-- BEGIN issue-flow (managed: do not edit this block) -->
# Issue-flow

This project tracks GitHub issues with issue-flow. Each `iflow-*` skill holds its own instructions; read a skill only when it is invoked.

## Running Python

Follow the project's documented toolchain (README, `AGENTS.md`, `pyproject.toml`, `environment.yml`, CI). Never call bare `python`: use the project's runner (`uv run …` by default, `conda run -n <env> …` for conda projects, `poetry run …` for poetry). In a uv project, manage dependencies with `uv add` / `uv remove` / `uv sync`, not `pip`.

## Tracking layout

Under `.issueflows/`:

- `00-tools/` — reusable helper scripts; `README.md` is the index. Check it before writing a one-off helper, and add useful tools back.
- `01-current-issues/` — the focus issue only: `issue<N>_original.md`, `issue<N>_plan.md`, `issue<N>_status.md`.
- `02-partly-solved-issues/` — parked work. `03-solved-issues/` — finished work.
- `04-designs-and-guides/` — durable design docs; `this-project.md` is the project brief.
- `05-epics/` — staged epic plans (`epic<N>_plan.md`).

- After each iteration, update `issue<N>_status.md` (done, current state, remaining work) with an explicit checkbox: `- [x] Done` when fully resolved, `- [ ] Done` otherwise. Other steps route files by that checkbox.
- Finished issues move to `03-solved-issues/`, unfinished ones to `02-partly-solved-issues/`.
- Before planning or building, read `04-designs-and-guides/this-project.md` if present and skim `04-designs-and-guides/` for relevant docs. Record non-trivial design decisions there (context, decision, alternatives, issue link).

## Commands

Invoke as `/iflow-<step>` or in chat as `iflow <step> [args]` (also `iflow-<step>` or `/iflow <step>`). A message that **starts with** one of these forms invokes the `iflow-<step>` skill with the trailing text as its arguments; plain `iflow` runs the dispatcher. Mid-sentence mentions are not invocations.

| Command | Purpose |
|---|---|
| `iflow` | Dispatcher: run the next of capture / plan / build / close. |
| `iflow-setup` | Get a project ready (uv, git, GitHub, scaffold). |
| `iflow-pick` | Choose an issue, branch, and capture it. |
| `iflow-plan` | Write the plan and stop for approval. |
| `iflow-build` | Implement the approved plan. |
| `iflow-pause` | Park unfinished work with resume notes. |
| `iflow-close` | Tests, bump, changelog trailers, commit, push, PR. |
| `iflow-cleanup` | After merge: default branch, pull, delete landed branches. |
| `iflow-run` | Hands-off runs under one up-front confirm. |
| `iflow-issue` | Create and shape GitHub issues. |
| `iflow-status` | Read-only overview of every issue. |
The core loop is `pick → plan → build → close → cleanup`. `/iflow` detects the focus issue's state and dispatches to the next of capture / plan / build / close; it never dispatches to any other command. Never skip the plan confirmation in `/iflow-plan` unless a hands-off mode was confirmed.

Issue labels can route `/iflow-pick`: `yolo` → `/iflow-run yolo`, `ops` → no-PR close (ops wins over yolo). A `publish` label makes `/iflow-close` bump the version and release after merge.

## Branch hygiene

- Work on an issue branch `<N>-<short-slug>`, never on the default branch.
- Before continuing a branch, run `git fetch --prune` and check ahead/behind against `origin/<default>`. PRs are **squash**-merged, so a merged branch looks "ahead" and is stale.
- An issue already under `02-partly-solved-issues/` or `03-solved-issues/` has a stale branch. Re-open it only on purpose with `/iflow-pick <N>`.

## Multi-repo workspaces

When the workspace holds several repos with their own `.issueflows/`, resolve the target repo first (`root:` / `repo:` hints, then `issue-flow agent resolve`, then the `issueflow-workspace.toml` default); ask when ambiguous. Pass `--repo <owner/repo>` to every `gh` call. Lifecycle state is per repository.

## Optional skills

- **caveman** — terse response style. **On by default here**: reply in caveman style from the first message of every session. Off with "stop caveman" / "normal mode". Code, commits, PRs, security warnings, and destructive-action confirmations are always normal prose.
- **grill-me** — relentless one-question-at-a-time planning interview. Off until the user asks ("grill me"). Off with "stop grilling".

## Knowledge graph

If `graphify-out/GRAPH_REPORT.md` exists, skim it before grepping. Run `graphify query` / `path` / `explain` only when `graphify-out/graph.json` exists. `/iflow-status graph` rebuilds the graph; nothing runs it automatically.


<!-- END issue-flow (managed) -->

## Using cellpy (for agents)

Coding agents that **call cellpy as a library** (e.g. a researcher’s small
GUI/app around cycling data) should read the usage chapter:

**[`docs/agents/index.md`](docs/agents/index.md)**
(site-root indexes: [`llms.txt`](https://cellpy.readthedocs.io/en/latest/llms.txt),
[`llms-short.txt`](https://cellpy.readthedocs.io/en/latest/llms-short.txt))

To wire Cursor or another MCP client (no Python in the chat), see
[`docs/agents/mcp.md`](docs/agents/mcp.md). Asked to
"install cellpy MCP and test it": follow that page's *Ask your agent to do
it* checklist — `cellpy mcp install --client cursor`, then
`cellpy mcp check --client cursor` proves the registered command answers
MCP (exit 1 = broken, with the reason); the user must restart Cursor after.
Ready-made paste prompts (MCP, load, batch, plot, ICA, …):
[`docs/agents/prompts.md`](docs/agents/prompts.md).

Quick facts:

- Product: Python library + `cellpy` CLI — not a hosted GUI server.
  Third-party CLI commands: `[project.entry-points."cellpy.cli_plugins"]`.
- Portable figure: `from cellpy.plotting.bundle import save_bundle` then
  `save_bundle(c, kind="cycles", path="cell.cfz")` (`summary`, `ica`, `dva`
  too). Needs the `plotting-mpl` or `batch` extra (`cellpy-figure` 0.1.0).
  A coauthor redraws the file with cellpy-figure, not cellpy.
- Entry: `import cellpy` then `c = cellpy.get(path, mass=..., instrument=...)`.
  For raw `.h5`/`.hdf5`, a set `instrument=` wins over native suffix auto-pick.
- Find by project + number range: `from cellpy import filefinder` then
  `filefinder.find_by_project("SAL", 10, 15, kind="cellpy")` (or `kind="raw"`).
  Uses `cellpydatadir` / `rawdatadir`; empty list if none match.
  MCP: `find_cells` (empty cellpy → `offer_raw`, no silent raw crawl;
  `kind=raw` lists raw and sets `needs_metadata`).
- Metadata peek (no frames): `cellpy.read_meta(path)` → dict with `cell` / `tests`.
- Ingestion form fields: `cellpy.instrument_meta_schema(instrument)` → `fields` / `units`.
- Live/running test: `c.update()` re-reads only the new raw rows (incremental
  loaders) or reloads fully, returns `True` when frames changed; `False` if
  the raw file did not change on disk. Also works after `cellpy.get(".cellpy")`.
  Follow on an interval: `cellpy.utils.live.poll(c, interval=60, on_update=cb)`;
  batch: `b.refresh()` / `b.poll(interval=, on_update=)`.
- External metadata (lab DB / BatBase): `c.fetch_meta("batbase", key=None,
  kind="cell_name")` pulls mass / area / nominal capacity / project onto the
  cell like a journal row and records `c.external_links["batbase"]`;
  unreachable source ⇒ `()` and no change (`strict=True` raises). Sources:
  `cellpy.readers.metadata_sources.names()`; the BatBase adapter is in
  `cellpy-connectors`. No filename needed when the source knows the files:
  `cellpy.get(source="batbase", key="SAL_010", kind="tag")` opens the
  record's file pointers (`filefinder` only as fallback);
  `batch.from_source("batbase", "SAL_010")` does the same for a whole tag.
  Raw pointers with `size`/`mtime` stay on `external_links[src].file_refs`;
  `update()` / `refresh()` skip the remote `stat` while they match what was
  loaded (`force=True` or a differing value → stat/reload as usual).
- Frames: `c.data.raw` / `.steps` / `.summary`; columns via `c.schema.*`.
  After a raw load, each cycle's raw capacity starts at 0. A forgotten tester
  reset that 1.x plotted as doubled capacity is rebased on load for every
  loader; a `UserWarning` names the columns and how many cycles carried over
  (#989). `.cellpy` files written by cellpy ≤ 2.1.5 keep the un-rebased raw;
  regenerate them from raw (`batch.load(..., force_raw_file=True)`).
- Example data: `from cellpy.utils import example_data` → `example_data.raw_file()`.
- ICA/DVA: `from cellpy import ica` then `ica.dqdv(c)` / `ica.dvdq(c)`.
  Recipe: `opts = ica.IcaOptions(...)` then `options=opts` (or one-off kwargs).
  Plot: `from cellpy.utils.plotutils import ica_plot, dva_plot`.
  Multi-cell: `collect_ica(batch, options=opts, cycles=...)` — same recipe.
  A cell with no cycle curve is skipped: `UserWarning` names it, and
  `meta.cells_included` / `meta.cells_skipped` record who stayed and who
  dropped (`collect_dva` too). `dqdv` / `dvdq` on that cell alone still raises.
  How-to: [`docs/guides/ica.md`](docs/guides/ica.md).
- Batch: `batch.load(name=..., project=...)`; `executor="threads"` speeds up
  reopening local `.cellpy` files (first remote load stays serial on the wire).
  `progress=None` auto-shows tqdm (TTY / Jupyter); `False` off.
  An existing `cellpy_batch_<name>.json` in cwd/`journal_dir` is reused and
  the db is not re-read (warns when db args were passed);
  `allow_from_journal=False` rebuilds from the db. A configured `db_cols`
  header missing from the sheet warns once (values become empty).
  After load: `b.summaries`, `b.cells[label]`, `b.plot()`, `b.result.report()`.
  Text in the cellpy_db `group` column becomes journal `group_label` (default
  legend for `summary_collector(..., group_it=True)`); `custom_group_labels=`
  still overrides. Numeric group ids stay unlabeled.
  `b.plot(ir=True, direction="discharge")` uses `ir_discharge`, or `ir_charge`
  with a warning if that column is missing. A normal `cellpy.get` /
  `batch.load` summary includes those columns (`find_ir=True`).
  `summary_collector(b, family=...).plot()` puts charge and discharge of one
  quantity in the same panel. Both on that panel: charge solid, discharge
  dashed, plus a "Direction" legend. Only one of them: solid line, no
  Direction legend. `combine_directions=False` gives one facet per variable.
  `mark_as_bad` is a session flag (unknown cell name → `ValueError`); `drop` /
  `drop_cells_marked_bad` remove now
  (plot/summaries work without `update()`). `save()` then next `load` (default
  `drop_bad_cells=True`) drops marked cells before update. Journal JSON has a
  top-level `version` (missing means 1; this cellpy writes 1). Missing raw files
  (filefinder miss) mark the cell `FAILED` and warn; see `b.result.report()`.
- In-memory batch: `from_cells({label: cell})` takes cells, not paths — a
  non-cell value raises `ValueError` naming the offending keys. When
  `collect_summaries` leaves a cell out (no summary, or filtered away) it
  warns and names it; `collection.meta.cells_included` is authoritative.
- Persist: `c.save("out.cellpy")`, `c.to_csv("out_dir")`.
    Collected figure bytes: `collection.to_image("png")` / `cellpy.plotting.write_image(fig, "svg")` (needs `cellpy[batch]` / kaleido). Matplotlib plots need `cellpy[plotting-mpl]` (#937).
- Prefer schema-resolved names over hard-coded 1.x header strings.
- When changing public get/save/schema/CLI surface, update
  `docs/agents/index.md` and this section in the same PR.

## Local toolchain

Day-to-day: `uv sync`, then `uv run pytest` / `uv run pytest -m essential` /
`uv run cellpy …`. Do **not** use conda for local pytest unless the issue is
specifically conda-forge install, `environment*.yml`, or scheduled CI conda
jobs. That overrides the generic issue-flow "if conda is documented" block
above. Detail: `.issueflows/04-designs-and-guides/this-project.md`.

## Cursor Cloud specific instructions

Environment is already provisioned on cloud VM startup: `uv` (on PATH via
`~/.local/bin`), the `mdbtools` system package (needed to read Arbin `.mdb`/`.res`
files on Linux), and the startup update script runs `uv sync`, which installs
Python 3.13 and the project + `dev` dependency group from `uv.lock` (`cellpycore`
resolves from PyPI). No manual install is normally needed.

- **Product:** `cellpy` is a Python library + `cellpy` CLI for battery/cell cycling
  data (no web/GUI server; `cellpy serve` only launches Jupyter). There is nothing
  long-running to "start" — you exercise it via the CLI or by importing the library.
- **Run everything through `uv run`** (e.g. `uv run cellpy ...`, `uv run pytest`,
  `uv run python ...`, `uv run issue-flow …`) so the `.venv` interpreter and deps
  are used. The `issue-flow` CLI is in the `dev` dependency group (no separate
  `uv tool install` needed after `uv sync`). Standard commands are in
  `CONTRIBUTING.md`, `.github/workflows/ci.yml`, and `pyproject.toml`.
- **Tests:** `uv run pytest -m essential` is the fast CI merge gate. Plotting tests
  run under `MPLBACKEND=Agg` (no file `--ignore` in Tier 1 / scheduled / release).
  Full suite is `uv run pytest` (default `addopts` deselects slow/local/unfinished
  markers).
- **Lint/format:** `uv run flake8 src/cellpy` and `uv run black --check src/cellpy` (line
  length 120). These are not wired into the Tier-1 CI gate, and the repo currently
  has pre-existing `black` reformat suggestions and some `flake8 F821` findings —
  do not treat those as regressions from your change.
- **Build:** `uv build` (hatchling; version derived from git tags via
  `uv-dynamic-versioning`, so a shallow/tagless checkout reports a `0.0.0`-style dev
  version — harmless for dev).
- **CLI smoke check:** `uv run cellpy setup --silent` then `uv run cellpy info --check`.
  `cellpy setup` writes a runtime `.env_cellpy` and a user `cellpy.toml`
  (legacy installs may still have `~/.cellpy_prms_*.conf`) and creates any
  missing configured local folders (remote path URIs are skipped) — these
  are local runtime files, do not commit them.
- **Example data** (`cellpy.utils.example_data`, e.g. `raw_file()`) downloads small
  fixtures from GitHub on first use, so those helpers need network access.
- **Dual-repo dev** with a sibling `../cellpy-core` checkout is optional (see
  `CONTRIBUTING.md`): `uv sync --no-sources` then `uv pip install -e ../cellpy-core`.
  The default `uv sync` uses the PyPI `cellpycore` pin and is sufficient for most work.
