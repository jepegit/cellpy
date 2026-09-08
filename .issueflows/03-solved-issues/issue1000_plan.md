# Issue #1000 — plan: journal JSON version field

## Goal

Batch journal JSON files carry a format `version`. Missing → 1. New writes
use `JOURNAL_FORMAT_VERSION` (currently 1). Reads store it and warn when the
file is newer than this cellpy.

## Constraints

- Existing journals without `version` keep loading.
- Do not implement a v2 schema in this issue — only the hook.

### Prior art

- `JOURNAL_FORMAT_VERSION = 1` already in `cellpy/batch/journal.py` but unused.
- `read_journal` / `write_journal` — top-level `info_df` / `metadata` / `session`.

## Approach

1. Top-level JSON key `"version"` (integer).
2. `Journal.version` defaults to 1; `read_journal` fills it (`raw.get("version", 1)`).
3. `write_journal` always writes `JOURNAL_FORMAT_VERSION`.
4. If file version > `JOURNAL_FORMAT_VERSION`, `UserWarning` and still load.

## Files to touch

- `cellpy/batch/journal.py`
- `tests/test_batch_v3.py`
- `HISTORY.md` (close)

## Test strategy

`uv run pytest tests/test_batch_v3.py` plus `uv run pytest -m essential`.

## Open questions

None.
