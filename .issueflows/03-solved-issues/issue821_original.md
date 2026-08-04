# Issue #821: ICA plotter: honour direction for line layouts; support direction='both'

Source: https://github.com/jepegit/cellpy/issues/821

## Original issue text

## Problem / context

`cellpy.utils.ica.dqdv(..., direction=\"both\")` (and therefore `collect_ica`, which calls `dqdv` with the default) returns a tidy frame with both half-cycles (`direction` column = `charge` / `discharge`). The collected **plot** path has two gaps:

1. **`both` unsupported.** `ica_plotter` only accepts `direction=\"charge\"` or `\"discharge\"` and silently coerces anything else to `\"charge\"` (with a `print`). Apps that want a single figure with both directions must merge two plot calls themselves. cellpy-simple-gui #56 therefore exposes only Charge | Discharge in the Cell explorer dQ/dV UI.

2. **Line / `fig_pr_cell` ignores `direction`.** `ica_plotter` → `_cycles_plotter` → `sequence_plotter` only calls `_select_direction` when `method==\"film\"`. For the default ICA line layout (`fig_pr_cell` / `layout=\"per_cell\"`), the `direction` kwarg is a **no-op**: both lobes stay in each cycle’s trace and Plotly can draw a spurious join between half-cycles. Surfaced in cellpy-simple-gui #67 after #56.

**App workaround (#67):** filter the collected ICA polars frame to `direction == charge|discharge` before `Collection.plot`.

## Spec

- Call `_select_direction` for ICA **line** layouts as well as `film`.
- Honour `direction=\"both\"` (e.g. two series or grouped legend entries per cycle, with a break so half-cycles do not join).
- Prefer a logger warning over `print` when coercing invalid values.

## Acceptance criteria

- [ ] `collection.plot(family_kind=\"ica\", layout=\"per_cell\", direction=\"charge\")` (and `"discharge\"`) actually filters half-cycles for line plots — not only `method=\"film\"`.
- [ ] Charge vs discharge figures differ for the same cell/cycles/resolution.
- [ ] Selecting a single direction does not draw a spurious line joining the other half-cycle.
- [ ] `direction=\"both\"` produces a usable overlay without silently coercing to charge.
- [ ] Invalid direction values log a warning (not `print`) if coerced.
- [ ] Tests cover charge / discharge / both for the default line layout.


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy ≥2.1.1.post4. Full write-up: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
