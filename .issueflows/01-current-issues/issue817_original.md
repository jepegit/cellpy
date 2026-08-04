# Issue #817: spread_plot ignores share_y / match_axes on collected summary facets

Source: https://github.com/jepegit/cellpy/issues/817

## Original issue text

## Problem / context

Follow-up to #804 (per-panel y-limits / `share_y` for collected summary facets — fixed for the non-spread path in 2.1.1.post2+).

`summary_plotter` resolves `share_y` / `match_axes` and passes `match_axes=` into `_cycles_plotter`, but the **spread** path (`spread_plot` / mean±std bands when a group-averaged frame is plotted with `spread=True`) never links facet y-axes — `matches` stays unset even when `match_axes=True`.

Apps that offer “Share y-scale” together with “Group avg + Spread” must re-apply `yaxisN.matches = \"y\"` after `collection.plot` (cellpy-simple-gui #47).

## Spec

Honour `share_y` / `match_axes` in `spread_plot` the same way the non-spread summary path does.

## Acceptance criteria

- [ ] `collection.plot(spread=True, share_y=True)` (or `match_axes=True`) links secondary facet y-axes to the primary.
- [ ] `share_y=False` keeps independent auto-scale on the spread path.
- [ ] Interaction with `y_ranges` remains coherent (fixed limits should not be defeated by re-linking).
- [ ] Regression test covers Group avg + Spread + share_y.

## Related

- #804 (closed) — non-spread path
- cellpy-simple-gui #47 (app workaround)


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy ≥2.1.1.post4. Full write-up: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
