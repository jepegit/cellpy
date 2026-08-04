# Issue #821 — Status

- [x] Done

## What's done

- Plan confirmed (Accept 2026-08-04); defaults: collected `direction="charge"`; `both` → Plotly `line_dash`.
- Branch: `cursor/821-ica-plotter-direction-both-a438`
- PR: https://github.com/jepegit/cellpy/pull/835 (#835)
- `_select_direction("both")` no-ops; line layouts (`fig_pr_cell` / `fig_pr_cycle`) filter direction.
- `ica_plotter` allows `both`; invalid → `logger.warning` + coerce to charge.
- Plotly `both` sets `line_dash=direction`.
- `ica_plotter` accepts `cycles=` from `collected_plot` kwargs without clash.
- Tests: `tests/test_collected_ica_direction.py` (essential); registry + `HISTORY.md` + `plotting-collected.md`.
- Essential suite: 665 passed.

## Remaining work

- None.
