# Issue #432: Stage 0.5: Per-loader golden snapshots of current loader outputs

Source: https://github.com/jepegit/cellpy/issues/432

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

For every tier-1/2 instrument loader with test files available (`arbin_res`, `maccor_txt`,
`neware_txt`, `pec_csv`, `custom`; then the arbin_sql/neware xlsx/nda family), commit a
golden snapshot of **today's** loader output: the raw frame (parquet), `raw_units`, and the
meta attributes the loader sets — regenerated via the Stage 0.1 script.

## Why

The loader port introduces a shared `harmonize()` stage producing native harmonized raw;
its per-loader parity tests need an oracle of current behavior to map against (loader plan
Step 0 / §5). The reset-granularity property test — the correctness landmine of the port —
compares against exactly these snapshots. For ODBC-dependent loaders (`arbin_res` on CI
without the Access driver), the committed snapshot *is* the oracle, same trick cellpy-core
uses for its golden parquet.

## Links

- `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` (Step 0, §5 tests, §6 ODBC risk)
- `cellpy-core/.issueflows/04-designs-and-guides/test-data-and-fixtures.md`
- Depends on Stage 0.1.

## Acceptance

- One snapshot set per tier-1 loader committed (tier-2 where test files exist).
- A parametrized test loads each vendor file and asserts frame/units/meta equality with the
  snapshot; skipped (not failed) where the driver/file is unavailable, with the snapshot
  still asserted against regeneration on machines that can.
