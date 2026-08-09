# Plan — Issue #862: dva_plot(direction='both') does not distinguish half-cycles visually

## Goal

Make charge vs discharge half-cycles visually distinguishable (not just via hover) when `direction="both"` in `dva_plot` — and, since it's the same code path, in `ica_plot` too.

## Investigation note (corrects the issue's framing)

`ica_plot` and `dva_plot` (`cellpy/utils/plotutils.py`) both route through the same shared
`prepare` (`cellpy/plotting/prepare/ica.py`) → `_render_ica_dva` renderer (one method per
backend: [`PlotlyBackend._render_ica_dva`](cellpy/plotting/backends/plotly.py) and
[`MatplotlibBackend._render_ica_dva`](cellpy/plotting/backends/mpl.py)). Reproduced with the
example cell: **`ica_plot(direction="both")` currently has the identical bug** — both docstrings
say outright "Line style is shared across charge and discharge." The issue's comparison is to
`cellpy.plotting.collected.ica_plotter` (the separate `Collection.plot` family-kind path fixed
in #821, `line_dash=direction_col` via `px.line`), not to `plotutils.ica_plot`.

Net effect: this is a **one-shared-fix** — patching `_render_ica_dva` fixes both `ica_plot` and
`dva_plot` at once, and they stay consistent with each other by construction (no per-kind
special-casing needed).

## Constraints

- Keep the fix minimal: line style only (dash), not a legend/trace-naming overhaul. The issue's
  "ideally `<cycle>, charge` / `<cycle>, discharge` names" is explicitly a nice-to-have
  ("ideally"), and both backends currently key their legend/colorbar by **cycle** (color), grouped
  across directions — renaming would double legend entries per cycle. Out of scope here.
- Match the #821 convention already established in `collected.py` for consistency across the
  codebase: charge = solid, discharge = dotted (`px.line`'s default dash sequence gives the first
  category `"solid"`, second `"dot"`, and `"charge"` < `"discharge"` alphabetically).
- Both backends (plotly + matplotlib) must get the fix — the issue only mentions plotly exports,
  but the mpl backend has the identical "shared line style" bug and docstring.
- Do not change trace/line count, names, or hover content — `tests/data/figure_specs.json`
  (structural snapshot, #567) does not record line style, so no golden-file update is needed as
  long as trace count/names/axes are untouched.

### Prior art

- `cellpy/plotting/collected.py::sequence_plotter` (#821 fix, lines ~573-580): sets
  `plotly_arguments["line_dash"] = direction_col` when `direction == "both"`, for the *separate*
  `Collection.plot(family_kind="ica")` path. Same convention (dash keyed by the `direction`
  column values `"charge"` / `"discharge"` from `cellpy.ica.CHARGE` / `cellpy.ica.DISCHARGE`) is
  reused here, but applied manually (since `_render_ica_dva` builds `go.Scatter` traces directly,
  not through `px.line`).
- `tests/test_collected_ica_direction.py::test_ica_line_direction_both_overlays_without_coerce` —
  existing pattern for asserting `{tr.line.dash for tr in fig.data}` has ≥2 distinct values;
  mirror this style for the new plotutils-level test.

## Approach

1. **Plotly backend** (`cellpy/plotting/backends/plotly.py::PlotlyBackend._render_ica_dva`):
   in the `for (cycle, direction), group in frame.groupby(group_cols, ...)` loop, compute
   `dash = "dot" if direction == DISCHARGE else "solid"` and pass `dash=dash` into the existing
   `line=dict(color=color, width=1.5)` dict. Import `CHARGE, DISCHARGE` from `cellpy.ica`
   (`ICA_COLS` is already imported there).
2. **Matplotlib backend** (`cellpy/plotting/backends/mpl.py::MatplotlibBackend._render_ica_dva`):
   in the `for (cycle, _direction), group in frame.groupby(...)` loop, rename `_direction` to
   `direction`, compute `linestyle = ":" if direction == DISCHARGE else "-"`, pass
   `linestyle=linestyle` to `ax.plot(...)`.
3. **Docstrings** — update both `_render_ica_dva` docstrings' "Line style is shared across charge
   and discharge" line to describe the new dash/linestyle behaviour.
4. **Tests** — add to `tests/test_ica_plot_prepare.py`:
   - `test_ica_plot_both_direction_dash_differs` (and `dva_plot` equivalent, or parametrized over
     both) for the plotly backend: call `ica_plot`/`dva_plot(direction="both", backend="plotly")`,
     assert `{tr.line.dash for tr in fig.data}` has at least 2 distinct values.
   - matplotlib equivalent: assert `{line.get_linestyle() for line in fig.get_axes()[0].get_lines()}`
     has at least 2 distinct values for `direction="both"`.
   - A `direction="charge"` (single-direction) sanity check that dash stays `"solid"`/`"-"` for
     both kinds, guarding against a future regression that always-dashes regardless of direction.

## Files to touch

- `cellpy/plotting/backends/plotly.py` — `PlotlyBackend._render_ica_dva`: add per-direction dash.
- `cellpy/plotting/backends/mpl.py` — `MatplotlibBackend._render_ica_dva`: add per-direction linestyle.
- `tests/test_ica_plot_prepare.py` — new direction/dash tests.
- `HISTORY.md` (at `/iflow-close`, per project convention) — patch-level fix note.

## Test strategy

- `uv run pytest tests/test_ica_plot_prepare.py -m essential` for the fast path; then the
  documented merge gate `uv run pytest -m essential` (per `AGENTS.md`).
- Plotting tests run fine outside `MPLBACKEND=Agg` requirement here since this repo's local dev
  loop uses conda per project rules — will run via the activated `cellpy_dev_313` env (or `uv run`
  if conda isn't needed locally); confirm whichever is available in the close step actually runs.
- Manually re-run the issue's repro snippet for both `ica_plot` and `dva_plot` to confirm dash
  values differ and match before/after.

## Open questions

None — scope, convention (match #821), and file list are all resolved from the codebase itself.
