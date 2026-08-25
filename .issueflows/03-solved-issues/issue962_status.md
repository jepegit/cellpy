# Issue #962 status

- [x] Done

## What's done

- `load_cell` fails with `FileNotFoundError` when filefinder found no raw
  files and no local `.cellpy` exists (was an empty `LOADED` cell).
- `find_files` warns listing unmatched cells.
- `batch.load` `_finalize` warns on any failed cells and points at
  `batch.result.report()`.
- Agent docs mention the FAILED path.

## Remaining work

None.
