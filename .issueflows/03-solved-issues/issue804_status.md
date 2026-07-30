# Issue #804 — Status

- [x] Done

## What's done

- Plan confirmed; build implemented.
- `summary_plotter`: default independent y-axes (`share_y=False`); `share_y` preferred, `match_axes` alias; non-empty `y_ranges` forces independent + applies Plotly per-panel ranges.
- Helpers: `_resolve_share_y`, `_yaxis_key_for_facet_label`, `_apply_summary_y_ranges`.
- Docs: `plotting-collected.md`, `docs/getting_started/agents.md`; `Collection.plot` / `collected_plot` docstrings.
- Tests: `tests/test_collected_summary_axes.py` (6 essential) — all passing.
- `HISTORY.md` Unreleased bullet; closing via `/iflow-close`.

## Remaining work

- None.
