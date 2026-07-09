# Golden fixture suites

Committed regression oracles for cellpy 2 Stage 0 characterization work.

**Do not edit files here by hand.** Regenerate with:

```bash
uv run python dev/regenerate_goldens.py
```

Full convention, naming rules, and how to add suites: [`../../README.md`](../../README.md).

## Suites

| Suite | Source | Artifacts |
|-------|--------|-----------|
| `pipeline_smoke` | `testdata/data/20160805_test001_45_cc_01.res` | `summary.parquet`, `metrics.json` |
