# Issue #820: Pretty-print cycles collector facet strips (Cycle N / cell label, not cycle_num=)

Source: https://github.com/jepegit/cellpy/issues/820

## Original issue text

## Problem / context

Follow-up to #801 / 2.1.1.post4: summary facet labels are pretty-printed (no more `variable=charge_capacity_gravimetric` on strips; axis titles are human-readable).

The **cycles** family (`layout=\"per_cell\"` / `\"per_cycle\"`, legacy `fig_pr_cell` / `fig_pr_cycle`) still annotates facets as `cycle_num=1`, `cell=demo`, etc. Axis titles for capacity/voltage are already fine; only the facet strips look unfinished next to summary plots.

Surfaced while adding the multi-cell Cycles tab in cellpy-simple-gui #55 — same `collection.plot(family_kind=\"cycles\", layout=…)` path.

## Spec

Apply the same pretty-label pass to cycles (and other non-summary) collected layouts — e.g. `Cycle 1` / cell label only — so apps get consistent chrome without per-family string scrubbing.

Optionally document that `layout=` is preferred over legacy `method=\"fig_pr_*\"` in `cycles_plotter` docs.

## Acceptance criteria

- [ ] `layout=\"per_cell\"` / `\"per_cycle\"` facet strips do not use raw `cycle_num=` / `cell=` key=value form by default.
- [ ] Labels remain unambiguous with multiple cells/cycles.
- [ ] Summary pretty-labels from #801 stay unchanged.
- [ ] Docs/example mention cycles facet chrome (and prefer `layout=` over legacy method names).


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy ≥2.1.1.post4. Full write-up: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
