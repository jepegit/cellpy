# Issue #989 — status (round 2)

- [x] Done

Branch: `989-capacity-doubling-cellpy-files`. Round 1 log is kept at the
bottom of this file (its status file was superseded by this one).

## What's done

- Root cause confirmed on `local/data/20260316_nor108_01_MLP01.cellpy`:
  no Arbin loader declares `reset_granularity`, so
  `normalize_reset_granularity` returned early; 405 of 902 cycles started
  non-zero, summary doubled on those cycles.
- `harmonize.normalize_reset_granularity`: handles every cumulative column
  present (capacity + energy); undeclared → `PER_CYCLE`; forgotten-reset
  guard rebases cycles whose first value > `CYCLE_START_RTOL` (1 %) of the
  column max; one `UserWarning` with "N of M cycles carried over".
  `PER_TEST` / `PER_STEP` unchanged.
- Kit check 7 (`testing.check_reset_granularity`) asserts cycles start at 0.
- Tests: 5 new in `tests/test_harmonize.py` (guard, legit increment left
  alone, energies, no-cycle-column no-op, kit check teeth).
- Verified on the real frame: cycle 901 → 0.9507 (was 1.9018), cycle 2 tiny
  first value untouched, warning lists 405/403 cycles per column.
- Docs: `AGENTS.md`, `docs/getting_started/agents.md`,
  `migration_v1_to_v2.md`, `harmonized-raw-default.md` (round-2 rationale).
- `uv run pytest -m essential`: 935 passed. Full `uv run pytest`: 1821
  passed. Parity + two-stage loader tests pass (no fixture needed an excuse).
- HISTORY entry under `[Unreleased]`; test registry rows added.

## Remaining work

- None. Follow-up idea (not requested): `CellpyCell.rebase_capacity()`
  helper for existing `.cellpy` files, if users ask.

## Round 1 (2026-09-07, `/iflow-fix` session, branch `989-capacity-calculation-behavior`)

- Docs + `UserWarning` when `normalize_reset_granularity` actually rebases
  `PER_TEST` / `PER_STEP` columns (silent on identity / `PER_CYCLE`).
  Tests in `tests/test_harmonize.py`; note in `get_cap` / agents.md /
  `harmonized-raw-default.md` / migration guide.
- Warning/docs no longer say 2.x unique bit is "last datapoint" (1.x did that
  too). Copy now: rebase so each cycle **starts at 0**.
- Assumed the rebase always ran; it did not for undeclared loaders (round 2).
