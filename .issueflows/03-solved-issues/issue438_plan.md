# Plan for issue #438: Decision register

## Goal

Record all six Stage 0.11 maintainer decisions in their owning `architecture-plan/`
documents with dated decision notes, so Stage 1 work (loaders, v9 format, core curves
port, utils migration, release policy) starts from explicit choices rather than implicit
PR defaults.

## Constraints

- **No behavior changes** in `cellpy` or `cellpy-core` — documentation only.
- **Authoritative plan home:** sibling repo `../architecture-plan/` (not `code-reviews/`).
- Each decision gets a **dated note** in the plan doc that owns it (per issue acceptance).
- Grill-me conclusions (2026-07-10) are binding for this plan.

### Prior art

- **`tests/parity.py::assert_value_parity`** (`tests/parity.py`, issue #434) — named
  `exceptions=` frozenset for oracle columns that intentionally diverge (IR semantics).
- **Curve goldens** (`tests/test_curve_extraction_goldens.py`, issue #433) — frozen legacy
  `get_cap` outputs; parity target for `cellpycore.curves` port.
- **Gap analysis F4** (`architecture-plan/cellpy2-plans-gap-analysis.md`) — documents the
  IR-semantics oracle tension; status row to update when decision is recorded.
- **Toolbox:** no script for decision recording; manual markdown edits in `architecture-plan/`.
- **Existing proposed defaults** in plan docs (D3 timezone, loader §2.3 curves, metadata
  open Q5) — align recordings with grill-me outcomes, replacing “decision needed” markers.

## Agreed decisions (grill-me, 2026-07-10)

| # | Topic | Decision |
|---|-------|----------|
| 1 | Timezone | Naive legacy `date_time` → `epoch_time_utc`: **assume local TZ**, **warn**, record on `TestMeta.time_zone`. |
| 2 | Curve-schema | **`cellpycore.curves` + spec-first `CurveCols`** (`curve_table.md`); `CellpyCell.get_cap` stays a thin wrapper. |
| 3 | v9 container | **Zip-of-parquet + sidecar `meta.json`** (not single Arrow file). |
| 4 | IR semantics | **Corrected extractor at native-headers flip (Stage 1 Phase 3)**; `ir_charge` / `ir_discharge` on parity **exception list** until goldens/shim document divergence. No change before flip. |
| 5 | easyplot | **Deprecate in v1.x** (module-level warning on `master` / next 1.x minor); **remove in 2.0** (no port, no rewrite). |
| 6 | v1.x maintenance | **12 months** bugfix-only on `v1.x` fork from **2.0 release date**. |

## Approach

1. **Branch in `architecture-plan`** (or commit from cellpy workspace with path into sibling
   checkout): one PR updating plan docs only.
2. **Per-decision edits** — in each owning doc, replace “decision needed” / open-question
   text with a `### Decision (2026-07-10, issue #438)` block stating the choice and
   downstream implication in one short paragraph.
3. **Cross-doc consistency pass:**
   - easyplot timeline: utils + plotting + architecture plans currently say “deprecate 2.0 /
     remove 2.1” — update all to **deprecate v1.x / remove 2.0**.
   - gap-analysis table: mark **F4** decided; note easyplot and maintenance where cited.
   - `stage0-github-issues.md` / `stage1-github-issues.md`: add footnote that #438 decisions
     are recorded (optional one-liner).
4. **Unblock downstream issues** — no GitHub issue state changes required; recording is
   sufficient to start cellpy-core#118 and Stage 1 child issues.
5. **cellpy repo** — optional: add a one-line pointer under
   `.issueflows/04-designs-and-guides/cellpy-workspace-repos.md` or a short
   `stage0-decisions.md` durable note linking to the architecture-plan commits (only if
   useful for local agents; not required by acceptance).

### Recording map (which file gets which decision)

| Decision | Primary doc(s) |
|----------|----------------|
| 1 Timezone | `cellpy2-native-headers-migration-plan.md` (D3), `cellpy2-loader-port-and-extraction-plan.md` (§2.1.3 / risks) |
| 2 Curves | `cellpy2-loader-port-and-extraction-plan.md` (§2.3), `cellpy2-architecture-plan.md` (seam table) |
| 3 v9 container | `cellpy2-metadata-handling-plan.md` (open Q5), `cellpy2-native-headers-migration-plan.md` (Phase 2) |
| 4 IR semantics | `cellpy2-plans-gap-analysis.md` (F4), `cellpy2-native-headers-migration-plan.md` (Phase-3 oracle / exceptions), `cellpy2-utils-migration-plan.md` (F4 menu note) |
| 5 easyplot | `cellpy2-utils-migration-plan.md` (§2 triage + §4 deprecations), `cellpy2-plotting-redesign-plan.md` |
| 6 Maintenance | `cellpy2-release-and-branching-plan.md` (§1 support matrix) |

## Files to touch

| Path | Change |
|------|--------|
| `../architecture-plan/cellpy2-native-headers-migration-plan.md` | D3 timezone decision; Phase 2 v9 layout; Phase-3 IR exception pointer |
| `../architecture-plan/cellpy2-loader-port-and-extraction-plan.md` | §2.3 curves confirmed; timezone per-loader default |
| `../architecture-plan/cellpy2-metadata-handling-plan.md` | Close open Q5 (v9 container); `time_zone` field usage note |
| `../architecture-plan/cellpy2-plans-gap-analysis.md` | F4 → decided; refresh status table |
| `../architecture-plan/cellpy2-utils-migration-plan.md` | easyplot deprecate v1.x / remove 2.0; IR semantics menu |
| `../architecture-plan/cellpy2-plotting-redesign-plan.md` | easyplot timeline aligned |
| `../architecture-plan/cellpy2-release-and-branching-plan.md` | 12-month maintenance locked |
| `../architecture-plan/cellpy2-architecture-plan.md` | Curves seam + easyplot one-liner if inconsistent |

**cellpy repo (issue-flow only):**

| Path | Change |
|------|--------|
| `.issueflows/01-current-issues/issue438_status.md` | Progress checklist (created at `/iflow-start`) |

## Test strategy

No pytest for this issue. Verification checklist:

- [ ] All six decisions have a dated `Decision (2026-07-10, issue #438)` note in the mapped docs.
- [ ] No remaining “decision needed” markers for these six items in those sections.
- [ ] easyplot timeline consistent across utils + plotting + release docs.
- [ ] gap-analysis F4 row shows decided.
- [ ] `git diff` in `architecture-plan` is markdown-only.

## Open questions

None — all resolved via grill-me (2026-07-10).

## Implementation note (v1.x easyplot deprecation)

Recording the easyplot decision does not by itself add the `DeprecationWarning` — that
lands in a follow-up **cellpy** PR on `master` (likely tied to next v1.x minor or Stage
1.10 / utils wave 0). This issue’s PR is plan-doc recording only; flag the code change in
`issue438_status.md` as a documented follow-up for Stage 1.
