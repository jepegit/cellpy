# Issue #761: Custom loader silently omits a declared-but-absent column

Source: https://github.com/jepegit/cellpy/issues/761

## Original issue text

## Summary

Found while adding the deliberately-broken fixture set for #655.

When a raw file is missing a column that the instrument definition's `normal_headers_renaming_dict` declares (e.g. `voltage`), the custom loader **loads successfully and silently drops that column** rather than raising or warning. The failure only surfaces much later, downstream, as a `KeyError` when something accesses the (now absent) column.

## Reproduce

`testdata/bad/custom_missing_column.csv` (voltage column removed) loaded via the `custom` instrument with `custom_instrument_001.yml`:

- loads without error, 60 rows
- `voltage` (legacy) / `potential` (native) is absent from `data.raw`
- accessing it raises `KeyError`

Pinned as current behavior in `tests/test_bad_fixtures.py::test_missing_required_column_omits_it_silently`.

## Desired

Loading a file that lacks a declared column should surface a **clear error or warning naming the missing column** at load time, not drop it silently. The desired contract is asserted (currently `xfail`) in `tests/test_bad_fixtures.py::test_missing_column_should_surface_a_clear_error` — when this is fixed, remove the xfail.

## Notes

Low-risk, well-scoped: the fix is a validation step in the custom loader's header-renaming path. Part of the #655 Phase-2 robustness follow-ups.
