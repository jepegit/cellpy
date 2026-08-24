# Issue #940 — plan

## Goal

Bring the `examples/` tutorial notebooks (and the `cellpy.get` docstring examples)
in line with the 2.1 native schema and public APIs so a reader can run them
without `KeyError` / missing-import / missing-file failures.

## Constraints

- One maintained notebook copy: top-level `examples/*.ipynb`. Docs pages under
  `docs/examples/` are generated — after notebook edits re-run
  `uv run --group docs python dev/render_example_notebooks.py` and commit the
  output ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md),
  [dev_docs.md](../../docs/contributing/developers_guide/dev_docs.md)).
- Prefer `c.schema.raw` / `.steps` / `.summary` over hard-coded 1.x names
  ([migration_v2.0_to_2.1.md](../../docs/getting_started/migration_v2.0_to_2.1.md),
  [agents.md](../../docs/getting_started/agents.md)).
- `plotutils.summary_plot(y=...)` only accepts registered families
  ([plotting-registry.md](../04-designs-and-guides/plotting-registry.md)).
  Unknown `y` raises `ValueError`.
- `get_cap` frame columns are `potential` / `cycle_num` / `capacity` /
  `direction` — not `voltage` / `cycle`
  ([migration_v1_to_v2.md](../../docs/getting_started/migration_v1_to_v2.md) § get_cap).
  ICA output from `ica.dqdv` still uses `voltage` / `cycle` — leave those plots.
- Do not add new example data files unless a notebook cannot run without them.
- Out of scope: cookiecutter template, `examples/batch_utility/` (already 2.1),
  `04_incremental_capacity_analysis.ipynb` (already 2.1), plotutils / schema
  implementation (notebooks adapt to current API).
- Keep notebook source edits small. Do not invent new tutorial content.

### Prior art

- `dev/render_example_notebooks.py` — committed-markdown renderer; does **not**
  execute notebooks. Reuse after source edits.
- `dev/backfill_notebook_plotly_pngs.py` — static PNG from stored Plotly JSON
  if a page would otherwise have no figure.
- `cellpy.utils.example_data` — downloadable fixtures (`cellpy_file()`,
  `pec_file_path()`, `maccor_file_path()`, …). `03` / `04` / `06` / `07`
  already use it; `01` / `02` / `05` still point at a local `20210210_FC.h5`.
- `cellpy.list_instruments()` / `cellpy.print_instruments()` — public listing.
  `cellpy.readers.data_structures.find_all_instruments` /
  `instrument_configurations` replace `cellpy.readers.core` (module gone).
- `00-tools/` scanners (`scan_hardcoded_headers.py`, …) — inventory helpers,
  not needed for this notebook pass.
- Graph: `graphify-out/` not present — skipped.

## Approach

Fix the issue's listed breakages, then a light sweep of the other numbered
tutorials for the same class of 1.x names. Recommended defaults below; flagged
items sit in **Open questions**.

### Shared column / API map (use everywhere)

| Old (notebook) | Now |
|---|---|
| `from cellpy.readers import core` | `from cellpy.readers import data_structures` (or `cellpy.list_instruments()`) |
| `cell.schema.*` when the object is `c` | `c.schema.*` |
| `raw["voltage"]` / `y="voltage"` on `get_cap` frames | `c.schema.raw.potential` / `"potential"` |
| `steps["type"]` / `"cycle"` / `"step"` / `"voltage_first"` | `c.schema.steps.step_type` / `.cycle_num` / `.step_num` / `.potential_first` (and `datapoint_num_*` for point min/max — resolve from `c.schema.steps` at implement time) |
| `get_cap` groupby `["cycle", …]` | `["cycle_num", …]` |
| `summary_plot(y="shifted_discharge_capacity_gravimetric")` | a registered family (`"capacities_gravimetric"` or `"capacities_gravimetric_coulombic_efficiency"`) |
| `summary_plot(y="capacities")` | keep — `"capacities"` is a registered family |
| `filedir / "out" / "20210210_FC.h5"` | probe `data/20210210_FC.h5` then `data/out/20210210_FC.h5`; if neither exists, fall back to `example_data.cellpy_file()` **except** in `05_GITT` (see open question) |

### Per notebook

1. **`02_Initial_data_inspection.ipynb`** — path probe; replace the shifted-discharge
   `summary_plot`; update the listed family names to the current registry
   (include `*_coulombic_efficiency`, `*_absolute`, `*_with_rate`,
   `fullcell_standard_*`). For `cycle_info_plot(..., cycle=[7,8,9])`, pick
   cycles that exist (`list(c.get_cycle_numbers())[:3]` or similar) so missing
   cycles are a data issue, not a silent empty plot.

2. **`03_capacity_vs_voltage.ipynb`** — `px.line(..., y="voltage")` →
   `y="potential"`; `color="cycle"` → `color="cycle_num"`. Refresh the pasted
   `get_cap` signature block only if it is still wrong after that. Keep
   `example_data.cellpy_file()`.

