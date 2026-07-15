# Status — issue #457 (Stage 1.12)

- [x] Done

## 2026-07-15

- A1 (raw), A2 (summary), A3 (journal drop=False) implemented; read path
  normalizes old files to column-keyed frames; storage format untouched.
- Warn-only index lint added (`tests/test_index_lint.py`); Phase D will flip
  it to a hard ban outside `cellpy_file/` and `parameters/legacy/`.
- Eleven characterization tests updated deliberately (each carries a Phase A
  note); `remove_outliers_from_summary_on_index` made column-aware;
  pipeline_smoke goldens regenerated via `dev/regenerate_goldens.py`.
- Full suite: **585 passed, 0 failed**. Benchmark gate: CI (tiered vs GHA
  baselines) on the PR.
