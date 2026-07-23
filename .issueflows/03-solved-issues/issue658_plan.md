# Issue #658 — Plan

## Goal

Wire `Batch.plot()` into `cellpy.plotting` (multi-cell cycle-life summary:
capacity + CE + optional IR/rate panels), delete
`cellpy/utils/batch_tools/batch_plotters.py`, and document backend triage —
without breaking the batch facade (`b.plot(...)`, `b.plotter.figure`).

## Constraints

- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.3–3.4 /
  Phase 4–5; batch hand-off `architecture-plan/cellpy2-batch-redesign-plan.md` §4.7.
- Epic #567 Stage 3: one drawing home; `#657` already re-based collectors —
  **do not rework collectors collection**.
- **Not** single-cell `summary_plot(cell, …)`: today's `Batch.plot` draws the
  multi-panel cycle-life figure from `plot_cycle_life_summary_plotly` (and
  friends). Issue text allows “or equivalent” — relocate that figure path into
  plotting; redesign-plan line `summary_plot(b, …)` is the long-term shape,
  not a force-fit of the CellContext prepare path this PR.
- Backend policy (epic + §4.7): `plotly` primary; `matplotlib` kept for
  print/CLI; bare `seaborn` not a public backend; `bokeh` dies.
- Parity: extend figure-spec snapshots with ≥1 batch-input cycle-life case;
  keep `tests/test_figure_specs.py` / collector snapshots green.
  `MPLBACKEND=Agg` for plotting tests.
- Facade: `b.plotter.figure` / `.fig` / `.figures` (and `_pb_save_plot` farms
  loop) stay usable; no farm/engine/dumper vocabulary required underneath.
- Docs: `DEPRECATIONS.md` (via `warn_once` registry) + migration /
  `docs/api/plotting.md` mention backend triage and module removal.

### Prior art

- `Batch.plot` / `plot_summaries` / `self.plotter = CyclingSummaryPlotter()` —
  [`cellpy/utils/batch.py`](cellpy/utils/batch.py) (~L36, L171, L1365–1498).
  **Migrate** draw callee; keep `summary_collector.do` for data.
- Frame prep + renderers —
  `generate_summary_frame_for_plotting`, `plot_cycle_life_summary_{plotly,matplotlib,seaborn,bokeh}`,
  `summary_plotting_engine` —
  [`cellpy/utils/batch_tools/batch_plotters.py`](cellpy/utils/batch_tools/batch_plotters.py).
  **Move** plotly (+ matplotlib) into plotting; **delete** bokeh/seaborn
  engines with the module.
- `#657` orchestrator —
  [`cellpy/plotting/collected.py`](cellpy/plotting/collected.py)
  (`collected_plot` / `summary_plotter`). **Coexist** for collector frames;
  Batch cycle-life layout is a **separate** entry (do not pretend
  `BatchSummaryCollector` + `collected_plot` already match CE/IR/rate
  panel defaults).
- Labels / theme already single-copy —
  [`cellpy/plotting/labels.py`](cellpy/plotting/labels.py)
  (`inverted_mode`), [`theme.py`](cellpy/plotting/theme.py). **Reuse**.
- Oracle helpers —
  [`tests/figure_spec_support.py`](tests/figure_spec_support.py),
  [`tests/test_collectors.py`](tests/test_collectors.py)
  (`collector_figure_specs.json`). **Mirror** for a batch `Batch.plot` case
  (new key in `figure_specs.json` and/or a small batch snapshot beside
  collectors).
- Re-export identity tests —
  [`tests/test_plotting_package.py`](tests/test_plotting_package.py)
  (imports `batch_plotters`). **Delete/rewrite** those assertions.
- Toolbox (`00-tools/`): nothing for batch figures. Graph: no
  `GRAPH_REPORT.md` in this checkout (grep-only).

## Approach

**Relocate the cycle-life summary path into `cellpy.plotting`, thin-wire
`Batch.plot`, then delete `batch_plotters.py`.**

### 1. Plotting entry for batch summaries

- Add something like `cellpy.plotting.batch_summary_plot(frame, *, backend=…, **opts)`
  (name bikeshed OK; export from `cellpy.plotting` / re-export via plotutils if
  other public plots are re-exported there).
- Move (mechanical) from `batch_plotters.py`:
  - `generate_summary_frame_for_plotting` + `_get_capacity_columns` / label helpers
    still needed by that path
  - `plot_cycle_life_summary_plotly` (primary)
  - `plot_cycle_life_summary_matplotlib` (kept per §4.7)
