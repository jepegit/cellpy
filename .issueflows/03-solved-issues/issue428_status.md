# Issue #428 status: Golden-fixture convention and regeneration tooling

- [x] Done

## What's done

- Added `dev/regenerate_goldens.py` — `@register_golden_suite` registry, CLI,
  `--verify` byte-identical check, shared parquet/JSON writers.
- Toy suite **`pipeline_smoke`** (canonical Arbin `.res` → step table → summary):
  `tests/data/goldens/pipeline_smoke/summary.parquet`, `metrics.json` (103 / 18 / 1457).
- Added `tests/test_goldens.py` — two `@pytest.mark.essential` tests (metrics + summary parquet).
- Documentation: `tests/README.md`, `tests/data/goldens/README.md`, cross-link in
  `testing-and-coverage.md`.

## Verification

- `uv run python dev/regenerate_goldens.py --verify pipeline_smoke` — byte-identical.
- `uv run pytest tests/test_goldens.py -v` — 2 passed.
- `uv run pytest -m essential --ignore=tests/test_plotutils_summary_plot.py` — 18 passed
  (includes new golden tests).

## Remaining work

None.
