# Status — Issue #866 (interactive `/iflow-fix` session)

Release prep for v2.1.2: `HISTORY.md` plus a documentation sweep. One branch
(`866-release-prep-2-1-2`), many small fixes, landed together via `/iflow-close`.

- [x] Done

## Iterative fixes log

- 2026-08-09 — `HISTORY.md`: turned the flat `[Unreleased]` list into a proper
  `## [2.1.2] - 2026-08-09` release section (fresh empty `[Unreleased]` kept on top).
  Added a lead paragraph noting that the interim `v2.1.1.post7` / `v2.1.1.post8` tags
  and the `v2.1.2a1`–`a4` pre-releases fold into this release, regrouped the 17 bullets
  by theme (Plotting and collect / Configuration and CLI / Data and files / Chores),
  and normalized style to the rest of the file (`*` bullets, single-backtick inline
  code instead of RST-style double backticks). Coverage verified against
  `git log v2.1.1.post6..master`: all user-visible PRs accounted for (#847 is a kaleido
  follow-up folded into the #818 bullet; dependabot bumps excluded, per existing
  convention). No content invented or dropped.
- 2026-08-09 — `docs/fundamentals/fundamentals.md`: the opening paragraph presented
  `pandas` as cellpy's only frame library. Verified the claim is *accurate* for the
  Data object (`c.data.raw` / `.steps` / `.summary` really are pandas), so kept it and
  appended a short paragraph covering the rest: `cellpy.collect` frames are polars
  (`Collection.data`, converted to pandas at the plotting seam) and the v9 cellpy-file
  stores parquet. Links to the existing frame-type note in
  `docs/getting_started/agents.md` instead of restating it (one source of truth).
  `docs/fundamentals/data_structure.md` already hedges correctly ("still the public
  surface in 2.x") and was left alone.
- 2026-08-09 — `docs/contributing/developers_guide/dev_loaders_and_instruments.md`:
  correctness pass on the "About loaders" section. Every claim checked against the code;
  fixed: (1) `generate_default_factory` / `find_all_instruments` are in
  `cellpy/readers/data_structures.py`, not the non-existent `cellpy/core.py`;
  (2) the executor binds to `CellpyCell.loader`, not `CellpyCell.loader_method` (no such
  attribute); (3) resolved the contradiction between "each reader is a subclass of
  `DataLoader` (in `base.py`)" and the correct "each module defines a class *named*
  `DataLoader` subclassing `BaseLoader`" — there is no `DataLoader` in `base.py`;
  (4) `BaseLoader`, not `DataLoader`, is what subclasses `AtomicLoad`; (5) `TxtLoader`
  subclasses `AutoLoader`, not `BaseLoader` directly; (6) `configuration` ->
  `configurations` package name; (7) replaced the `pd.read_csv(warn_bad_lines=...)`
  example (removed in pandas 2.0; cellpy pins `pandas>=3.0.3`) with `on_bad_lines`;
  (8) `parse_formatter_parameter` -> `parse_loader_parameters` in the prose so it matches
  the example beneath it; (9) noted that `register_instrument_readers` is DI-aware (builds
  the default factory only when none is injected). The newer entry-point-contract intro
  block was already current and left untouched.
- 2026-08-09 — Docs sweep, evidence pass: checked that every relative markdown link in
  `docs/` resolves (clean — the single hit was a false positive from a link title), then
  grepped for removed-in-2.1 API names. Found and fixed the false claim that the legacy
  `headers_normal` / `headers_step_table` / `headers_summary` attributes "still resolve
  via a shim (removal 2.1)" — verified they now raise `AttributeError`. Corrected in
  `docs/fundamentals/data_structure.md` and `docs/getting_started/migration_v1_to_v2.md`,
  both now pointing at the replacement table in `migration_v2.0_to_2.1.md` (which already
  stated it correctly).
- 2026-08-09 — `docs/examples/batch_utility/cellpy_batch_processing_docs.md` (published in
  the site nav as **Batch processing**): the whole "Working with batch objects" section
  taught API removed in 2.1. Rewrote it against `cellpy.collect`:
  `BatchSummaryCollector` / `BatchCyclesCollector` / `BatchICACollector` (all now raise
  `NotImplementedError`) -> `summary_collector` / `cycles_collector` / `ica_collector`;
  `.show()` -> `.plot()`; `.save(serial_number=1)` -> `.save("out", formats=...)` (explicit
  directory, no cwd fallback); `max_cycle=10` on cycles -> `cycles=`; `collector_type=` ->
  `method=`; `plot_type="fig_pr_cycle"` -> `.plot(layout="per_cycle")`; drawing options
  (`spread`, `height`) moved off the collector onto `.plot()`. Also fixed
  `b.summaries.discharge_capacity_gravimetric` (attribute access on what is now a
  long-format *polars* frame -> `AttributeError`) to a `.pivot(...)` + `.to_pandas()` for
  the matplotlib cell, updated the setup-cell import off the legacy
  `cellpy.utils.collectors` shim, added a migration note admonition, and fixed the prose
  typos ("sumaries", "ploted") and the wrong class name `BatchCycleCollector`. Stale
  nbconvert "figure name: ..." output blocks for the rewritten cells removed; images kept.
  **Verified**: wrote a throwaway pytest exercising all five rewritten snippets against the
  `populated_batch` fixture — all pass (scratch file deleted afterwards).
  **Superseded** by the 2026-08-09 notebook-regeneration entry below: two claims made here
  were wrong. `ir_charge` is *not* present in the tutorial's paper01 data (that batch has no
  IR/resistance column at all, so the kept `ir_charge` cell would have raised), and the
  `.md` is a generated artifact, so editing it directly was the wrong layer.
