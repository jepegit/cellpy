# Plan: issue #479 — Deprecate utils/easyplot on v1.x

## Goal

Emit a module-level `DeprecationWarning` when `cellpy.utils.easyplot` is imported, using
`warn_once`, register in `DEPRECATIONS.md`, point users to `plotutils`/`collectors`.
No functional changes.

## Constraints

- Use existing `cellpy._deprecation.warn_once` (#437/#456).
- Removal version **2.0** (issue #438 decision 5).
- Dead code at `easyplot.py:721–739` stays for #455.

### Prior art

| Hit | Use |
|-----|-----|
| `cellpy/_deprecation.py` | `warn_once`, `_seed_known_deprecations`, DEPRECATIONS.md renderer |
| `cellpy/utils/helpers.py` | `make_new_cell` consumer pattern |
| `tests/test_deprecation_conventions.py` | Warning + registry + DEPRECATIONS.md parity tests |

## Approach

1. Call `warn_once` at module level in `easyplot.py` after imports (fires once per import).
2. Add entry to `_seed_known_deprecations()` for static DEPRECATIONS.md generation.
3. Regenerate `DEPRECATIONS.md` via `python -m cellpy._deprecation`.
4. Add essential test: import warns once, mentions replacement and 2.0 removal.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/utils/easyplot.py` | Module-level `warn_once` |
| `cellpy/_deprecation.py` | Seed easyplot entry |
| `DEPRECATIONS.md` | Regenerated table row |
| `tests/test_deprecation_conventions.py` | Import warning test |

## Test strategy

```bash
conda run -n cellpy_dev_313 pytest -m essential tests/test_deprecation_conventions.py tests/test_easyplot.py -q
```
