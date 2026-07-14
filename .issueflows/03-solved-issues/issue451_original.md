# Issue #451 — Stage 1.6: Units Phase 2 — delegate the duplicated converters to cellpycore.units

GitHub: https://github.com/jepegit/cellpy/issues/451
Labels: cellpy2-stage1, yolo

## Goal

Delete cellpy's duplicated converter bodies and wrap the cellpycore.units
originals (unit plan Phase 2): `get_converter_to_specific`,
`nominal_capacity_as_absolute`, `to_cellpy_unit` (→ `convert_value`),
`unit_scaler_from_raw` (→ `calculate_scaler`), and the inline current-factor
pint math in `_make_summary` (→ `calculate_current_conversion_factor`).
Blocked on core#115 (released as cellpycore 0.2.0) + re-pin.

## Acceptance

- Converter parity fixtures green (tests/test_unit_handling_stage0.py).
- Full suite green; duplicated bodies deleted, wrappers ≤ a few lines each.
