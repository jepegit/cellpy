# Issue #428: Stage 0.1: Golden-fixture convention and regeneration tooling

Source: https://github.com/jepegit/cellpy/issues/428

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see [issue #439](issue439_original.md) / [GitHub #439](https://github.com/jepegit/cellpy/issues/439)). Plan documents live in the **`architecture-plan`** repository (`cellpy-workspace/architecture-plan/`, alongside `cellpy` and `cellpy-core`). *(They used to sit in `code-reviews/`; that folder is no longer the home for these plans.)*

## Goal

One shared convention for all cellpy-2 characterization/parity fixtures in the cellpy repo:
committed golden files under `tests/data/goldens/` (parquet for frames, JSON for dicts/meta),
regenerated **only** by a script (`dev/regenerate_goldens.py` with per-suite registration),
never edited by hand.

## Why

Five plan documents each specify characterization or parity tests
(cellpy-file round-trip, loader snapshots, curve snapshots, converter parity, value-parity
oracle). Without one convention we get five ad-hoc fixture styles that drift. cellpy-core
already solved this (committed golden parquet + `dev/regenerate_test_data.py`); adopting the
same mechanics keeps cross-repo parity oracles comparable. This is item **F8** in the gap
analysis and a dependency of Stage-0 issues 0.2, 0.5, 0.6, 0.7 and 0.9.

## Links

- `architecture-plan/cellpy2-plans-gap-analysis.md` (F8)
- `cellpy-core/.issueflows/04-designs-and-guides/test-data-and-fixtures.md` (the pattern to adopt)
- `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` (Step 0 uses this)

## Tasks

- [ ] Directory layout + naming convention (`tests/data/goldens/<suite>/<name>.parquet|.json`)
- [ ] `dev/regenerate_goldens.py` skeleton with a registration decorator per suite
- [ ] Short README section in `tests/` documenting the rule ("goldens are regenerated, never edited")
- [ ] Note on the `essential` pytest marker usage for the fast subsets

## Acceptance

- Running the script twice produces byte-identical goldens (deterministic).
- At least one suite (can be a toy one) registered and exercised in CI.
