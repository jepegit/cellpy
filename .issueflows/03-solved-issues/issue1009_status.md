# Issue #1009 — status

- [x] Done

## Diagnosis

`summary_collector(b, family="fullcell_standard_gravimetric").plot()` drew 10
facets instead of 4: `summary_options` stripped the `_cv` suffix and asked for
the base column with `partition_by_cv=True`; `collect_summaries` then kept
`col`, `col_non_cv`, `col_cv` for every requested column (CE included).
All 7 `fullcell_standard*` families were affected (10–12 columns vs 4); the 13
other summary families were exact. On top of that the plot faceted one row per
variable, so charge and discharge of the same quantity never shared a panel.

## Done

- `cellpy/plotting/registry.py` — `summary_options` requests declared columns
  literally (still turns `partition_by_cv` on for `*_cv` / `*_non_cv`).
- `cellpy/collect/summary.py` — the `(col, col_non_cv, col_cv)` expansion only
  applies when the requested list names no CV variant itself.
  `SummaryOptions` docstring updated.
- `cellpy/plotting/collected.py` (`summary_plotter`, Plotly):
  - `split_direction()` / `_panel_mapping()`: variables differing only by a
    `charge` / `discharge` token (prefix, suffix or mid-name) share a panel
    named by the token-free key; a variable alone on its key keeps its name.
  - `line_dash="direction"` (charge solid, discharge dashed); trace names
    reduced to the series with one legend entry each; second legend
    `legend2` ("Direction"). `spread_plot` gets the same dashes.
  - `order_variables`, `y_ranges`, `y_label_mapper` accept original variable
    names or panel keys; `_yaxis_key_for_variable` falls back to the panel key.
  - `combine_directions=False` opt-out.
  - Labels: `capacity_gravimetric` (direction-less panel key) gets units;
    `*_non_cv` → "… non-CV" with correct mode/unit; `mod_01_*` →
    "Normalized … (%)".
- Tests: oracle in `tests/test_collect.py` now rejects extra columns; literal
  CV list test; `summary_options` tuple test; new
  `tests/test_collected_summary_directions.py` (8 essential tests);
  `tests/test_collected_summary_groups.py` synthetic names neutralised and the
  #947/#948 snippets updated for the merged capacity panel;
  `test_collected_summary_axes.py` spread hover test skips `legend2` entries.
- Docs: `HISTORY.md`, `AGENTS.md`, `docs/getting_started/agents.md`,
  `.issueflows/04-designs-and-guides/test-registry.md`.

## Resulting facet counts

`fullcell_standard_*` 4 (CV part / capacity / CE / normalized); `capacities_*`
1; `*_coulombic_efficiency` 2; `*_with_rate` 2; `*_split_constant_voltage` 3;
`voltages` 1. Verified with an in-memory batch of the two Arbin `.res` test
cells and rendered PNGs.

## Out of scope / notes

- Seaborn / matplotlib summary backends: facets follow the panel rewrite, no
  dash styling.
- Legacy `b.plot()` (`plot_cycle_life_summary_plotly`) and single-cell
  `summary_plot(y=...)` untouched.
