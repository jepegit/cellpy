# Issue #476 — plan

## Goal

Fix the Windows `loader_pec_csv` essential golden failure and make the benchmark
baseline gate tolerant of normal CI noise: **warn** on moderate slowdowns, **fail**
only on extreme regressions (>100%).

## Constraints

- **Behavior-preserving:** no loader or production code changes unless required for
  the golden fix (Part 1 should be test-helper only).
- **Essential gate:** `test_loader_raw_matches_golden_parquet[loader_pec_csv]` must
  pass on Windows and Linux.
- **Benchmark ruler unchanged:** do not rebaseline JSON in this PR unless a deliberate
  speed change is documented — the CI failure in the issue (26.6% slowdown) should
  become a warning, not a pass-by-rebaseline.
- **Stage 0.9 contract:** keep the dedicated `benchmarks.yml` workflow; peak RSS stays
  compare-exempt.

### Prior art

- [`tests/loader_golden_support.py`](../../tests/loader_golden_support.py) —
  `assert_raw_matches_golden()` compares `date_time` / `step_time` / `test_time` via
  epoch-ns tolerance; all other columns use strict `assert_frame_equal` (dtype-sensitive).
- [`tests/golden_support.py`](../../tests/golden_support.py) — same pattern for summary
  goldens (`date_time` only).
- [`cellpy/readers/instruments/pec_csv.py`](../../cellpy/readers/instruments/pec_csv.py) —
  adds `position_start_time` as `pd.to_datetime` (PEC-only datetime column).
- [`benchmarks/check_baseline.py`](../../benchmarks/check_baseline.py) — single ±20%
  fail threshold; used by [`.github/workflows/benchmarks.yml`](../../.github/workflows/benchmarks.yml).
- [`benchmarks/README.md`](../../benchmarks/README.md) — documents the 20% gate.
- **Toolbox:** no existing helper; add small unit tests for `check_baseline.compare()`.

## Approach

### Part 1 — `loader_pec_csv` golden on Windows

**Root cause:** `position_start_time` is datetime64 on both sides but not listed in
`DATETIME_LIKE_COLUMNS` (only `date_time`). It lands in the strict `exact_cols`
branch → pandas compares `datetime64[ns]` (Windows load) vs `datetime64[us]` (parquet
golden from Linux CI).

**Fix:** In `assert_raw_matches_golden()` (and the matching path in
`prepare_raw_for_golden` if needed), **auto-detect temporal columns** from dtypes:

```python
def _temporal_columns(actual, expected):
    cols = set(DATETIME_LIKE_COLUMNS) | set(TIMEDELTA_LIKE_COLUMNS)
    for frame in (actual, expected):
        for col in frame.columns:
            if pd.api.types.is_datetime64_any_dtype(frame[col]):
                cols.add(col)
            elif pd.api.types.is_timedelta64_dtype(frame[col]):
                cols.add(col)
    return cols
```

Use `_temporal_columns()` for the temporal vs exact split and for
`assert_temporal_series_equal()` (already normalizes to ns epoch int64).

Explicitly add `position_start_time` to `DATETIME_LIKE_COLUMNS` only if we prefer
minimal diff — **prefer auto-detect** so future loader datetime columns don't repeat
this failure.

No parquet regeneration expected (values match; dtype comparison was the bug).

### Part 2 — Tiered benchmark baseline gate

Replace the single hard-fail at +20% with two bands (issue spec):

| Ratio vs baseline | Action |
|-------------------|--------|
| ≤ 1.20 (+20%) | Pass silently |
| > 1.20 and ≤ 2.0 (+20% … +100%) | **`warnings.warn()`** with benchmark name, means, ratio — exit 0 |
| > 2.0 (+100%) | **Fail** (exit 1), same message shape as today |

Implementation in `benchmarks/check_baseline.py`:

- Refactor `compare()` → return `(warnings: list[str], failures: list[str])` or a
  small result dataclass.
- `main()`: print warnings to stderr, return 1 only if `failures` non-empty.
- CLI flags: `--warn-tolerance 0.20` (default), `--fail-tolerance 1.0` (default =
  +100% slowdown → ratio 2.0). Keep backward-compatible `--tolerance` as alias for
  `--warn-tolerance` if useful.

Update docs:

- `benchmarks/README.md` — describe warn vs fail bands.
- `.github/workflows/benchmarks.yml` step comment (no workflow logic change beyond
  what the script does).

**Not in scope:** increasing `pytest-benchmark` rounds/min_time (noise reduction) —
only revisit if warnings still flood CI after the tiered gate.

## Files to touch

| Path | Change |
|------|--------|
| [`tests/loader_golden_support.py`](../../tests/loader_golden_support.py) | Auto-detect datetime/timedelta columns in golden compare |
| [`benchmarks/check_baseline.py`](../../benchmarks/check_baseline.py) | Tiered warn (+20%) / fail (+100%) logic |
| [`benchmarks/README.md`](../../benchmarks/README.md) | Document new gate behavior |
| [`.github/workflows/benchmarks.yml`](../../.github/workflows/benchmarks.yml) | Update step description |
| [`tests/test_check_baseline.py`](../../tests/test_check_baseline.py) | **New** — unit tests for compare bands with synthetic JSON |

## Test strategy

```bash
uv run pytest tests/test_loader_goldens.py::test_loader_raw_matches_golden_parquet[loader_pec_csv] -v
uv run pytest tests/test_check_baseline.py -v
uv run pytest -m essential --ignore=tests/test_plotutils_summary_plot.py
```

**New tests (`tests/test_check_baseline.py`):**

- ratio 1.10 → no warn, no fail
- ratio 1.30 → warn, exit 0
- ratio 2.50 → fail
- peak RSS benchmark name still skipped

**Manual verify (optional):** run `check_baseline.py` against the CI log means from
the issue (batch_summary ratio 1.266) — should warn, not fail.

**Branch:** create `476-golden-benchmark-fixes` from updated `master` (current
`446-format-spec` is stale; run `/iflow-cleanup` or `git switch master && git pull`
first).

## Open questions

1. **Warning channel:** `warnings.warn()` (pytest captures in logs) vs `print(..., file=sys.stderr)` — recommend stderr print so GHA logs show yellow-style visibility without pytest warning filters.
2. **Rebaseline:** Confirm we do **not** refresh `v1x_ubuntu_py313.json` in this PR (issue slowdown becomes warn-only).

---

**Confirm:** Accept / Revise / Abort
