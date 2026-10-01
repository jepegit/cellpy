# Issue #1125 — plan: instrument-neutral docs and docstrings

## Goal

Remove wording that still assumes cellpy is a `.res` (Arbin) loader: generic
prose that says "res-files" / "hdf5 file" when it means "raw files" / "cellpy
file", and copy-paste docstrings that name the wrong tester. Keep every
mention that is genuinely Arbin-specific.

## Constraints

- Docs live on `master` (same PR as code); preview with
  `uv run --group docs zensical serve` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).
- Docstrings render through mkdocstrings (`docs/api/cellpy.md`,
  `docs/api/cell.md`, `docs/api/instruments.md`) — wording changes there are
  user-visible docs.
- Prose only. No behaviour, no header/column renames, no code changes other
  than comments, docstrings and one `logging.debug` string.
- Rendered tutorials under `docs/examples/*.md` come from `examples/*.ipynb`;
  out of scope here (render drift risk, separate pass as in #1023).
- `_old_docs/`, `HISTORY.md`, `DEPRECATIONS.md`, tests and `testdata/` names
  are not touched.
- Loader modules named for a tester (`arbin_res.py`, `arbin_sql*.py`,
  `_aux_map.py`) legitimately talk about Arbin — leave.

### Prior art

- `#1023` iterations 1–13 (docs usability review,
  [docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md))
  — same docs tree, same conventions (short code-first pages, `my_cell.res`
  as the running example filename). Coexist: this pass only neutralises
  prose, it does not restructure pages.
- `.issueflows/00-tools/check_docs_relative_links.py`,
  `check_rtd_latest_links.py` — run after edits (docs CI already does).
- No toolbox script for prose scanning; `rg -i '\.res\b|res[- ]file|arbin'`
  is the whole inventory (done, see below).
- Graph: not needed (no code structure involved).

## Inventory and decision

Scan: `rg -n -i '\.res\b|res[- ]file|arbin' src/cellpy docs` excluding Arbin
loader modules, tests, `_old_docs`, `docs/examples`. ~200 hits; triaged into:

### Change — generic prose that means "raw file" / "cellpy file"

`src/cellpy/readers/cellreader.py`

- Module docstring: "exporting them in a common hdf5-format" → "a common
  `.cellpy` format"; example `c.save("super_battery_run.h5")` → `.cellpy`;
  keep the two-file merge example but drop the tester-specific suffix
  (`super_battery_run_01.res` → neutral name, or state "any supported raw
  file").
- `set_raw_datadir`: "directory containing .res-files" / "res-files" /
  "res-directory" → raw files / raw-data directory.
- `set_cellpy_datadir`: ".hdf5-files" / "hdf5-directory" / `"MyData/HDF5"` →
  cellpy files / cellpy-file directory.
- `check_file_ids`: "raw-data and cellpy hdf5", "hdf5 file and the res-files",
  ".res -files", "cellpy hdf5-file" (x2) → raw files / cellpy file.
- `logging.debug("contains %i res-files")` → "contains %i raw files".
- `load` (deprecated path): `raw_files (list): name of res-files` → raw files.
- `get()` docstring examples: keep the first example (explicitly
  `instrument="arbin_res"`), but the later generic examples
  (`cellpy_file=`, list merge, `units=`) use `.res` as if it were the only
  format — keep filenames (valid, autodetected) and add one sentence that any
  registered tester file works and `.res` is just the example. Comment
  "read an arbin .res file" stays (that example is Arbin).
- `fetch_meta` example `cellpy.get("cell_042.res")` — keep (valid), no change
  needed; revisit only if we settle on a neutral example name (open question).

`src/cellpy/readers/instruments/neware_xlsx.py`

- Class docstring "Class for loading arbin-data from MS SQL server" and
  loader docstring "Loads data from arbin SQL server h5 export" → Neware xlsx
  export. Copy-paste bug.

`src/cellpy/readers/instruments/biologics_mpr.py`

- `file_name (str): path to .res file.` → path to `.mpr` file. Copy-paste bug.

`src/cellpy/readers/instruments/configurations/maccor_txt_one.py`,
`maccor_txt_zero.py`

- Comments `# new Arbin SQL Server` on Maccor header aliases → `# shared
  alias (also used by the Arbin SQL loaders)` or drop. Comment only.

`docs/`

- `docs/reference/summary_columns.md:3` "for a plain Arbin file with no extra
  options — 58 columns" → "for a plain file (any tester) with no extra
  options"; the count does not depend on the tester.
- `docs/getting_started/basic_usage.md:65` "For an Arbin file that means Ah"
  → "For an Arbin `.res` file, for example, that means Ah" (keeps the fact,
  marks it as one tester).
- `docs/agents/index.md:450` "large `.res` / SQL dumps" → "large raw files
  (e.g. `.res`, SQL dumps)".
- `docs/guides/units.md:41`, `:206`, `docs/fundamentals/glossary.md:84`,
  `docs/reference/summary_columns.md:31` — same pattern: keep the Arbin fact,
  phrase it as an example ("the tester's unit — Ah for an Arbin `.res`
  file").

### Keep — genuinely Arbin / `.res` specific

- Installation / checkup / troubleshooting / CLI pages: Access driver,
  mdbtools, `cellpy info --check` "arbin .res support", several data sets in
  one `.res` file, `dataset_number`.
- Instrument table in `docs/index.md`, `arbin_res` loader ids in
  `batch_database.md`, migration notes about Arbin loaders / aux columns,
  `ArbinConfig` in configuration reference, folder-structure listing.
- `example_data.raw_file()` "a small Arbin file" — it is one.
- `cli_api.py` Arbin driver checks; `prms.py` / `config/*` legacy Arbin SQL
  secrets; `data_structures.py` vendor map; `merger.py` / `hooks.py` /
  `harmonize.py` / `declarations.py` comments that compare testers by name.
- `docs/fundamentals/fundamentals.md` mermaid "(.res, .txt, .csv, …)" —
  already neutral.

### Leave — not worth touching

- `__main__` / `_check_*` dev code in `ocv_rlx.py`, `data_structures.py`,
  `filefinder.py` that hard-codes the Arbin test fixture.
- `docs/examples/*.md` rendered notebooks (separate render pass).

## Approach

1. Apply the **Change** list above file by file (docstrings, comments, one
   debug string, ~8 doc pages). Each edit keeps facts and only removes the
   "everything is a .res file" framing.
2. Re-run the inventory `rg` and confirm every remaining hit falls in Keep /
   Leave; paste the residual count into the status file.
3. `uv run --group docs zensical build --clean` → "No issues found";
   `uv run .issueflows/00-tools/check_docs_relative_links.py`.
4. `uv run pytest -m essential` (no behaviour change expected; guards the
   `logging.debug` string edit and the loader docstring edits).
5. HISTORY entry at close (docs line).

## Files to touch

- `src/cellpy/readers/cellreader.py` — module docstring, `set_raw_datadir`,
  `set_cellpy_datadir`, `check_file_ids`, `load`, `get` docstrings; one
  debug string.
- `src/cellpy/readers/instruments/neware_xlsx.py` — two docstrings.
- `src/cellpy/readers/instruments/biologics_mpr.py` — one arg docstring.
- `src/cellpy/readers/instruments/configurations/maccor_txt_one.py`,
  `maccor_txt_zero.py` — three comments each.
- `docs/reference/summary_columns.md`, `docs/getting_started/basic_usage.md`,
  `docs/guides/units.md`, `docs/fundamentals/glossary.md`,
  `docs/agents/index.md` — one or two sentences each.
- `.issueflows/01-current-issues/issue1125_status.md` — new.

## Test strategy

- `uv run pytest -m essential` (merge gate; no new tests — prose only).
- `uv run --group docs zensical build --clean` must report no issues.
- `uv run .issueflows/00-tools/check_docs_relative_links.py`.
- Final `rg` inventory shows zero hits in the Change category.

## Open questions

1. **Example filename convention.** ~40 doc snippets use `my_cell.res`
   (often with `instrument="arbin_res"`). Options: (a) keep — valid, one
   consistent running example, Arbin is still the most common tester for
   this user base; (b) rotate a few generic snippets (no `instrument=`) to
   another suffix (`my_cell.txt` + `instrument="maccor_txt"`) to show
   variety. Recommendation: **(a)** plus the single "any registered tester
   file works" sentence in `get()` and `basic_usage.md`. Say if you want (b).
2. **`hdf5` → `.cellpy` wording** in the same `cellreader.py` docstrings is
   not strictly "instrument" but is the same era of leftover and sits on
   the same lines. Recommendation: include. Say if you want it left out.
