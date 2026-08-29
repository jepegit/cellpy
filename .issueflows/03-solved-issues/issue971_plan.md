# Issue #971 — plan

## Goal

`ica.dqdv` / `ica.dvdq` raise a clear error when the cycle frame is empty
(missing requested cycle), instead of claiming missing `capacity` /
`direction` / `potential` columns.

## Constraints

- Owner clarification: root cause was missing cycle 4, not a template/API
  column-name bug. Do not rewrite the 04 ICA example.
- Keep the existing "missing column(s)" error for non-empty frames that
  lack the curve columns (`test_a_frame_without_the_curve_columns_says_so`).
- Same pipeline for `dqdv` and `dvdq` — one check in `_resolve_source` /
  `_half_cycles_from_frame`.

### Prior art

- `_half_cycles_from_frame` / `_resolve_source` in `cellpy/ica.py` — column
  check already exists; empty `DataFrame()` has no columns so it hits that
  path first.
- Cell path already treats `len(frame) == 0` as "no half-cycles" and
  returns `[]` (silent empty ICA frame). Raise there too when the extracted
  curve frame is empty.
- Sibling contract tests in `tests/test_ica_api.py`
  (`test_a_frame_without_the_curve_columns_says_so`).
- Toolbox: none relevant.

## Approach

1. If the source `DataFrame` is empty (`frame.empty`), raise `ValueError`
   that the cycle frame is empty / the requested cycle may be missing.
   Run this **before** the required-column check.
2. If a `CellpyCell` extraction returns `None` or 0 rows, raise the same
   error instead of returning `[]`.
3. Leave the missing-column message unchanged for non-empty wrong-schema
   frames.

## Files to touch

- `cellpy/ica.py` — empty-frame check in `_half_cycles_from_frame` and the
  cell branch of `_resolve_source`.
- `tests/test_ica_api.py` — empty `DataFrame()` and empty-with-columns
  cases; optional cell + missing cycle if `get_cap` returns empty.

## Test strategy

- `uv run pytest tests/test_ica_api.py tests/test_ica.py -q`
- Then `uv run pytest -m essential` (merge gate).
- New tests assert `ValueError` matches `empty` (not `missing column`).

## Open questions

- None. Owner comment is the acceptance criterion.
