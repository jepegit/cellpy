# Issue #378: Add header/unit parity contract tests between cellpy and cellpy-core

Source: https://github.com/jepegit/cellpy/issues/378

## Original issue text

## Goal

Add **contract tests** that assert the duplicated settings copies in `cellpy-core`'s
`legacy.py` stay identical to `cellpy`'s authoritative
`cellpy/parameters/internal_settings.py`. This prevents silent drift once `cellpy`
delegates processing to `cellpy-core` (see #377).

## Background

`cellpy-core/src/cellpycore/legacy.py` currently carries **verbatim copies** of:

- `HeadersNormal`, `HeadersSummary`, `HeadersStepTable`
- `CellpyUnits`

Verified field-by-field as identical to `cellpy`'s `internal_settings` today. But nothing
enforces this — if a header/unit is edited in one repo and not the other, the seam will
silently produce mismatched column names or units.

## Tasks

- [ ] Add a test (in `cellpy`, which will import both packages) asserting field names and
      values match for each shared class:
      `HeadersNormal`, `HeadersSummary`, `HeadersStepTable`, `CellpyUnits`.
- [ ] Compare via dataclass fields (name + default value), not just `==`, so the failure
      message points at the drifted field.
- [ ] Mark the test so it is skipped gracefully if `cellpy-core` is not installed.

## Notes

- This depends on `cellpy` actually having `cellpy-core` as a dependency (#377).
- Known cosmetic non-issue to NOT trip over: `CellpyUnits.resistance` value is `"ohm"` in
  both repos; the `"Ohms"` in the docstring is a shared artifact, not a value mismatch.
- `CellpyLimits` is intentionally NOT yet in `cellpy-core`; add it to this contract test
  only once it is ported (cellpy/cellpy-core step-table port).
