# Plan — Issue #863: No collect_dva (DVA is single-cell only)

## Goal

Add `cellpy.collect.collect_dva(batch, options=IcaOptions(...))` returning a `Collection`,
mirroring `collect_ica`, so DVA gets the same multi-cell `Collection.plot()` / grouping /
save / export treatment as summaries/cycles/ICA.

## Constraints

- Reuse the existing `cellpy.collect.options.IcaOptions` dataclass for both ICA and DVA (per
  the issue's own proposed signature) rather than inventing a `DvaOptions` — add the one field
  DVA actually needs (`capacity_resolution`) instead of a parallel dataclass.
- Match `collect_ica`'s per-cell cycle-isolation behaviour exactly (cycles resolved from the
  *originally requested* set every iteration — the legacy cross-cell narrowing bug,
  collectors.py:1691 — must not regress for DVA either).
- `Collection.plot()` must work out of the box for a DVA collection (`kind="dva"`) — currently
  `Collection._FAMILY` has no `"dva"` entry (falls back to `"cycles"`, wrong columns) and
  `render_collected` has no `family_kind == "dva"` branch (falls through to raw
  `sequence_plotter` without ICA/DVA column defaults). Both must be wired, or `collect_dva(...).plot()`
  breaks immediately — this is the same gap the issue calls out for the *plot family registry*
  (`registry.get("dva")` already exists) vs the *collector*.
- Correct resolution knob: `cellpy.ica.dqdv` differentiates along **voltage** (needs `voltage_resolution`
  for the q(V) interpolation); `cellpy.ica.dvdq` differentiates along **capacity** (needs
  `capacity_resolution` for the V(q) interpolation, per `cellpy.ica.IcaOptions` docstring +
  `dvdq`'s own docstring: "differentiates the smoothed V(q) curve"). `collect_ica` forwards
  `voltage_resolution`; `collect_dva` must forward `capacity_resolution`, not `voltage_resolution`.
- Follow the existing one-file-per-collect-family convention (`cells.py`, `curves.py`, `ica.py`,
  `summary.py`) — new `cellpy/collect/dva.py`, not a growing `ica.py`.
- Keep the legacy `BatchCollector` convenience-wrapper parity too (`ica_collector` exists
  alongside `collect_ica`) — add `dva_collector` for symmetry; it is a 5-line wrapper.

### Prior art

- `cellpy/collect/ica.py::collect_ica` — the function to mirror almost line-for-line: per-cell
  `iter_cells` loop, per-cell cycle isolation via the *originally requested* tuple, `_as_polars`
  conversion, `pl.concat(..., how="diagonal_relaxed")`, `opts.transforms` post-hooks,
  `CollectionMeta(kind=..., options={...}, cells_included=...)`.
- `cellpy/plotting/collected.py::ica_plotter` (wraps `_cycles_plotter` with
  `x="voltage", y="dqdv", z="cycle", g="cell"`) — mirror as `dva_plotter` with
  `x="capacity", y="dvdq"` (labels/units swapped: "Capacity"/"mAh/g" and "dV/dQ"/"V/(mAh/g)").
  `_cycles_plotter` / `sequence_plotter` are already column-name-generic — no changes needed there.
- `cellpy/collect/collection.py::Collection._FAMILY` and
  `cellpy/plotting/collected.py::render_collected` — both need a `"dva"` branch/entry (see
  Constraints above).
- `cellpy/collect/collector.py::ica_collector` — mirror as `dva_collector`.
- `tests/test_collectors.py::test_ica_collector_uses_the_specced_frame` /
  `test_ica_collector_film_mode` / `test_ica_collector_fig_pr_cycle` — mirror for DVA in a new
  `tests/test_collect_dva.py` (or add alongside in `test_collectors.py`; matches existing
  `populated_batch` fixture reuse pattern).

## Approach

1. `cellpy/collect/options.py::IcaOptions` — add `capacity_resolution: float | None = None`
   field (alongside existing `cycles`, `voltage_resolution`, `transforms`).
2. New `cellpy/collect/dva.py::collect_dva(batch, options=None, **overrides) -> Collection`:
   copy `collect_ica`'s structure, swap `ica.dqdv` → `ica.dvdq`, forward
   `opts.capacity_resolution` (not `voltage_resolution`) into the per-cell call, `kind="dva"`,
   `name=f"{batch.journal.name or 'batch'}_dva"`, `meta.options={"cycles": ..., "capacity_resolution": ...}`.
3. `cellpy/collect/collector.py` — add `dva_collector(batch, options=None, *, autorun=True, **overrides)`
   convenience wrapper bound to `collect_dva` (mirrors `ica_collector`).
4. `cellpy/collect/__init__.py` — import/export `collect_dva`, `dva_collector`.
5. `cellpy/collect/collection.py::Collection._FAMILY` — add `"dva": "dva"`.
6. `cellpy/plotting/collected.py`:
   - Add `dva_plotter(collected_curves, cycles_to_plot=None, backend="plotly", method="fig_pr_cell", direction="charge", **kwargs)`
     mirroring `ica_plotter`, calling `_cycles_plotter(..., x="capacity", y="dvdq", z="cycle", g="cell", x_label="Capacity", x_unit="mAh/g", y_label="dV/dQ", y_unit="V/(mAh/g)", default_title="Differential Voltage Analysis Plots", ...)`.
   - `render_collected`: add `if family_kind == "dva": return dva_plotter(frame, backend=backend, method=method, **opts)`.
   - Update `collected_plot`'s docstring `family_kind` line to list `"dva"` too.
7. **Tests** — new `tests/test_collect_dva.py` (reusing `populated_batch` from `tests/test_batch.py`,
   same `pytest.importorskip("plotly")` guard as `test_collectors.py`):
   - `collect_dva` produces the specced frame (`cycle`, `direction`, `capacity`, `voltage`, `dvdq`)
     and `.plot()` renders a non-empty figure.
   - `dva_collector` convenience wrapper runs end to end (mirrors `test_ica_collector_uses_the_specced_frame`).
   - `capacity_resolution` reaches `ica.dvdq` (monkeypatch spy, mirrors
     `test_collect_cycles_forwards_mode_and_method`), and that `voltage_resolution` is
     **not** what gets forwarded (guards the resolution-knob mixup called out above).
   - `Collection(kind="dva").plot()` picks the `dva` family (not the `cycles` fallback) —
     regression guard for the `_FAMILY` wiring.

## Files to touch

- `cellpy/collect/options.py` — add `capacity_resolution` to `IcaOptions`.
- `cellpy/collect/dva.py` — new, `collect_dva`.
- `cellpy/collect/collector.py` — add `dva_collector`.
- `cellpy/collect/__init__.py` — export both.
- `cellpy/collect/collection.py` — `_FAMILY` entry.
- `cellpy/plotting/collected.py` — `dva_plotter` + `render_collected` branch + docstring.
- `tests/test_collect_dva.py` — new.
- `HISTORY.md` (at `/iflow-close`).

## Test strategy

- `uv run pytest tests/test_collect_dva.py tests/test_collectors.py -v` (needs plotting extras;
  both files already guard with `pytest.importorskip("plotly")`).
- `MPLBACKEND=Agg uv run pytest -m essential` merge gate.
- Mark new tests `@pytest.mark.essential` matching the existing collector test conventions (none
  of `test_collectors.py`'s existing tests carry the marker today — check current state at build
  time and follow whatever the file does, per the essential-tests-review step in `/iflow-close`).

## Open questions

None — the API shape, options reuse, and the two wiring gaps (`_FAMILY`, `render_collected`)
were all resolved by reading the existing ICA collector/plotter pair end to end.
