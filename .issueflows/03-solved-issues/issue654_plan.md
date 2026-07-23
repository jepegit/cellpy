# Issue #654 — plan

## Goal

Make CV-split summary series real again: **without-CV** via
`make_summary(exclude_step_types=["cv_"])`, **with-CV** as
`full − non_cv` on the selected capacity columns — so
`capacities_*_split_constant_voltage` (and related helpers) stop drawing three
identical panels.

## Constraints

- `selector_type` / `selector` on `make_summary` stay deprecated no-ops (#509);
  do not revive them.
- `exclude_step_types=["cv_"]` is the supported non-CV path (capacity subtracted
  before derived columns are recomputed).
- With-CV is **not** a first-class summary mode today; derive it. Difference is
  meaningful for **additive capacity columns**; do not pretend it yields a true
  CV-only coulombic efficiency / voltage summary.
- Keep the existing melted row labels (`all` / `without CV` / `with CV`) and
  wide `_non_cv` / `_cv` suffixes so plot families and figure-spec structure
  stay stable (regenerate structural snapshots only if labels/structure change).
- Do not expand into #312 (CCCV substep typing).

### Prior art

- `make_summary(exclude_step_types=...)` — [`cellpy/readers/cellreader.py`](../../cellpy/readers/cellreader.py) (#509 / PR #517); behavioral test `test_make_summary_exclude_step_types` on `rate_dataset` (has `cv_*` steps).
- `partition_summary_cv_steps` — [`cellpy/utils/plotutils.py`](../../cellpy/utils/plotutils.py) (melted; used by `SummaryPlotDataPreparer._prepare_cv_split_data`).
- `_partition_summary_based_on_cv_steps` — [`cellpy/utils/helpers.py`](../../cellpy/utils/helpers.py) (wide concat; `concat_summaries` / `select_summary_based_on_rate` when `partition_by_cv`).
- `_prepare_fullcell_standard_data` — [`cellpy/plotting/prepare/summary.py`](../../cellpy/plotting/prepare/summary.py) still calls `selector_type="only-cv"` (same dead path; include in this fix).
- Existing non-mutation guard: `test_cv_split_plot_leaves_the_summary_frame_alone` (`tests/test_plotutils_headers.py`).
- Toolbox: none relevant (scan_* / migrate_prms only).
- Graph: plotting prepare / plotutils communities; no extra helper beyond the above.

## Approach

1. **Shared partition core** (one small private helper — prefer in
   `cellpy/utils/helpers.py` or a tiny function both sites import — avoid a third
   public API):
   - `full = c.data.summary` (copy / index-align as today).
   - `non_cv = c.make_summary(exclude_step_types=["cv_"], create_copy=True).data.summary`.
   - `cv = full[cols] - non_cv[cols]` (aligned on cycle index; only for the
     selected columns). Clip tiny negatives from float noise to `0` if needed.
   - Optional: if step table has no `cv_*` types, log a warning once; still
     return `cv ≈ 0` and `non_cv ≈ full` (correct for CC-only cells).

2. **Wire call sites** to that helper:
   - `partition_summary_cv_steps` (melt path for `summary_plot` CV-split).
   - `_partition_summary_based_on_cv_steps` (wide path for batch helpers).
   - `_prepare_fullcell_standard_data` CV merge (replace `only-cv` summary with
     the derived CV frame / same subtraction for the columns it merges).

3. **Do not** change `make_summary` deprecation warnings or add an
   `include_step_types` API in this issue.

4. **Docs**: one-line note in the partition helper docstring pointing at
   `exclude_step_types` + difference; no migration-guide rewrite unless a
   sentence already claims `selector_type` still works for CV split.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/utils/helpers.py` | Shared CV partition helper; rewrite `_partition_summary_based_on_cv_steps`. |
| `cellpy/utils/plotutils.py` | `partition_summary_cv_steps` uses shared helper (drop dead `selector_type`). |
| `cellpy/plotting/prepare/summary.py` | Fix `_prepare_fullcell_standard_data` off `only-cv`. |
| `tests/test_*.py` (new or extend) | Numeric regression on `rate_dataset`: with-CV ≈ full − non_cv; without-CV matches `exclude_step_types`; CC-only / figure cell: with-CV ≈ 0. Keep existing “summary frame untouched” test green. |
| Figure-spec snapshots | Only if structural labels change (unlikely). |

## Test strategy

- `uv run pytest` for touched files; gate with `uv run pytest -m essential` before close.
- New focused test(s) using `rate_dataset` (known `cv_*` steps + existing
  `test_make_summary_exclude_step_types` oracle):
  - After partition (melt or wide): `all ≈ without_cv + with_cv` on a capacity
    column (rel/abs tolerance matching #509 test).
  - Smoke: `summary_plot(..., y="capacities_*_split_constant_voltage")` still
    leaves `c.data.summary` columns alone.
- Optional: assert warning when no `cv_*` steps (figure cell) if we add that
  warning.

## Open questions

1. **Include fullcell `only-cv` fix in this PR?**  
   **Recommend: yes** — same dead API, same root cause, tiny extra surface.

2. **Shared helper vs fix three sites in place?**  
   **Recommend: one private shared helper** used by plotutils + helpers (+ prepare
   for fullcell), so the difference logic cannot drift.

3. **Warn when no `cv_*` steps?**  
   **Recommend: yes, `logging.warning` once** (or debug if too noisy) — still
   emit correct zeros; do not skip the family unless you prefer skip later.

4. **Helpers with `column_set=None` (all summary columns)?**  
   **Recommend: still subtract selected/all numeric columns as today, knowing
   non-capacity `_cv` columns are not physically meaningful** — callers of
   `partition_by_cv` are capacity-oriented; documenting that is enough. No new
   column classifier unless you want one.
