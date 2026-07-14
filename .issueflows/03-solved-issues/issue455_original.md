# Issue #455: Stage 1.10: Fix hard-coded column-header literals (report priorities 1–3)

Source: https://github.com/jepegit/cellpy/issues/455

## Original issue text

> Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

Replace the ~250 true hard-coded column-name literals with canonical headers-class
lookups, in the report's priority order:

1. **Journal pages** (`batch.py:277–292` info_df keys, `batch_journals.py` "selected",
   `helpers.py`/`collectors.py`/`batch_plotters.py` group/sub_group/label sites) →
   `hdr_journal.*`.
2. **Steps/raw access** in `ocv_rlx.py` (~25 sites) and `plotutils.py` (~40) →
   `hdr_steps.*` / `hdr_raw.*`.
3. **Instrument loaders** (`neware_nda.py` rename-dict values, arbin/maccor config
   `"power"`/`"dv_dt"` values, `post_processors.py` groupbys) → `headers_normal.*`.

Also delete the dead block at `easyplot.py:721–739` (references the pre-v8 API).

## Why

Native-headers plan Phase 0 prerequisite: after this cleanup, renaming a header touches
header classes only, and the Stage-2 flip cannot be silently broken by a stray literal.
Priority 3 matters doubly — loaders define the raw-table contract, and a header rename
would break them without any test noticing today.

## Links

- `architecture-plan/hardcoded-column-headers-report.md` (the full file:line → replacement tables, §8)
- `architecture-plan/cellpy2-native-headers-migration-plan.md` (Phase 0.2)
- Independent of other Stage-1 issues; can start immediately.

## Acceptance

- Re-running the report's scanner (methodology in the report) over the priority-1–3
  files returns zero unclassified column-literal hits.
- Full suite green (pure refactor — the strings resolve to identical values).

