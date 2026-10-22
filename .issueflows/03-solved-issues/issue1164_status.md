# Issue #1164 — status

- [x] Done

## What's done

- `_parse_mpr_log_data` now decodes the `VMP LOG` fields (acquisition start,
  user, directory, file, host, comments). `biol.mpr` starts at
  2017-03-15 10:22:54 instead of midnight.
- `bl_log_pos_dtype` string fields use `S<n>` (numpy 2 safe).
- New test `test_mpr_start_time_from_log` in `tests/test_biologics.py`
  (left unmarked: the essential `tests/test_loader_goldens.py` already
  covers the timestamps through the regenerated golden).
- Regenerated `tests/data/goldens/loader_biologics_mpr/raw.parquet`.
- Bio-Logic, golden, harmonized-raw and v9 tests pass. The essential suite
  shows the same 49 local failures/errors with and without the change
  (missing mdbtools / unixodbc on the dev Mac).

## Notes

- `dev/regenerate_goldens.py` fails with `ModuleNotFoundError: tests` unless
  run as `PYTHONPATH=. uv run python dev/regenerate_goldens.py …` — not
  fixed here.

## Remaining work

None.
