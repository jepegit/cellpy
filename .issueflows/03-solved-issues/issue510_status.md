# Issue #510 — status

- [x] Done

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
  - [x] pin gate cleared: cellpy-core #136 → `cellpycore==0.2.2` on PyPI
  - [x] `HeadersSummary` / `HeadersStepTable.test_id` parity + pipeline_smoke golden regen
  - [x] PR #523 CI green / merge
  - [ ] follow `release-procedure.md` / cut `v2.0.0aN` when ready (tag timing may slip)

## Pin gate — cellpy-core #136

Cleared (2026-07-17): core #136 shipped as `cellpycore==0.2.2`. cellpy pin +
header parity + pipeline_smoke golden updated on this branch.
