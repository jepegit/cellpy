# Status — Iterative fixes: New cellpy-core release

Interactive `/iflow-fix` session. GitHub issue was not created (`gh` write is
blocked in this environment). Work lands on `cursor/cellpycore-pin-0-2-6-4828`.

- [ ] Done

## Iterative fixes log

- **2026-09-08** — Pin `cellpycore` `0.2.5`→`0.2.6` in `pyproject.toml` /
  `uv.lock`. Drop strict xfails on `test_empty_tail_is_noop` (core#147) and
  `test_gap_append_mid_step_equals_full_load` (core#148). Update
  `tests/README.md`, pin-gate doc, and `HISTORY.md`. Leave conda env YAMLs on
  `0.2.4` (conda-forge latest).
  - `uv sync --no-sources` → `cellpycore 0.2.6`
  - `tests/test_incremental_update.py`: 7 passed (both former xfails now pass)
  - `pytest -m essential`: 845 passed, 64 skipped, 0 xfailed
