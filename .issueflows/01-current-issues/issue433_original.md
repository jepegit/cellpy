# Issue #433: Stage 0.6: Curve-extraction golden snapshots (get_cap family)

Source: https://github.com/jepegit/cellpy/issues/433

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Golden snapshots of `get_cap` / `get_ccap` / `get_dcap` / `get_ocv` outputs on the golden
cells, across the option matrix that utils actually use (method="forth"/"forth-and-forth",
`categorical_column`, `label_cycle_number`, `interpolated`, `trim_taper_steps`,
`as_frame` variants) — including the current output column names ("capacity", "voltage",
"cycle", "direction") that today exist in no headers class.

## Why

The extraction layer is proposed to move into `cellpycore.curves` with a spec'd schema
(gap item G4); its parity tests need today's outputs frozen first. This is also the safety
net for the curve-frame header decision the native-headers plan lists as a prerequisite —
13+ call sites in utils consume these frames.

## Links

- `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` (§2.3 curves module, §5 tests)
- `architecture-plan/hardcoded-column-headers-report.md` (§5 — the unspec'd curve columns)
- `architecture-plan/cellpy2-utils-migration-plan.md` (waves 2–3 consume the curves module)
- Depends on Stage 0.1.

## Acceptance

- Snapshot matrix committed + regenerable; a parametrized parity test reads them back.
- Known interpolation corner cases (empty cycles → NullData) captured as explicit cases.
