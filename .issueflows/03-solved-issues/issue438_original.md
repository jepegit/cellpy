# Issue #438: Stage 0.11: Decision register — the calls that gate Stage 1+

Source: https://github.com/jepegit/cellpy/issues/438

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Decide (with the maintainer) and record — each in its owning plan document under
`architecture-plan/` — the small set of decisions later stages build on:

1. **Timezone rule** for legacy naive `date_time` → `epoch_time_utc`
   (native-headers plan D3; loader plan §2.1.3). Proposed default: naive = local, warn,
   record on `TestMeta.time_zone`.
2. **Curve-schema home**: confirm `cellpycore.curves` + `CurveCols` spec-first
   (loader/extraction plan §2.3) — gates utils waves 2–3.
3. **v9 container format**: zip-of-parquet + `meta.json` vs single arrow file with schema
   metadata (metadata plan open Q5; file plan §5; header-migration Phase 2).
4. **IR-semantics switch** (gap F4): when cellpy 2 adopts the corrected extractor and how
   the parity exception is recorded (Stage 0.7's exception list).
5. **easyplot fate**: deprecate-in-2.0 vs rewrite (utils plan triage).
6. **v1.x maintenance window**: 12 months vs last-two-minors (release plan §1).

## Why

Each is cheap to decide and expensive to reverse after code lands; several plans explicitly
mark them "decision needed". Parking them in one checklist prevents them from being decided
implicitly by whoever writes the first affected PR.

## Links

- `architecture-plan/cellpy2-native-headers-migration-plan.md` (D3, §6)
- `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` (§2.3)
- `architecture-plan/cellpy2-metadata-handling-plan.md` (open questions)
- `architecture-plan/cellpy2-plans-gap-analysis.md` (F4)
- `architecture-plan/cellpy2-utils-migration-plan.md` / `architecture-plan/cellpy2-release-and-branching-plan.md`

## Acceptance

- All six checkboxes decided; each recorded in its plan doc with a dated note.

