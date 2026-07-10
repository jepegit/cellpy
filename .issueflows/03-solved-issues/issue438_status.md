# Issue #438 — status

- [x] Done

## What's done

- Plan confirmed (`issue438_plan.md`, grill-me 2026-07-10).
- Branch `438-decision-register` on `cellpy` and `architecture-plan`.
- Six decisions recorded in `architecture-plan/` with dated notes (2026-07-10):
  1. Timezone — naive = local + warn + `TestMeta.time_zone`
  2. Curves — `cellpycore.curves` + `CurveCols`
  3. v9 — zip-of-parquet + `meta.json`
  4. IR semantics — corrected at flip; parity exceptions
  5. easyplot — deprecate v1.x, remove 2.0
  6. Maintenance — 12 months from 2.0 release
- Cross-doc consistency: easyplot timeline, gap-analysis F4, stage0/stage1 footnotes.

## Remaining work

- None.

## Close (2026-07-10)

- Essential tests green (`uv run pytest -m essential`).
- Issue files archived to `03-solved-issues/`.
- PRs: cellpy #472 (tracking), architecture-plan #1 (decision recordings).

## Follow-up (out of scope)

- Add `DeprecationWarning` on `utils/easyplot` import in a v1.x cellpy PR (Stage 1).
