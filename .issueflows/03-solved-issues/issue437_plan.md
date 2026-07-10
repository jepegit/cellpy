# Issue #437 — plan

## Goal

Bootstrap shared conventions machinery: `warn_once` deprecation helper with registry, `DEPRECATIONS.md` rendering, exception-tree stubs, and a contributing-doc checklist line.

## Constraints

- No import-time logging changes (out of scope).
- Keep existing `cellpy.exceptions` classes importable (backward compatible).
- Logging helper must warn once per call site, not per invocation loop.
- Plan reference: `architecture-plan/cellpy2-conventions-plan.md` §1, §3, §5.

### Prior art

- `cellpy/exceptions.py` — legacy flat exception tree rooted at `Error`.
- `cellpy/utils/helpers.py::make_new_cell` — ad-hoc `warnings.warn(..., DeprecationWarning)`.
- `cellpycore.exceptions.CellpyError`, `NoDataFound` — core root exceptions.
- `tests/test_cell_readers.py::test_deprecations` — xfail deprecation test (unrelated path).
- None in `00-tools/` for deprecation rendering.

## Approach

1. Add `cellpy/_deprecation.py` with `warn_once`, in-memory registry, `render_deprecations_md()`, and `write_deprecations_md()`.
2. Wire `helpers.make_new_cell` as first consumer via `warn_once`.
3. Extend `cellpy/exceptions.py`: re-export `CellpyError`; add stub subclasses `CorruptCellpyFile`, `ConfigurationError`, `UnitsError`, `LoaderError`; keep legacy exceptions unchanged.
4. Commit generated `DEPRECATIONS.md` (seed known entry for `make_new_cell`).
5. Add `tests/test_deprecation_conventions.py` covering once-per-site warnings, registry render, and exception stubs.
6. Add one checklist line to `CONTRIBUTING.md` under pull-request guidelines.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/_deprecation.py` | New helper module |
| `cellpy/exceptions.py` | Re-export `CellpyError`, add stub exceptions |
| `cellpy/utils/helpers.py` | Use `warn_once` in `make_new_cell` |
| `DEPRECATIONS.md` | Generated deprecation table |
| `tests/test_deprecation_conventions.py` | New tests |
| `CONTRIBUTING.md` | Test-convention checklist line |

## Test strategy

`uv run pytest tests/test_deprecation_conventions.py -m essential` and `uv run pytest -m essential`.

## Open questions

- None — scope is bounded to bootstrap machinery per issue acceptance criteria.
