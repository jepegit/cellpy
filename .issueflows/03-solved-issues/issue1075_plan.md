# Issue #1075 plan

## Goal

`filefinder` can parse `<date>_<project><number>` stems and return the run
number, or `None` on a miss. No I/O.

## Approach

Add `parse_project_run_number(name, project) -> int | None` in
`cellpy/readers/filefinder.py`. Digit date prefix, case-insensitive exact
project token, digits immediately after the token (so `SAL` ≠ `SALAMANDER`),
optional `_suffix` / extension. Tests only.

## Files to touch

- `cellpy/readers/filefinder.py`
- `tests/test_filefinder.py`
- `HISTORY.md` (close)

## Test strategy

Parametrized unit tests for the must-match / must-miss examples. Mark
essential so Tier 1 CI covers them.

## Constraints

### Prior art

- `filefinder.search_for_files` already uses `file_name_format`
  `YYYYMMDD_[name]EEE_CC_TT_RR` — coexist; this helper is a narrow parse, not
  a glob rewriter.
- No toolbox script for filename parsing.

## Open questions

None — spec examples are the oracle.
