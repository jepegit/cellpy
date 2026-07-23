# Issue #657: Re-base collectors' drawing half onto `cellpy.plotting`

Source: https://github.com/jepegit/cellpy/issues/657

## Original issue text

## Context

Part of epic #567 (Stage 3 — Collectors drawing half, Batch.plot, retire batch_plotters). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` (plus batch redesign §4.7 and collectors redesign §3.3 for the hand-offs). Collection, caching, autonaming, and frame persistence stay in collectors (out of scope to redesign).

## Scope

Delete collectors' plotter implementations (`sequence_plotter`, `summary_plotter`, `cycles_plotter`, `spread_plot` drawing bodies) and local templates; `BatchCollector.plot` / render path calls `cellpy.plotting.*` with the already-collected tidy frame (`cell`/`group`/`sub_group` columns). Fold fig-per-cell / fig-per-cycle / film / spread capabilities into plotting options (`layout=`, `kind=`) as needed for parity.

## Acceptance

- Collector-driven figures that the maintainers' docs/tutorials exercise match the oracle (add collector/batch-input cases to `figure_specs.json` as needed).
- Collectors no longer define figure IO, legend helpers, or plotly templates locally.
- `import cellpy.utils.collectors` stays safe without the `batch` extra for non-plot imports.

## Depends on

#647

Part of epic #567.

