# Issue #679 status

- [x] Done

## What's done

- Plan confirmed (Accept).
- Fixed `_cycles_plotter` to count unique cycles via `z` (ICA `cycle` / capacity `cycle_num`).
- Fixed `sequence_plotter` curve/ICA cycle filters to use `z` (filter before `z`/`g` swap on `fig_pr_cycle`).
- Fixed `cycles_plotter` “too many cycles” branch to use `_CCOLS.cycle_num`.
- Tests: `test_batch_ica_collector_fig_pr_cycle`, `_with_cycles_arg`, `test_batch_cycles_collector_fig_pr_cycle` (`@pytest.mark.essential`).
- Design note in `plotting-collected.md`.
- `MPLBACKEND=Agg uv run pytest tests/test_collectors.py` → 12 passed.
- `MPLBACKEND=Agg uv run pytest -m essential` → 627 passed, 1 skipped.
- HISTORY Unreleased bullet added.

## Remaining work

- None (PR + `/iflow-cleanup` after merge).
