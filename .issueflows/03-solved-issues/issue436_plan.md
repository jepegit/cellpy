# Plan: issue #436 — Stage 0.9 benchmark harness + v1.x baselines

## Goal

Add a `pytest-benchmark` suite under `benchmarks/` (outside default `pytest` discovery),
capture v1.x performance baselines on the canonical golden cells, and gate regressions in a
dedicated Linux CI job with a ±20% band — closing **G8** and unblocking polars Phase A.

## Constraints

- **Baselines before polars** — JSON captured on current v1.x `master`; values are the
  ruler for all later refactors (release plan §4, polars plan Phase D).
- **Not in default CI** — `benchmarks/` must not run in the Tier-1 `essential` job; own
  workflow on a **fixed runner** (`ubuntu-latest` only for compare).
- **`pytest-benchmark` already in dev deps** — do not add `asv` or new timing frameworks.
- **Golden inputs only** — reuse committed Stage-0 fixtures (`testdata/`, `tests/data/goldens/`);
  no network, no `dev_data/`.
- **Depends on Stage 0.1** — canonical Arbin `.res`, v8 `.h5`, and pipeline smoke path exist
  (`tests/test_goldens.py`, `tests/fdv.py`).
- **Issue scope is v8 load** — release plan also mentions v9; defer v9 benchmark until v9
  format lands (note in `benchmarks/README.md`, not a blocker for this issue).

### Prior art

- [cellpy2-release-and-branching-plan.md](../../architecture-plan/cellpy2-release-and-branching-plan.md) §4 — harness shape, metrics list, ±20%, acceptance for 2.0.
- [cellpy2-polars-port-execution-plan.md](../../architecture-plan/cellpy2-polars-port-execution-plan.md) Phase D — benchmarks run before/after Phase C flip.
- `cellpy-core/tests/test_benchmarks.py` — opt-in `pytest.mark.benchmark`, no CI gate
  (cellpy **adds** the gate per issue acceptance).
