# Plan: #949 `b.plot` not showing IR

## Goal

Make `b.plot(ir=True, direction="discharge")` show an IR panel when the
summaries contain IR, and tell the user when they do not — instead of dropping
the panel with a debug log.

## Constraints

- Stay inside `cellpy.plotting.batch_summary` (the `Batch.plot` delegate). Do
  **not** rebase onto collectors / `collected_plot` (Epic B / #708).
- Do not change `make_summary(find_ir=…)` defaults in this issue (see open
  question 2).
- `ir=True` is already the plotly default; the reporter's call is the
  `direction="discharge"` combination.
- New merge-gating tests: `@pytest.mark.essential` + a row in
  [test-registry.md](../04-designs-and-guides/test-registry.md).
- Test command is `uv run pytest`; no conda.
- Public batch-plot surface: one line in
  [`docs/getting_started/agents.md`](../../docs/getting_started/agents.md) if
  the warning/fallback is user-visible.
- `HISTORY.md` `[Unreleased]` bullet at `/iflow-close`.

### Prior art

- `plot_cycle_life_summary_plotly` —
  [`cellpy/plotting/batch_summary.py`](../../cellpy/plotting/batch_summary.py):
  `direction` picks capacity **and** IR (`ir_discharge` vs `ir_charge`); if
  that header is missing from `summaries.variable.unique()`, IR is skipped at
  `logging.debug("no ir data available")`. Rate uses the same pattern.
- `generate_summary_frame_for_plotting` (same file): optional IR/rate columns
  are included when present. Synthetic farms with `ir_charge` /
  `ir_discharge` melt correctly; `'ir_discharge' in unique` is True. Frame
  prep is not the bug when the columns exist.
- Matplotlib renderer (same file): ignores `ir=` / `direction=`; always tries
  `summaries.ir_charge`. Honour the same pick/fallback if cheap.
- `cellpycore.summarizers.ir_to_summary` + `LastIRExtractor`: both
  `ir_charge` and `ir_discharge` are added only when `find_ir` is True **and**
  raw has `internal_resistance`. A cycle without a discharge step gets NaN
  `ir_discharge`, not a missing column. A summary built with `find_ir=False`
  (public `CellpyCell.make_summary` default; `batch.runner` recalc) has **no**
  IR columns at all.
- Design doc:
  [plotting-batch-summary.md](../04-designs-and-guides/plotting-batch-summary.md)
  (#658). Update the IR/`direction` contract there.
- Existing tests `test_issue668_batch_plot_variants` /
  `test_batch_plot_delegates_without_batch_plotters` (`tests/test_batch.py`)
  already call `ir=True, direction="discharge"` but are **xfail** (Epic B
  `.plotter` holder). Leave them; do not un-xfail. New tests assert on the
  figure `Batch.plot` / `plot_cycle_life_summary_plotly` returns.
- Toolbox: nothing in `.issueflows/00-tools/` applies. Graph: no
  `graphify-out/`, so grep-only.
- #950 (same notebook line) deliberately left this as a separate plotting
  issue.

## Approach

Verified on this branch (synthetic farms, not assumed from the issue text):

1. When both IR columns exist, `direction="discharge"` **does** select
   `ir_discharge` and would put `"IR (discharge)"` in the plotly title.
2. The reported miss is therefore either (a) `ir_discharge` absent from the
   melted `variable` column while `ir_charge` (and discharge capacity / rate)
   are present, or (b) **neither** IR column present, skipped at debug.

Fix in `plot_cycle_life_summary_plotly` (and matplotlib if the same helper
fits):

1. Small helper `_pick_optional_summary(available, preferred, fallback)`:
   return `preferred` if it is in `available`, else `fallback`, else `None`.
   Pass `list(available)` so ArrowStringArray membership is not a factor.
2. When `ir=True`:
   - preferred = direction's IR (`ir_discharge` / `ir_charge`);
   - fallback = the other IR column;
   - if a column is picked, append it;
   - if we used the fallback, `warnings.warn` once (preferred missing, using
     the other);
   - if neither exists, `warnings.warn` (not debug) naming both headers.
   Same for `rate=True` only if it is a one-liner with the same helper;
   otherwise leave rate as-is (reporter said rate works).
3. Do **not** treat all-NaN as missing: if the column exists, keep the panel
   (autorange). Empty traces are a data issue, not a plotter skip.
4. Tests use a tiny fake `experiment` (`memory_dumped["summary_engine"]` +
   journal pages) — no `populated_batch`. Assert on the plotly title /
   y-axis texts:
   - both IR columns + `direction="discharge"` → `"IR (discharge)"`;
   - only `ir_charge` + `direction="discharge"` + `ir=True` → still an IR
     panel (`"IR (charge)"`) and a `UserWarning`;
   - no IR columns + `ir=True` → `UserWarning`, no IR in title;
   - `ir=False` → no IR even when columns exist.
5. Record the pick/fallback/warn contract in
   `plotting-batch-summary.md`. One sentence on `b.plot(ir=…, direction=…)`
   in `agents.md` if the warning is part of the public recipe.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/plotting/batch_summary.py` | `_pick_optional_summary`; IR (and optionally rate) pick/fallback/warn; matplotlib uses the same pick if cheap. |
| `tests/test_batch_summary_ir.py` | New essential tests on synthetic farms (above cases). |
| `.issueflows/04-designs-and-guides/plotting-batch-summary.md` | IR/`direction` contract. |
| `.issueflows/04-designs-and-guides/test-registry.md` | Rows for the new tests. |
| `docs/getting_started/agents.md` | One line on `ir=` / `direction=` if user-visible. |
| `HISTORY.md` | `[Unreleased]` bullet (written at close). |

## Test strategy

```bash
uv run pytest tests/test_batch_summary_ir.py -m essential
uv run pytest -m essential
```

Do not un-xfail the Epic B `populated_batch.plotter` tests.

## Open questions

1. **Fallback or strict direction IR?** Recommended: **fallback + warning** —
   `direction="discharge"` still selects discharge capacity; IR shows the
   charge column when that is all the summary has. Strict (warn and omit)
   matches today's silent skip and keeps the reporter's plot IR-less.
2. **Also pass `find_ir=True` from `batch.runner` recalc / flip
   `make_summary` default?** Recommended: **not in this issue.** Plotter
   warnings cover "no IR in the frame". Changing summary defaults is a
   behaviour change for every recalc. Follow-up if we confirm the reporter's
   summaries lack IR columns entirely.
