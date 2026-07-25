# Issue #679 plan — bug in BatchICACollector (`fig_pr_cycle`)

## Goal

Make `BatchICACollector(..., plot_type="fig_pr_cycle")` render without `KeyError: 'cycle_num'`, matching the already-working `fig_pr_cell` / `film` paths on the same ICA frame.

## Constraints

- Specced ICA collected frame columns stay `cycle`, `direction`, `voltage`, `capacity`, `dqdv` (#591 / tests in `tests/test_collectors.py`). Do **not** rename ICA to `cycle_num`.
- Capacity-curve collectors keep native `CurveCols.cycle_num` (#540).
- Drawing stays in `cellpy.plotting.collected` (#657); no move of collection logic.
- Keep the fix small — no plotting redesign, no collector API rewrite.
- Target branch: `master` / label `v2` (rc1 regression).

### Prior art

- Design: [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) — `fig_pr_cycle` → `layout="per_cycle"`.
- `ica_plotter` already passes `z="cycle"` into `_cycles_plotter` (`cellpy/plotting/collected.py`).
- `cycles_plotter` passes `z=_CCOLS.cycle_num` for capacity curves.
- `sequence_plotter` already uses `curves[z]` for palette sizing on `fig_pr_cell`, but still hardcodes `.cycle` when filtering by `cycles=`.
- Tests: `test_batch_ica_collector_*` cover default / film / frame shape; **no** `fig_pr_cycle` coverage today.
- Toolbox: nothing relevant for this bug (`00-tools` checked).
- Graph: `BatchICACollector` → `collected_plot` / `_cycles_plotter` / `sequence_plotter` (community ~14 / 810).

## Approach

**Root cause.** ICA frames use column `"cycle"`. In `_cycles_plotter`, when `method == "fig_pr_cycle"` and `cycles is None`, the code does:

```python
number_of_figs = len(collected_curves[_CCOLS.cycle_num].unique())  # KeyError
```

That path is hit in practice because constructor `cycles=[…]` feeds the **data** collector only; plotter `cycles_to_plot` defaults to `None`, and `ica_plotter` leaves it `None` when unique cycles ≤ 50. `fig_pr_cell` / `film` never touch that line (they count `"cell"`), which matches the issue comment.

**Fix (primary).** In `_cycles_plotter`, count unique cycles via the existing `z` parameter (the cycle column for both families):

```python
number_of_figs = len(collected_curves[z].unique())
```

**Fix (same PR, small hardening).** In `sequence_plotter`, stop hardcoding `collected_curves.cycle` for cycle filters:

- `fig_pr_cell` / `film`: filter with `collected_curves[z]` (pre-swap `z` is the cycle column).
- `fig_pr_cycle`: after `z, g = g, z`, the cycle column is in `g` — filter with `collected_curves[g]` (or filter before the swap with the original `z`). Prefer one clear pattern (filter before swap) so both capacity (`cycle_num`) and ICA (`cycle`) work.

**Out of scope (note only).** `cycles_plotter` still references `collected_curves.cycle` in its “too many cycles” branch despite using `cycle_num` as `z` — separate latent bug; only touch if a one-liner falls out of the same edit. Do not auto-wire constructor `cycles` → `cycles_to_plot` unless we decide that in Open questions.

## Files to touch

| Path | Change |
|------|--------|
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | `_cycles_plotter`: use `z` for `fig_pr_cycle` fig count; `sequence_plotter`: filter cycles via the cycle column param, not `.cycle` |
| [`tests/test_collectors.py`](../../tests/test_collectors.py) | Add `BatchICACollector(..., plot_type="fig_pr_cycle")` smoke (and optionally cycles-collector `fig_pr_cycle` if filter hardening is in) |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | One short note: ICA frames use `"cycle"`; plotters must use `z` / the cycle column arg, not hardcode `cycle_num` |

## Test strategy

```bash
uv run pytest tests/test_collectors.py -q
uv run pytest -m essential   # before close
```

New test(s):

1. `BatchICACollector(populated_batch, plot_type="fig_pr_cycle")` runs (`_assert_ran`) — reproduces #679.
2. Optional: same with `cycles=[1, 2]` on the constructor (collection filter) still renders.
3. If filter hardening lands: `BatchCyclesCollector(..., plot_type="fig_pr_cycle", cycles_to_plot=[1])` (or equivalent) does not `KeyError` on `.cycle`.

Mark the new ICA regression `@pytest.mark.essential` only if it stays fast on the existing `populated_batch` fixture (prefer yes — this is an rc1 plot regression).

## Open questions

1. **Wire `cycles` → `cycles_to_plot`?** When the user passes `cycles=[1,2,3]` to `BatchICACollector`, should that also become the plotter’s `cycles_to_plot` default?  
   - **Recommended: no** for this PR — constructor already documents separate elevated args; the `z`-based count fix is enough for the crash. Can be a follow-up UX issue.
2. **Include capacity-curve filter hardening in this PR?**  
   - **Recommended: yes** — same hardcoded `.cycle` footgun, tiny diff, prevents the next KeyError on `BatchCyclesCollector` + `fig_pr_cycle` / filtered `fig_pr_cell`.
