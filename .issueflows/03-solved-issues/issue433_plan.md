# Plan for issue #433: Curve-extraction golden snapshots

## Goal

Commit regenerable golden snapshots of `get_cap` / `get_ccap` / `get_dcap` / `get_ocv`
outputs on the canonical Arbin `.res` cell, with parametrized essential regression tests.

## Approach

1. `tests/curve_golden_support.py` — case registry, shared cell loader (raw → steps →
   summary), curve extraction runner, frame normalization, NullData error cases.
2. Register one golden suite per case in `dev/regenerate_goldens.py` (`curve_*` dirs).
3. `tests/test_curve_goldens.py` — parametrized `@pytest.mark.essential` parity tests.
4. Update `tests/data/goldens/README.md`.

## Case matrix

| Suite | API | Notes |
|-------|-----|--------|
| `curve_get_cap_back_and_forth_c1` | `get_cap(cycle=1)` | default method |
| `curve_get_cap_forth_labeled_c1` | `get_cap(..., method="forth-and-forth", categorical_column=True, label_cycle_number=True)` | cycle/voltage/capacity/direction columns |
| `curve_get_cap_forth_interpolated_c1` | `get_cap(..., method="forth", interpolated=True, number_of_points=100)` | interpolated |
| `curve_get_cap_forth_c12` | `get_cap(cycles=[1,2], method="forth", label_cycle_number=True)` | multi-cycle tidy |
| `curve_get_ccap_c5` | `get_ccap(cycle=5)` | charge only |
| `curve_get_dcap_c5` | `get_dcap(cycle=5)` | discharge only |
| `curve_get_ocv_up_c1` | `get_ocv(cycles=1, direction="up")` | OCV relaxation |
| `curve_get_ccap_null_cycle` | `get_ccap(cycle=999)` | expects `NullData` |
| `curve_get_dcap_null_cycle` | `get_dcap(cycle=999)` | expects `NullData` |

## Files

- `tests/curve_golden_support.py` (new)
- `tests/test_curve_goldens.py` (new)
- `dev/regenerate_goldens.py`
- `tests/data/goldens/README.md`
- `tests/data/goldens/curve_*/`

## Test strategy

- `uv run pytest tests/test_curve_goldens.py -m essential`
- `uv run python dev/regenerate_goldens.py --verify curve_*`