- Do **not** port bokeh (~575 lines) or seaborn cycle-life engines.
- Prefer calling existing `labels.legend_replacer` / `theme.make_plotly_template`
  (already aliased inside batch_plotters today).
- Optional thin adapter: accept `experiment` + kwargs and build the melted
  frame internally so `Batch.plot` stays small.

### 2. Wire `Batch.plot`

- Drop `from … batch_plotters import CyclingSummaryPlotter`.
- Replace `self.plotter` with a tiny holder (local class or `SimpleNamespace`)
  exposing `.figure` / `.fig` / `.figures` (and `.farms` alias if
  `_pb_save_plot` still needs it).
- Flow:
  1. `summary_collector.do(reset=True)` when needed (unchanged gate on
     `memory_dumped["summary_engine"]`).
  2. Resolve `backend` (config default; see triage below).
  3. Build tidy frame → `batch_summary_plot(...)`.
  4. Stash canvas on `self.plotter`.
- `plot_summaries` stays a `DeprecationWarning` shim → same path as `plot`
  (no bokeh notebook/`output_file` special-case).

### 3. Backend triage

| Input | Behaviour |
|---|---|
| `None` / `"plotly"` | plotly cycle-life (primary) |
| `"matplotlib"` | matplotlib cycle-life |
| `"seaborn"` | `warn_once` → treat as `"matplotlib"` (**confirmed**) |
| `"bokeh"` | **clear error** (`ValueError`) naming `backend="plotly"` / `"matplotlib"` |
| other | clear error listing allowed names |

Also stop rewriting config default `bokeh`/`matplotlib` → plotly silently in
`plot()` except where a deprecation warning documents the old override;
prefer explicit triage table above. Persist `config.batch.backend` only for
supported names.

### 4. Delete module + clean call sites

- Delete `cellpy/utils/batch_tools/batch_plotters.py`.
- Grep-clean imports/docs: `docs/api/plotting.md`, folder-structure docs,
  `plotutils` comments, `__init__` package docs that claim batch_plotters
  re-exports.
- Update `tests/test_plotting_package.py` (drop batch_plotters identity
  checks; keep `inverted_mode` coverage on `labels`).

### 5. Oracle + docs

- Add ≥1 batch-input snapshot case covering the cycle-life figure
  (n_traces / n_axes style, same helper as collectors).
- Register any `warn_once` aliases; regenerate `DEPRECATIONS.md`.
- Short note in `docs/getting_started/migration_v1_to_v2.md` (plotting /
  batch section): bokeh removed; seaborn not a Batch backend; use
  `backend="plotly"|"matplotlib"`.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/` (new module e.g. `batch_summary.py` + `__init__` exports) | Relocated frame prep + plotly/matplotlib cycle-life renderers; public entry |
| `cellpy/utils/batch.py` | Drop CyclingSummaryPlotter; rewire `plot` / `plot_summaries`; thin plotter holder |
| `cellpy/utils/batch_tools/batch_plotters.py` | **Delete** |
| `cellpy/utils/plotutils.py`, `cellpy/plotting/{__init__,labels,theme}.py` | Doc/comment cleanup; drop batch_plotters re-export mentions |
| `tests/test_plotting_package.py` | Remove batch_plotters import tests |
| `tests/figure_spec_support.py` and/or `tests/test_batch*.py` / `test_collectors.py` | Batch cycle-life snapshot + assert |
| `tests/data/figure_specs.json` (and/or sibling batch snapshot) | New case |
| `DEPRECATIONS.md`, `docs/getting_started/migration_v1_to_v2.md`, `docs/api/plotting.md` | Backend triage + module gone |
| Dev folder-structure docs that list `batch_plotters.py` | Remove line |

## Test strategy

- `uv run pytest -m essential` (merge gate).
- Focused: `MPLBACKEND=Agg uv run pytest tests/test_plotting_package.py tests/test_figure_specs.py tests/test_collectors.py` (+ new batch-plot snapshot test).
- Grep gate: no in-tree `batch_plotters` / `CyclingSummaryPlotter` imports remain (docs history / `.issueflows` archives OK).
- Manual sanity (optional): populated batch → `b.plot()` → `b.plotter.figure` is non-`None`.

## Open questions

_None — confirmed 2026-07-23:_

1. `seaborn` → `warn_once` → **matplotlib**.
2. Port `plot_cycle_life_summary_matplotlib` **in this PR**.

**Status:** Accepted — ready for `/iflow-build`.
