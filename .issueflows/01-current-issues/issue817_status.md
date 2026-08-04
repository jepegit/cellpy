# Issue #817 — Status

- [ ] Done

## What's done

- Plan confirmed (Accept 2026-08-04).
- Branch: `cursor/817-spread-plot-share-y-a438` (cloud prefix; tracks #817).
- PR: https://github.com/jepegit/cellpy/pull/834 (#834, draft)
- `_cycles_plotter`: set `matches="y"` when `match_axes` True; clear when False.
- Spread path: `_apply_summary_y_ranges` no longer skipped.
- Tests in `tests/test_collected_summary_axes.py` (group-avg + spread + share_y / y_ranges).
- `plotting-collected.md` notes spread parity with #804.
- `MPLBACKEND=Agg uv run pytest tests/test_collected_summary_axes.py` — 11 passed.

## Remaining work

- Essential suite + `/iflow-close` (HISTORY, mark Done, PR ready).