- 2026-08-09 — `docs/examples/04_incremental_capacity_analysis.md` (site nav: **Incremental
  capacity analysis**): the page documented the pre-2.1 ICA API throughout. Verified
  `ica.dqdv_cycle` / `dqdv_cycles` / `dqdv_np` / `Converter` are all absent from
  `cellpy.utils.ica`, and that the current signature is
  `dqdv(source, cycles=None, direction="both", options=None, ...)` returning one long frame
  with columns `cycle, direction, voltage, capacity, dqdv`. Rewrote: the intro bullets (now
  `ica.dqdv`'s three input forms — cell, curve frame, `(voltage, capacity)` arrays) with a
  migration admonition; `split=True` -> filter the `direction` column; `cycle=` -> `cycles=`;
  every `y="dq"` plotly call -> `y="dqdv"` (the duplicate `dq` column was removed in 2.1, so
  those calls raised); the stale `get_cap` output table (now native `cycle_num` / `potential`
  names); and replaced the pasted, obsolete `def dqdv(...)` docstring dump with the current
  signature plus an `IcaOptions` field/default table and a link to the ica API reference (less
  to rot next time). All rendered output tables were **regenerated from the real
  `example_data.cellpy_file()`** the page loads — no hand-written numbers. **Verified**: a
  throwaway pytest exercising all rewritten snippets (including both plotly calls) passes;
  scratch file deleted. Scope note: this grew beyond the "cellpy-agnostic methods" section
  I originally proposed, because the main section was equally stale — finishing the page was
  better than leaving it half-migrated. **Superseded** by the notebook-regeneration entry
  below — the fixes were re-applied at the notebook layer and the `.md` regenerated.
- 2026-08-09 — `docs/getting_started/migration_v1_to_v2.md`: same "deprecated, removal 2.1"
  staleness as fix 4, but for plotting and ICA. Verified against the code, then corrected:
  `plotutils.summary_plot_legacy` (absent — was described as a live deprecated alias);
  `backend="seaborn"` (documented as "warns once and maps to matplotlib", actually raises
  `ValueError: unknown plotting backend 'seaborn' (known: plotly, matplotlib)`, as does
  `"bokeh"`); and the ICA list (`Converter` / `dqdv_cycle` / `dqdv_cycles` / `dqdv_np` /
  old `dqdv` kwargs / the `dq` column) which is now removed rather than deprecated. Also
  repointed two stale references to the removed `BatchICACollector` and the
  `cellpy.utils.collectors` shim at `cellpy.collect`.
- 2026-08-09 — Final sweep: re-ran the removed-API scan across all of `docs/**/*.md`
  (`dqdv_cycle`, `dqdv_np`, `ica.Converter`, `collectors.Batch*`, `split=True`, `y="dq"`,
  `make_new_cell`, `summary_plot_legacy`, `backend="seaborn"|"bokeh"`). Remaining hits are
  all legitimate — the migration guides documenting the removals, and a plotly `fig.show()`
  in `05_GITT.md`. No further stale API found in the published docs.
- 2026-08-09 — **Notebooks regenerated** (prompted by the user pushing back on my claim that
  regenerating needed a dataset we lacked — the claim was wrong twice over). The ICA notebook
  only uses `example_data.cellpy_file()`, and the batch tutorial's paper01 dataset is
  **vendored in the repo** (`docs/examples/batch_utility/data/{raw,cellpyfiles}` +
  `cellpy_db.xlsx`); `b.update()` loads all 7 cells here in ~40 s. Decisive finding: the two
  `.md` pages are **generated artifacts** — `dev/render_example_notebooks.py` converts every
  `docs/examples/**/*.ipynb` to markdown ("re-run and commit whenever a notebook changes"), so
  the earlier hand edits to the `.md` would have been destroyed on the next render. The fixes
  were therefore re-applied to the `.ipynb` source cells, both notebooks executed, plotly
  figures backfilled to PNG (`dev/backfill_notebook_plotly_pngs.py`), and the `.md` regenerated
  through the official script. Every cell now runs; all outputs, tables and figures are real.
  Three further breaks surfaced only because the notebooks were actually executed:
  (1) the batch tutorial's **first config cell** used `prms.Paths.db_path = "."`, which raises
  `AttributeError` — `prms.Paths` does not exist in 2.x (the page also falsely claimed "the
  legacy names still work via the compatibility layer"); correct API is `cellpy.config.paths.*`;
  (2) paper01's summaries have **no IR/resistance column**, so the `ir_charge` cell I had kept
  would raise — the second matplotlib subplot now plots `coulombic_efficiency`;
  (3) `get_cap()` returns `potential`, not `voltage`, so `cap.voltage` in two later cells
  raised as well. Also fixed the stale "should still run under 2.x thanks to the compatibility
  layer" note in `docs/examples/index.md`. Verified: `IcaOptions` field/default table and the
  `dqdv` signature checked against the dataclass and `inspect.signature`; all four introduced
  relative links resolve; the seven untouched example pages re-render byte-identical; the
  batch run wrote **no** artifacts into the tracked `docs/examples/batch_utility/out/` tree.
  Note for future editors: the notebook editor drops the required `metadata` /
  `execution_count` keys from output records, which makes `nbconvert` refuse the file — the
  committed notebooks already had this defect, and it must be repaired before rendering.
- **Spun off as [#869](https://github.com/jepegit/cellpy/issues/869)**: the repo also carries a *second*, older copy of the tutorials
  at the top-level `examples/` tree (`examples/04_incremental_capacity_analysis.ipynb`,
  `examples/cellpy batch utility/cellpy_batch_processing.ipynb`, 11 notebooks total), which
  `docs/examples/index.md` links to as the download location. Those copies still use removed
  API (9 and 11 hits respectively) and had already diverged from the `docs/` copies before this
  issue. Out of scope here; worth its own issue.
