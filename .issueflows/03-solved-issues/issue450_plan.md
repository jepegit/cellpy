# Plan: issue #450 — Units Phase 1 (one registry)

## Goal

Single pint registry per process: re-export `CellpyUnits` and `Q` from cellpycore,
remove cellpy-local registry in `data_structures.py`, rename confusing `core` alias in
`cellreader.py`, flip interop test to hard pass.

## Constraints

- No numeric behavior changes; parity tests must stay green.
- Read `cellpy-core-migration.md`: PyPI pin only; no cellpy-core code changes in this PR.
- Rename only `cellreader.py`'s `data_structures as core` — leave other modules' `core` aliases untouched.

### Prior art

| Hit | Use |
|-----|-----|
| `tests/test_unit_handling_stage0.py` | strict-xfail interop test to flip |
| `tests/test_core_settings_parity.py` | CellpyUnits field parity (#378) |
| `cellpycore.legacy.CellpyUnits` | already re-exports `cellpycore.units.CellpyUnits` |
| `cellpy/readers/data_structures.py` | local `_ureg` / `Q` to remove |

## Approach

1. **`internal_settings.py`**: delete local `CellpyUnits` class; `from cellpycore.units import CellpyUnits`.
2. **`data_structures.py`**: remove `_ureg`/`ureg`/`get_ureg`/local `Q`; `from cellpycore.units import Q`.
3. **`cellreader.py`**: `data_structures as ds`; replace `core.` → `ds.` (not `self.core.`).
4. **Tests**: remove xfail; add one-registry assert via `_get_unit_registry()`.
5. **`test_core_settings_parity`**: compare against `cellpycore.units.CellpyUnits` (identity after re-export).

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/parameters/internal_settings.py` | Re-export CellpyUnits |
| `cellpy/readers/data_structures.py` | Re-export Q, drop local registry |
| `cellpy/readers/cellreader.py` | Rename `core` → `ds` module alias |
| `tests/test_unit_handling_stage0.py` | Flip interop test |
| `tests/test_core_settings_parity.py` | Optional: note identity |

## Test strategy

```bash
conda run -n cellpy_dev_313 pytest -m essential tests/test_unit_handling_stage0.py tests/test_core_settings_parity.py -q
conda run -n cellpy_dev_313 pytest -m essential --ignore=tests/test_plotutils_summary_plot.py -q
```
