# Issue #654: bug: summary CV-split plots show full capacity for with-CV / without-CV (dead selector_type)

Source: https://github.com/jepegit/cellpy/issues/654

## Original issue text

## Summary

`summary_plot(y=\"capacities_*_split_constant_voltage\")` draws three rows (all / without CV / with CV) that are essentially **identical**. Expected: `capacity â‰ˆ capacity_without_cv + capacity_with_cv`.

Discovered while visually previewing figures on the #648 branch (`dev/preview_summary_plots.py`).

## Trace (plotting â†’ summary)

1. Prepare path: `SummaryPlotDataPreparer._prepare_cv_split_data` â†’ `partition_summary_cv_steps` in `cellpy/utils/plotutils.py`.
2. That helper builds the three series via:

```python
summary_no_cv = c.make_summary(selector_type=\"non-cv\", create_copy=True).data.summary
summary_only_cv = c.make_summary(selector_type=\"only-cv\", create_copy=True).data.summary
```

3. Same pattern in `cellpy/utils/helpers.py` â†’ `_partition_summary_based_on_cv_steps`.

4. **`make_summary(..., selector_type=...)` is deprecated and has no effect** (#509 / PR #517). Docstring and implementation only emit `DeprecationWarning`; the core summary engine ignores custom selectors. Both calls therefore return the **full** cycle-end summary.

5. Consequence: melted rows \"all\", \"without CV\", and \"with CV\" carry the same capacity values â†’ three visually identical panels.

## Evidence (golden Arbin figure cell)

On `tests` golden cell (`load_figure_cell()` / `20160805_test001_45_cc_01`):

- `selector_type=\"non-cv\"` summary â‰¡ full summary (byte-identical for areal discharge).
- `selector_type=\"only-cv\"` summary â‰¡ full summary.
- Step types present: `charge`, `discharge`, `ir`, `ocvrlx_*` â€” **no** `cv_charge` / `cv_discharge`.

So for this fixture, a *correct* CV split would show without-CV â‰ˆ all and with-CV â‰ˆ 0. Today with-CV wrongly shows the full capacity.

## Intended replacement (from #509)

`make_summary(exclude_step_types=[\"cv_\"], ...)` subtracts CV step capacity from cycle-end totals (\"as if CV never happened\") â€” that is the **non-CV** series.

There is **no** first-class \"only-CV\" summary mode today; the with-CV series should likely be derived as `full âˆ’ non_cv` (same columns), or core needs an include-only / CV-delta API.

## Suggested fix scope

- Update `partition_summary_cv_steps` and `_partition_summary_based_on_cv_steps` off dead `selector_type`.
- Define with-CV as difference (or add a proper summary mode).
- Add a regression test with a cell that actually has `cv_*` steps (golden Arbin CC-only is insufficient alone).
- Optionally warn/skip CV-split families when no `cv_*` steps exist.
- Regenerate figure-spec snapshots if structure/labels change; numerics are not in the structural oracle.

## Out of scope / notes

- Not a matplotlib/plotly layout bug â€” prepare feeds wrong numbers.
- Related open feature: #312 (split single-step CCCV into CC/CV substeps) â€” step typing may still be incomplete for some instruments; this issue is specifically the dead selector wiring.

## Related

- #509 / #517 (`exclude_step_types`)
- #648 (plotting redesign â€” discovery context only)
- Helpers: `cellpy/utils/plotutils.py` (`partition_summary_cv_steps`), `cellpy/utils/helpers.py` (`_partition_summary_based_on_cv_steps`)