3. **`05_GITT.ipynb`** — source already uses `cycle_num` / `step_type` /
   `potential_*`. Fix the load path. Keep hardcoded GITT cycle `5` only if that
   cycle exists in the loaded file; otherwise document the cycle used.
   `cycle_info_plot` range must match cycles present in the file.

4. **`06_loading_different_formats.ipynb`** — replace `cellpy.readers.core`
   with `cellpy.readers.data_structures` (`find_all_instruments`,
   `instrument_configurations`). Leave `summary_plot(..., y="capacities")`.

5. **`08_batmo_bdf.ipynb`** — `r = c.schema.raw` (object is `c`); steps subset
   via `c.schema.steps`; raw plot `raw[c.schema.raw.potential]` (not
   `"voltage"`); `get_cap` plot uses `cycle_num` + `potential`. Keep the
   testdata / examples path probe for `batmo_bdf.csv`.

6. **`09_loading_pec_data.ipynb`** — rename `cell` → `c` for consistency;
   move `#` narration into markdown cells so it matches 01–08. Logic already
   uses `schema.raw`.

7. **`01_loading_data.ipynb`** — teaching notebook for local `.res` → save.
   Keep that story. After `c.save(...)`, load via the same path probe as 02
   (`data/` then `data/out`) so a reader who already has the `.h5` in `data/`
   is not sent looking in `out/`. Do not require the Arbin `.res` files in-repo.

8. **`07_custom_loaders.ipynb`** — light check only (already uses
   `example_data` + `plotutils`). Fix only if the same class of breakage appears.

### `cellreader.py` `get()` examples

Update the `Examples:` block on `cellpy.readers.cellreader.get`:

- `"my_cellpy_file.clp"` → `"my_cellpy_file.cellpy"` (same for the
  `cellpy_file=` pair).
- Prefer `nominal_capacity=` in the first example (`nom_cap` still aliases,
  but the public parameter is `nominal_capacity`).
- Keep instrument names (`arbin_res`, `maccor_txt`) — those are current.

If `docs/getting_started/agents.md` / the short AGENTS.md snippet already match,
leave them. This change is docstring-only.

### Docs render

After notebook source + output cells are updated, run
`dev/render_example_notebooks.py` and commit `docs/examples/*.md` (and any
figure dirs). Update the note on `docs/examples/index.md` that most tutorials
are still 1.x once 02/03/05/06/08/09 are current.

### Execution / outputs

Recommended: execute the notebooks that have in-repo or `example_data`
fixtures (`03`, `06`, `07`, `08`, `09`; `02`/`05` if the local `.h5` is
present) with `MPLBACKEND=Agg`, then save. Do **not** bloat git with new
Plotly HTML blobs — keep PNG/HTML-table outputs the renderer already
understands. If execute is blocked (no local GITT file, no jupyter kernel),
edit source cells only and render from existing outputs; say so in status.

## Files to touch

- `examples/02_Initial_data_inspection.ipynb` — path, `summary_plot` y, cycle list, family list
- `examples/03_capacity_vs_voltage.ipynb` — `potential` / `cycle_num` in plots
- `examples/05_GITT.ipynb` — load path; cycle selection
- `examples/06_loading_different_formats.ipynb` — `data_structures` import
- `examples/08_batmo_bdf.ipynb` — schema + `potential` / `cycle_num`
- `examples/09_loading_pec_data.ipynb` — `c` + markdown cells
- `examples/01_loading_data.ipynb` — load-path probe after save
- `examples/07_custom_loaders.ipynb` — only if a 1.x leftover shows up
- `cellpy/readers/cellreader.py` — `get()` examples block
- `docs/examples/*.md` (+ figure assets) — regenerate
- `docs/examples/index.md` — drop the “still 1.x” caveat for the updated set

## Test strategy

- No new `@pytest.mark.essential` tests (notebooks are not in the essential
  suite; scheduled CI has no notebook execute gate).
- After edits: `uv run pytest -m essential` (no library regression from the
  docstring-only `get()` change).
- Build verification: execute the runnable notebooks listed above through
  `uv run` (nbconvert or a small `nbformat`+`nbclient` loop). Treat a clean
  top-to-bottom run as acceptance for that file.
- `uv run --group docs python dev/render_example_notebooks.py` must succeed.
- Manual spot-check: `08` raw + `get_cap` plots; `02` `summary_plot` +
  `cycle_info_plot`; `06` instrument listing cell.

## Open questions

1. **GITT fixture.** `example_data.cellpy_file()` is `20180418_sf033_4_cc.cellpy`
   (ordinary cycling), not the `20210210_FC` GITT run. **Recommended:** keep
   `05_GITT` on `20210210_FC.h5` with a `data/` then `data/out/` probe; do not
   silently swap in `example_data.cellpy_file()`. If the file is absent, fail
   with a short “run notebook 01 / place the file in `examples/data/`” message.
2. **Re-execute vs source-only.** **Recommended:** execute when fixtures exist;
   source-only + render if execute cannot run in this environment.
3. **Split.** One PR is enough (notebooks + render + docstring). Say so if you
   want 01+docs-index deferred.
