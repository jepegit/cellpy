# cellpy performance benchmarks (Stage 0.9 / issue #436)

Opt-in `pytest-benchmark` suite measuring v1.x wall time on committed golden cells.
Excluded from the default `pytest` run (lives outside `tests/`). A dedicated GitHub
Actions workflow compares results against a committed baseline captured on
**ubuntu-latest**.

## Metrics

| Benchmark | What it measures |
| --- | --- |
| `test_benchmark_single_cell_pipeline` | `from_raw` → `make_step_table` → `make_summary` (canonical Arbin `.res`) |
| `test_benchmark_batch_summary_collection` | `concat_summaries` on 20 cells (same data path as `BatchSummaryCollector`) |
| `test_benchmark_v8_cellpy_file_load` | `cellpy.get()` on the v8 cellpy-file oracle |
| `test_benchmark_get_cap_all_cycles` | `get_cap(cycle=None)` on a pre-built cell |
| `test_benchmark_peak_rss_kib` | Peak RSS via `resource.getrusage` (Linux only; informational, not compare-gated) |

**Deferred:** v9 cellpy-file load — add when the v9 format lands (release plan §4).

## Commands

From the repo root:

```bash
# Local timing (no regression gate)
uv run pytest benchmarks/ --benchmark-only

# Capture baseline on **GitHub Actions ubuntu-latest** (commit the JSON).
# Do **not** capture on local WSL/macOS/Windows — use the GHA capture job so the
# ruler matches the compare runner.
#
# Recommended: run the **Benchmarks** workflow via *workflow_dispatch* (capture job)
# and download the `v1x-baseline` artifact, or copy means from a green GHA log.
uv run pytest benchmarks/ --benchmark-only --benchmark-save=v1x \
  --benchmark-json=benchmarks/baselines/v1x_ubuntu_py313.json

# Regression gate (fail only if slower than baseline by more than 20%) — CI uses this
uv run pytest benchmarks/ --benchmark-only --benchmark-json=/tmp/bench.json
uv run python benchmarks/check_baseline.py /tmp/bench.json benchmarks/baselines/v1x_ubuntu_py313.json
```

Baselines are **runner-class specific**. Do not compare a macOS/Windows capture against
Linux CI.

## CI

See `.github/workflows/benchmarks.yml` — runs on `ubuntu-latest` only, separate from the
Tier-1 `essential` merge gate. The compare job **fails only on slowdown** (>20% slower than
baseline); faster runs pass. Rebaseline on GHA when a speedup should become the new ruler.

To refresh the committed baseline on the real CI runner, trigger the workflow manually
(*Actions → Benchmarks → Run workflow*). The `capture-baseline` job uploads
`benchmarks/baselines/v1x_ubuntu_py313.json` as an artifact.

## Legacy

`tests/test_cellpy.py` contains an older `@pytest.mark.benchmark` on diagnostics load;
new work belongs here under `benchmarks/`.
