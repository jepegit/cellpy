# Plan for issue #378: Header/unit parity contract tests between cellpy and cellpy-core

## Goal
Prevent silent drift between cellpy's authoritative settings and the verbatim copies in `cellpy-core` by adding a contract test that compares dataclass fields (name + default value) for the shared classes. The test lives in `cellpy` (which imports both packages) and skips when `cellpy-core` is not installed.

## Context / findings
- Authoritative source: `cellpy/parameters/internal_settings.py` defines `@dataclass` classes `HeadersNormal` (l.466), `HeadersSummary` (l.501), `HeadersStepTable` (l.605), `CellpyUnits` (l.367).
- Copies: `cellpy-core/src/cellpycore/legacy.py` carries matching `@dataclass` copies of the same four classes (`CellpyUnits` l.137, `HeadersNormal` l.256, `HeadersSummary` l.291, `HeadersStepTable` l.399).
- Verified the copies match today (e.g. both `CellpyUnits` have `resistance="ohm"` and `pressure="bar"`), so the test passes immediately.
- `HeadersSummary` has non-field members (`postfixes` class attr, `specific_columns`/`areal_*` properties). `dataclasses.fields()` ignores these, so a field-based comparison is clean and unaffected.
- `cellpy-core` is available in cellpy's test envs (e.g. `tests/test_slim.py` imports `cellpycore` directly), so the test runs there; `pytest.importorskip` covers CI where it is absent.
- `CellpyLimits` is intentionally NOT yet ported to `cellpy-core` (the #12 step-table port uses raw-limits by value, no `CellpyLimits` class added), so it is excluded from this contract test per the issue notes.

## Constraints
- Scope: dataclass fields only (name + default), per the issue. No behavioral/runtime assertions.
- Fixture-free, fast, deterministic unit test (matches the project's low-cost test guidance in `.issueflows/04-designs-and-guides/testing-and-coverage.md`).
- Must skip gracefully (not error) when `cellpy-core` is missing.
- One new test file only; no source changes.

## Approach
Add one parametrized test module in `cellpy/tests`:
- `pytest.importorskip("cellpycore.legacy")` at module top so the file is skipped wholesale when cellpy-core is absent.
- Helper `_field_map(cls) -> dict` built from `dataclasses.fields(cls)` mapping `field.name -> field.default`.
- Parametrize over the four class names; for each, fetch the class from `cellpy.parameters.internal_settings` and from `cellpycore.legacy`, build both field maps, and assert equality.
- On mismatch, produce a message that names the drifted fields: keys only in cellpy, keys only in cellpy-core, and keys whose defaults differ (with both values). This makes failures point straight at the drift.

## Files to touch
- `cellpy/tests/test_core_settings_parity.py` (new) - the parametrized contract test described above.

## Test strategy
- Run the new test in the env where cellpy-core is installed: `uv run pytest tests/test_core_settings_parity.py` (expected: 4 passed).
- Graceful skip behavior is covered by `pytest.importorskip` when cellpy-core is absent.

## Status
- [x] Done

Implemented as `tests/test_core_settings_parity.py`; `uv run pytest tests/test_core_settings_parity.py -v` -> 4 passed.

## Open questions (resolved/deferred)
- Assert parity of `HeadersSummary.postfixes`/`specific_columns` (behavioral, not dataclass fields)? Deferred - out of issue scope (fields only).
- Filename: chose `test_core_settings_parity.py`.
- The cellpy working tree also has uncommitted cellpy-core integration (seam) changes; the #378 deliverable is just this one new file and should be committed on its own.
