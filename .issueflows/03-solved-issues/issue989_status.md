# Issue #989 status

Interactive `/iflow-fix` session: check capacity calculation behavior
(2.x auto-corrects a forgotten tester capacity reset vs 1.x double-capacity
plot). Reuses existing GitHub #989 rather than creating a duplicate.

- [x] Done

## Iterative fixes log

- 2026-09-07: Docs + `UserWarning` when `normalize_reset_granularity` actually
  rebases `PER_TEST` / `PER_STEP` columns (silent on identity / `PER_CYCLE`).
  Tests in `tests/test_harmonize.py`; note in `get_cap` / agents.md /
  `harmonized-raw-default.md` / migration guide.
- 2026-09-07: Warning/docs no longer say 2.x unique bit is "last datapoint"
  (1.x did that too). Copy now: rebase so each cycle **starts at 0**.
