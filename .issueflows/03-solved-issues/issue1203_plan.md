# Issue #1203 — plan

Source: https://github.com/jepegit/cellpy/issues/1203

## Goal

`ica_collector(b, cycles=(2, 3, 4))` must not raise
`ValueError: cycle frame is empty` when one cell has no curve and another
does. Same for a call with `cycles` omitted. There is no cell-count limit.

## Constraints

- The raise the report shows is the v2.1.5.post8 behavior. It was fixed in
  v2.1.5.post9 (`54ca1556`, #1154, HISTORY "Improve function ica_collector.
  (#1152)"). Master and PyPI `2.1.5.post11` already skip that cell, warn,
  and record `meta.cells_skipped`. A direct `dqdv` / `dvdq` on the empty
  cell still raises.
- conda-forge `cellpy` is still `2.1.5.post8`, which is why
  `conda update -c conda-forge cellpy` does nothing for the reporter.
  The feedstock is not in this repo. This PR does not touch it.
- Do not change the skip rules, the error text, or `cycles_collector`.
  `cycles_collector` already ignores an empty `get_cap` per cycle
  (`cellpy/collect/curves.py`).
- No cell-count cap exists. One empty frame used to abort the whole batch.

### Prior art

- `cellpy.collect.ica._collect_derivative` — catches
  `ValueError` whose message contains `"cycle frame is empty"`, warns,
  and continues. `ica_collector` / `dva_collector` both call it.
- `tests/test_collect.py::test_derivative_collector_skips_an_empty_cycle_frame`
  — same skip for `collect_ica` / `collect_dva` with `cycles=(1,)`.
  Mirror this; do not add a second skip implementation.
- `cellpy.ica._empty_cycle_frame_error` — the message the report quotes.
  Single-cell `dqdv` keeps raising it
  (`tests/test_ica_api.py`).
- Toolbox: nothing applies. `graphify-out/GRAPH_REPORT.md` is absent.

## Approach

1. Leave `src/cellpy/collect/ica.py` and `collector.py` as they are.
2. Add one essential test that calls the public `ica_collector` (the
   function in the report), not only `collect_ica`:
   - batch with one good `_CurveCell` and one whose `get_cap` is an
     empty frame
   - `ica_collector(batch, cycles=(2, 3, 4))` does not raise
   - `ica_collector(batch)` with `cycles` omitted does not raise
   - the warning names the empty cell
   - `meta.cells_included` is the good cell and `meta.cells_skipped` is
     the empty cell
   - the good cell's rows are the only rows
3. On close, comment on #1203: no cell limit; post8 aborts the batch;
   post9+ skips the empty cell; PyPI is post11; conda-forge is still
   post8, so conda cannot see the fix. `pip install -U cellpy` can.

## Files to touch

- `tests/test_collect.py` — the new essential test next to
  `test_derivative_collector_skips_an_empty_cycle_frame`. Reuse
  `_CurveCell`, `_linear_curve_frame`, and `_derivative_batch`.
- `.issueflows/01-current-issues/issue1203_status.md` — during build.

## Test strategy

```bash
uv run pytest -m essential tests/test_collect.py::test_ica_collector_skips_an_empty_cycle_frame
uv run pytest -m essential tests/test_collect.py::test_derivative_collector_skips_an_empty_cycle_frame
```

Then `uv run pytest -m essential` before close.

## Open questions

- None. conda-forge stays out of this PR.
