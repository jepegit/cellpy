# Issue #450 — status

- [x] Done

## What's done

- `CellpyUnits` re-exported from `cellpycore.units` in `internal_settings.py`.
- Local pint registry removed from `data_structures.py`; `Q` re-exported from cellpycore.
- `cellreader.py`: `data_structures as ds` (disambiguates from `self.core` / cellpycore).
- Interop test hard-pass + single-registry assert in `test_unit_handling_stage0.py`.
- Essential suite green (81 tests).

## Remaining work

- None.
