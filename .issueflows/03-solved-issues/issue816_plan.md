# Plan: #816 — mixed group_it averaging (yolo)

## Goal

With `group_it=True`, average groups that have ≥2 cells and keep singleton
groups as long-form series (`mean` = cell value, `std` = null) in the same
frame. Drop all-or-nothing wide fallback when any multi-member group exists.

## Approach

1. In `collect_summaries`, partition journal groups into multi (≥2) vs singleton.
2. Run `group_average` on multi only; unpivot singletons to the same long schema.
3. `grouped=True` iff any multi group was averaged. All-singleton still wide + False.
4. Stretch (long vs wide facet ids): **out of scope** for this yolo pass.

## Files to touch

- `cellpy/collect/summary.py` — partition gate
- `cellpy/collect/_summary_ops.py` — `singletons_as_long` helper
- `cellpy/collect/collection.py` — docstring tweak
- `tests/test_collect.py` — mixed multi+singleton test; keep all-singleton fallback

## Test strategy

`uv run pytest tests/test_collect.py -q` then `uv run pytest -m essential -q`
