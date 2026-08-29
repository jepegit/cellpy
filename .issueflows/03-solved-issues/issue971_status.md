# Issue #971 — status

- [x] Done

## What's done

- Captured original + owner comment (empty cycle frame, not template bug).
- Plan written (yolo auto-accept).
- Empty cycle frame now raises `ValueError` ("cycle frame is empty") before the
  missing-column check; same for a `CellpyCell` whose `get_cap` returns no rows.
- Tests: empty `DataFrame()`, empty-with-columns, missing cycle on a cell.
  Marked `@pytest.mark.essential`. `tests/test_ica_api.py` + `tests/test_ica.py`:
  51 passed. Full suite: 1547 passed. Essential: 776 passed.
- HISTORY bullet under `[Unreleased]`.

## Remaining work

- None.
