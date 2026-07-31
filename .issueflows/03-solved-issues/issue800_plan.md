# Issue #800 — plan

## Goal

Apps can ask which `cellpy.get` metadata knobs to show for an instrument pick, instead of exposing every field blindly.

## Approach

- Add `instrument_meta_schema(instrument=None)` next to `list_instruments`.
- Return a shared framework catalog (mass/area/loading/nominal_capacity/…) — code today has no per-loader required-meta diffs; `instrument` is echoed for future overrides.
- Export as `cellpy.instrument_meta_schema`.
- Do **not** change `list_instruments` row shape (breaks existing tests).

## Files

- `cellpy/readers/data_structures.py`
- `cellpy/__init__.py`
- `tests/test_instrument_meta_schema.py`
- `docs/getting_started/agents.md`, `AGENTS.md`, `HISTORY.md`

## Test strategy

- Shape keys present; known field names; `instrument` echoed; units dict non-empty.
