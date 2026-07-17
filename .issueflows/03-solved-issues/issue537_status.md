# Issue #537 status — journal-page column literals → HeadersJournal

- [x] Done

## Outcome

All 6 `HeadersJournal` scan findings removed (3 lines):

- `cellpy/utils/batch_tools/batch_plotters.py` — `hdr_journal["mass"|"loading"|"label"]`
  and `["group"|"sub_group"]` → attribute access.
- `cellpy/utils/helpers.py` — `hdr_journal["loading"]` → `hdr_journal.loading`.

Scan tool now reports **0 `HeadersJournal` findings** for both files.

## Verification

- Attribute values confirmed equal to subscript values (byte-identical behavior).
- `tests/test_batch.py` + `tests/test_helpers.py`: 58 passed post-edit.
- Full suite baseline green (668 passed; the single Windows-only HDF5
  `driver lock request failed` setup error on `test_has_no_full_duplicates` is
  a pre-existing test-isolation flake — passes in isolation, not on the Linux
  CI gate).
- ruff: no new findings vs master.

## Out of scope (other issues)

- Raw/steps/summary literals in the same files → #538.
