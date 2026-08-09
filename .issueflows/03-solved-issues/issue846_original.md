# Issue #846: No selective summary rebuild after metadata edits (mass/area/nom-cap/cycle mode)

Source: https://github.com/jepegit/cellpy/issues/846

## Original issue text

## Problem
Editing physical metadata after load — mass, active electrode area, nominal
capacity, cycle mode — requires a **full** `cell.make_summary()`. There's no
public API to rebuild only the dependent summary columns (e.g. gravimetric
capacities after a mass change, C-rates after a nominal-capacity change).

There's also no documented **meta → summary-column dependency map**, so an app
can't do targeted updates or tell the user precisely what a change will affect.

## How it surfaced
cellpy-simple-gui's "Manage Cells" lets users change these knobs post-load. The
app assigns `cell.mass` / `cell.active_electrode_area` / `cell.nominal_capacity`
/ `cell.cycle_mode` and then always calls the full `make_summary()`. Correct,
but opaque and potentially expensive for large cells, and easy to get subtly
wrong (which attribute invalidates which column?).

## Suggested fix (either is useful)
1. Cheap selective-refresh helpers keyed by meta field, e.g.
   `cell.refresh_after(("mass",))` that recomputes just the affected columns; or
2. A small documented dependency map / note ("`nominal_capacity` affects
   `charge_c_rate`, `discharge_c_rate`, normalized cycle index; `mass` affects
   `*_gravimetric`; `area` affects `*_areal`; …") so GUIs can scope rebuilds
   and messaging.

Dedicated setters (vs bare attribute assignment) would also help
discoverability of "what do I call after changing mass?".


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy 2.1.1.post7. Context: [CELLPY_PAINPOINTS.md §19](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