- `tests/test_goldens.py` — `_run_pipeline_smoke()` = `from_raw → make_step_table → make_summary`
  on `20160805_test001_45_cc_01.res` (reuse for benchmark #1).
- `tests/fdv.py` — `cellpy_file_path_v8`, `res_file_name`, batch paths.
- `tests/test_cellpy.py:124` — legacy `@pytest.mark.benchmark` on diagnostics load (leave
  in place or migrate later; new suite lives under `benchmarks/`).
- `dev/regenerate_goldens.py` / `tests/golden_support.py` — golden conventions; benchmarks
  read the same files, do not duplicate oracle logic.
- `.issueflows/00-tools/` — no benchmark helper yet; add `capture_baselines.sh` only if a
  one-liner wrapper helps (optional).

## Approach

### 1. Layout (`benchmarks/` at repo root)

```
benchmarks/
  README.md              # how to regen baselines, CI expectations, metric list
  conftest.py            # paths, module fixtures, RSS helper, compare hook
  test_performance.py    # five benchmark functions
  baselines/             # committed pytest-benchmark JSON (Linux / py3.13 / ubuntu)
```

- Register `benchmark` marker in `pyproject.toml` (document opt-in; default `addopts` unchanged
  because collection root stays `tests/`).
- Each benchmark: `pytest.mark.benchmark` + stable `group`/`name` for compare keys.

### 2. Five metrics (match issue + release plan)

| # | Benchmark | Implementation sketch |
|---|-----------|----------------------|
| 1 | **Single-cell pipeline** | Reuse `_run_pipeline_smoke()` pattern: `CellpyCell.from_raw(RES)` → `make_step_table()` → `make_summary()`. |
| 2 | **20-cell batch summary collection** | Module fixture: 20 `CellpyCell` loaded from the same v8 `.h5` (or minimal `Batch` journal with 20 pages → `update()`). Time `BatchSummaryCollector` data-collection path only (not plot). Setup outside `benchmark()` callable. |
| 3 | **v8 cellpy-file load** | `cellpy.get(fdv.cellpy_file_path_v8, testing=True)` or `CellpyCell.load()` on v8 oracle. |
| 4 | **`get_cap` all cycles** | Load canonical cell once (module scope); benchmark `get_cap(cycle=None)` or loop all cycle numbers from `get_cycle_numbers()`. |
| 5 | **Peak RSS (informational)** | In benchmark teardown on Linux: `resource.getrusage(RUSAGE_SELF).ru_maxrss` (KiB). Record via `benchmark.extra_info`; **optional gate** — log + store in baseline JSON; do not fail CI on RSS in v1 unless trivial to stabilize. |

Warmup: enable `warmup=True` / `warmup_iterations=1` on noisy paths (loader IO).

### 3. Baseline capture + JSON commit

1. On **`ubuntu-latest`** (match CI):  
   `uv run pytest benchmarks/ --benchmark-only --benchmark-autosave --benchmark-save=v1x`
2. Copy the generated save from `.benchmarks/Linux-CPython-3.13-64bit/` into
   `benchmarks/baselines/v1x_ubuntu_py313.json` (committed, stable path).
3. `conftest.py` configures compare against that file on CI via  
   `--benchmark-compare=v1x --benchmark-compare-fail=mean:20%`  
   (or equivalent hook if pytest-benchmark needs the save name registered).

Document regen command in `benchmarks/README.md`. Baselines are **runner-class specific** —
do not compare macOS/Windows saves against Linux CI.

### 4. CI job (new workflow)

Add `.github/workflows/benchmarks.yml`:

- **Triggers:** `pull_request` + `push` to `master` (paths: `benchmarks/**`, `cellpy/**`, `pyproject.toml`, workflow file).
- **Job:** single `ubuntu-latest`, `uv sync`, `apt` deps same as `ci.yml` (mdbtools).
- **Run:**  
  `uv run pytest benchmarks/ --benchmark-only --benchmark-compare=v1x --benchmark-compare-fail=mean:20%`
- **Not** part of `ci.yml` essential job — keeps merge gate fast.

### 5. Acceptance sanity check (PR)

In the PR description / manual step: temporarily add `time.sleep(0.5)` inside one benchmarked
callable, push, confirm the benchmarks workflow **fails**, revert before merge.

### 6. Optional cleanup (low priority)

- Note in `benchmarks/README.md` that `tests/test_cellpy.py` diagnostics benchmark predates
  this harness; migrate or leave for a follow-up.

## Files to touch

| Path | Change |
| --- | --- |
| `benchmarks/README.md` | New — metrics, regen, CI, v9 deferral |
| `benchmarks/conftest.py` | New — fixtures, baseline compare config, RSS helper |
| `benchmarks/test_performance.py` | New — five benchmarks |
| `benchmarks/baselines/v1x_ubuntu_py313.json` | New — committed baseline (captured on Linux) |
| `pyproject.toml` | Add `benchmark` marker; optional `[tool.pytest.ini_options] testpaths` note in README only (keep default discovery) |
| `.github/workflows/benchmarks.yml` | New — dedicated compare job |
| `.issueflows/01-current-issues/issue436_status.md` | Created in `/iflow-start` |

## Test strategy

- **Local:** `uv run pytest benchmarks/ --benchmark-only` (no compare) during development.
- **Baseline regen:** command in README; run on Linux before committing JSON.
- **Regression gate:** `benchmarks.yml` on PR.
- **Suite health:** existing `uv run pytest -m essential` must stay green (benchmarks excluded).
- **PR proof:** one-off artificial slowdown → CI red → revert.

## Open questions

1. **20-cell batch setup** — synthetic 20× same v8 file (simple, deterministic) vs real
   multi-cell batch project JSON (more realistic, heavier fixture)? **Recommend:** 20× same v8
   load into a minimal `Batch`/`BatchSummaryCollector` path unless you want realism over speed.
2. **RSS gating** — record only in v1 baseline, or fail CI on RSS regression too? **Recommend:**
   record in `extra_info`, wall-time gate only for this issue.
3. **Baseline capture location** — capture JSON in CI `workflow_dispatch` on `master` after merge
   vs capture locally on WSL/Linux before first PR? **Recommend:** capture in CI once workflow
   exists, commit JSON in same PR if runner output is stable across reruns.

## Scope check

Single cohesive deliverable (~1–2 days): harness + baselines + CI gate. No polars work, no
production refactors. **Do not split** unless 20-cell batch setup balloons — then park batch
benchmark as a follow-up issue (unlikely).
