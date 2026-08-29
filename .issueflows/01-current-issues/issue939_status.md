# Status — Issue #939: `from_cells` silently drops values that are not cells

- [x] Done

Branch: `939-from-cells-validation`
PR: https://github.com/jepegit/cellpy/pull/974 (#974, draft)
Plan: [issue939_plan.md](issue939_plan.md)

## What's done

- Reproduced on `master` @ `82ab7e03` (3 cells in, 1 out, no warnings).
- Located the real drop site: not `from_cells`, but the bare `continue` in
  `collect_summaries` after `extract_cell_summary` returns `None` for a value
  with no `.data`.
- `Batch.from_cells` now raises `ValueError` naming every value that is not a
  cell and the type that arrived, with an extra `cellpy.get(path)` hint when an
  offender is a path or a string (the reported `rate_file()` /`cellpy_file()`
  trap). Covers the mapping and the sequence form.
- `collect_summaries` now warns (`UserWarning`) and names cells that
  contributed no rows, reusing the `included` bookkeeping it already kept for
  `CollectionMeta.cells_included`. Cells skipped by `only_selected` are not
  reported — those are deliberate.
- "Is a cell" is duck-typed on `.data` asked of the **type**, not the instance:
  `CellpyCell.data` is a property raising `NoDataFound` until something is
  loaded, so an instance-level `hasattr` would answer "not a cell" (and raise)
  for a legitimately empty cell. A strict `isinstance(value, CellpyCell)` was
  rejected because every cell stub in the suite is a `SimpleNamespace`.
- 6 new tests (4 in `test_from_cells.py`, 2 essential + 1 unmarked in
  `test_collect.py`), registered in `test-registry.md`.
- Docs: `docs/getting_started/agents.md` (new `from_cells` guidance), root
  `AGENTS.md` bullet, `batch-load-orchestrator.md` design note. Also repaired
  an orphaned list item in that design doc left by the #950 edit.

## Deviation from the plan

None on substance. Both open questions from the plan were settled with
evidence rather than a guess:

1. **Is the `collect_summaries` warning noisy?** No. A full run with
   `-W always::UserWarning` records the new message **zero** times across
   1744 tests, while still capturing other `UserWarning`s (e.g. the #962
   batch-load warning). The plan's fallback — downgrading it to a debug log —
   was not needed.
2. **Raise or warn in `from_cells`?** Raise, as planned and confirmed.

## Test results

- `uv run pytest tests/test_from_cells.py tests/test_collect.py` — 59 passed.
- `uv run pytest -m essential` — passed.
- `uv run pytest` (full) — 1744 passed, 17 skipped, 15 xfailed, 1 xpassed,
  0 failures.
- `flake8` / `black`: no new findings; the remaining ones are present on
  `master` for the same files.

## Remaining work

- None. Ready for `/iflow-close` (HISTORY bullet lands in the close commit).
