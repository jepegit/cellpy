# Issue #816: group_it=True: average multi-member groups even when some groups are singletons

Source: https://github.com/jepegit/cellpy/issues/816

## Original issue text

## Problem / context

`collect_summaries(..., group_it=True)` still silently returns a *wide, non-averaged* frame when **any** group has < 2 cells (the \"std needs ≥ 2 cells\" guard). One singleton disables averaging for *every* group — including those with plenty of members.

`Collection.is_grouped` / `meta.grouped` (#790) fixed the observability side. The **all-or-nothing** averaging behaviour remains; GUIs that mix multi-cell and single-cell groups must partition selections themselves (cellpy-simple-gui #27) and then merge Plotly figures.

Related merge friction (cellpy-simple-gui #39): long (averaged) and wide (per-cell) summary plots assign different subplot axis ids to the same `variable`, so naive `add_trace` puts singleton series on the wrong facet.

## Spec

1. When `group_it=True`, average groups with ≥ 2 cells and leave singletons as ordinary (non-spread) series in the **same** collection — not all-or-nothing.
2. Prefer stable facet subplot ids across long (averaged) vs wide (per-cell) summary plots for the same column set (or a documented merge helper), so apps can combine traces without remapping axes.

## Acceptance criteria

- [ ] A selection with one multi-member group and one singleton still averages the multi-member group.
- [ ] Singletons remain plottable as per-cell series (no forced empty/non-averaged whole collection).
- [ ] `is_grouped` / `meta.grouped` stay accurate for the mixed result.
- [ ] Tests cover mixed multi/singleton selections.
- [ ] (Stretch) long vs wide summary facets for the same variables share subplot identity, or a merge helper is documented.

## Out of scope

- Changing default UI in downstream apps.


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy ≥2.1.1.post4. Full write-up: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
