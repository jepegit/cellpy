# Issue #436: Stage 0.9: Benchmark harness + v1.x performance baselines

Source: https://github.com/jepegit/cellpy/issues/436

## Original issue text

> Part of **Stage 0 â€” foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

A `pytest-benchmark` suite under `benchmarks/` (excluded from the default test run, own CI
job) measuring, on the committed golden cells:

- single-cell `load â†’ make_step_table â†’ make_summary` wall time,
- 20-cell batch summary collection,
- v8 cellpy-file load,
- `get_cap` over all cycles,
- peak RSS where cheap to record.

Baselines captured on **current master (v1.x)** and committed as JSON; the CI job compares
against them with a Â±20% band.

## Why

Gap item G8: the polars/headers flips are justified by performance, but without a baseline
captured *before* de-indexing Phase A starts, "faster" is folklore. The release plan sets
"no metric slower than 1.x" as a 2.0 acceptance criterion â€” this issue creates the ruler.

## Links

- `architecture-plan/cellpy2-release-and-branching-plan.md` (Â§4 â€” this issue implements it)
- `architecture-plan/cellpy2-polars-port-execution-plan.md` (Phase D enforcement)
- Depends on Stage 0.1 (golden cells), blocks the start of polars Phase A.

## Acceptance

- Baseline JSON committed; CI job green and demonstrably failing when a benchmark is
  artificially slowed (one-off sanity check in the PR).


