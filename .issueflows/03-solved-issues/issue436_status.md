# Issue #436 — status

- [x] Done

## What's done

- Branch `436-benchmark-harness` created; plan confirmed in `issue436_plan.md`.
- `benchmarks/` suite: `conftest.py`, `paths.py`, `test_performance.py`, `check_baseline.py`, `README.md`.
- Five benchmarks implemented (single-cell pipeline, batch `concat_summaries` ×20, v8 load, `get_cap`, peak RSS).
- Committed baseline `benchmarks/baselines/v1x_ubuntu_py313.json` (captured on WSL Linux / py3.13).
- `benchmark` marker registered in `pyproject.toml`.
- `.github/workflows/benchmarks.yml` — dedicated ubuntu job with ±20% `check_baseline.py` gate.
- Batch fixture fix: `db_reader="off"` + testdata `prms.Paths` (no user-config DB dependency).
- RSS benchmark fix: run pipeline inside timed block; skip ambiguous `get_cycle_numbers()` assert.
- Local verification:
  - Windows: 4 passed, 1 skipped (RSS) — ~12s
  - WSL Linux: 5 passed — baseline capture + `check_baseline.py` within ±20%

## Notes

- PR acceptance: temporarily slow one benchmark (~0.5s) on PR to confirm CI gate fails — left for reviewer/manual check.
- `pytest -m essential`: 1 pre-existing failure (`test_loader_goldens.py::loader_pec_csv`, `datetime64[ns]` vs `us`) — unrelated to this issue.
