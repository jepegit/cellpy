# Issue #431 — Status

- [x] Done

## What's done

- Branch `431-unit-handling-stage0` from current `master`.
- cellpy-core preflight: `test_units_optional.py` + `test_units_converters.py` — **28 passed** (no core PR).
- `tests/unit_parity_support.py` — golden cases + `make_parity_cell` / `make_core_stub`.
- `tests/test_unit_handling_stage0.py` — strict-xfail registry interop + essential parity (4) + charge-mismatch + explicit nom_cap.
- `tests/README.md` — Stage 0.4 subsection; `tests/test_units.py` pointer comment.
- Pytest: `tests/test_unit_handling_stage0.py` — 6 passed, 1 xfailed; `-m essential` — 30 passed.

## Known limitation (documented)

- `nominal_capacity_as_absolute` areal/absolute parity **not** tested: legacy catches removed
  `pint.errors.PerformanceWarning` → `AttributeError` masks real conversion errors. Gravimetric
  parity only until legacy path fixed (out of scope for Stage 0.4).
