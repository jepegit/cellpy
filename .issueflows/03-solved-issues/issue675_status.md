# Issue #675 status

Interactive `/iflow-fix` session (yolo close).

- [x] Done

## Iterative fixes log

- **2026-07-24** — Pin `cellpycore` `0.2.3` → `0.2.4` in `pyproject.toml` / `uv.lock` (`UV_NO_SOURCES=1 uv lock`).
- **2026-07-24** — Sync `HeadersSummary` with core EFC fields (`cumulated_capacity_throughput`, `equivalent_full_cycles`); regen `pipeline_smoke` goldens; leave conda YAMLs on `0.2.3` until conda-forge publishes `0.2.4`.
- **2026-07-24** — `uv run pytest -m essential`: 606 passed, 13 skipped.
- **2026-07-24** — Commit `ca70c001` pushed on `675-pin-cellpycore`. PR create blocked by GitHub API 500 (status: Partially Degraded Service). Retry: `gh pr create` or https://github.com/jepegit/cellpy/pull/new/675-pin-cellpycore
