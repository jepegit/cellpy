# Issue #467: test: Stage 0.9 benchmark harness with v1.x baselines (#436)

Source: https://api.github.com/repos/jepegit/cellpy/issues/467

> **Note:** GitHub `#467` is a **merged pull request** (not a standalone tracking issue). It closed jepegit/cellpy#436 (Stage 0.9 benchmark harness).

## Original issue text

## Summary

- Adds an opt-in `pytest-benchmark` suite under `benchmarks/` measuring five v1.x performance metrics on committed golden cells (single-cell pipeline, 20-cell batch summary collection, v8 load, `get_cap`, peak RSS).
- Commits a Linux baseline JSON (`benchmarks/baselines/v1x_ubuntu_py313.json`) and a `check_baseline.py` comparator with a ±20% mean wall-time gate.
- Introduces a dedicated `.github/workflows/benchmarks.yml` job on `ubuntu-latest`, separate from the Tier-1 `essential` merge gate.

Closes #436.

## Test plan

- [x] `pytest benchmarks/ --benchmark-only` — 4 passed, 1 skipped (RSS) on Windows; 5 passed on WSL Linux
- [x] `python benchmarks/check_baseline.py` — within ±20% on WSL after baseline capture
- [x] `ruff check benchmarks/` — clean
- [ ] CI `Benchmarks` workflow green on this PR
- [ ] Optional acceptance check: temporarily slow one benchmark (~0.5s), confirm CI fails, revert

## Notes

- Peak RSS is recorded on Linux only and is **not** compare-gated.
- `pytest -m essential` has one pre-existing failure (`loader_pec_csv` golden, `datetime64[ns]` vs `us`) unrelated to this change.

Made with [Cursor](https://cursor.com)
