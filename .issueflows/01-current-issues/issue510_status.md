# Issue #510 — status

- [ ] Done

## What's done

- Plan confirmed (2026-07-17): v9 zip-of-parquet + `.cellpy`, default write v9, native cols; three milestones A→B→C.
- **Milestone A (V2-13)** — merged via PR #521.
- **Milestone B (V2-14)** — merged via PR #522 (2026-07-17).
- GitHub issue #510 closed as completed when B landed (plan allowed closing after B and tracking C as release checklist).
- **Milestone C (V2-15) started** on branch `510-v2-release-discipline-milestone-c`:
  - Draft user guide: `docs/getting_started/migration_v1_to_v2.md` (linked from getting-started toctree + HISTORY + data-structure note)

## Remaining work

- **C (V2-15):**
  - [x] v1→v2 migration guide (draft in tree; polish/link review still OK)
  - [ ] exact `cellpycore==` pin for the release commit — **blocked** (see gate)
  - [ ] `UV_NO_SOURCES=1 uv lock` + essential green against that pin
  - [ ] follow `release-procedure.md` / cut `v2.0.0aN` when ready (tag timing may slip)

## Pin gate — cellpy-core #136

Do **not** treat the current `cellpycore==0.2.1` bump as the v2.0 release pin until:

1. [cellpy/cellpy-core#136](https://github.com/cellpy/cellpy-core/issues/136) is fixed
   (legacy bridge: preserve `test_id` on steps/summary; legacy-schema `merge_data`),
2. cellpy-core gets a **version bump + PyPI release** (next tag after `v0.2.1`),
3. cellpy re-pins to that exact `cellpycore==X.Y.Z` with `UV_NO_SOURCES=1 uv lock`.

Until then, campaign merge in cellpy still relies on the #507 re-stamp workaround;
pinning 0.2.1 again does not close V2-15.
