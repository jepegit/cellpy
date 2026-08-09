# Plan: #846 selective summary rebuild after metadata edits

## Goal

Give apps (e.g. cellpy-simple-gui) a public meta→summary dependency map and a
`refresh_after(...)` helper so post-load mass/area/nom-cap/cycle-mode edits
do not require an opaque full `make_summary()` when a summary already exists.

## Constraints

- Yolo-sized: no new selective column engine; reuse existing
  `core.add_scaled_summary_columns` seam already used by `_make_summary`.
- Document **current** behaviour accurately: C-rate columns come from the step
  table and are **not** derived from `nominal_capacity` (core comment).
- Keep setters as assignment; point them at `refresh_after` in docstrings.
- Do not change default `make_summary` behaviour.

### Prior art

- `_make_summary` → `core.make_core_summary` + `core.add_scaled_summary_columns`
  (`cellpy/readers/cellreader.py`) — scaled path is already the meta-dependent half.
- `cellpycore.summarizers.generate_specific_summary_columns` /
  `equivalent_cycles_to_summary` — overwrite via `with_columns` (safe re-run).
- Toolbox: none relevant.

## Approach

1. Add module-level `SUMMARY_META_DEPENDENCIES` (and alias map) describing what
   each meta field invalidates / affects.
2. Add `CellpyCell.refresh_after(fields, **kwargs)`:
   - normalize field names (`mass`/`active_mass`, `area`/`active_electrode_area`,
     `nom_cap`/`nominal_capacity`, `cycle_mode`);
   - if no summary → `make_summary(**kwargs)`;
   - else recompute `nom_cap_abs` + specific conversion factors and call
     `core.add_scaled_summary_columns` in place (no `make_core_summary`).
3. Docstring notes on mass / area / nom_cap / cycle_mode setters.
4. One paragraph in `docs/getting_started/agents.md`.
5. Unit tests for map keys + mass change updates gravimetric columns without
   requiring a full rebuild path assertion.

## Files to touch

- `cellpy/readers/cellreader.py` — map + `refresh_after` + setter docs
- `docs/getting_started/agents.md` — short usage note
- `tests/test_refresh_after_meta.py` — new focused tests
- `.issueflows/01-current-issues/issue846_{plan,status}.md`

## Test strategy

`uv run pytest tests/test_refresh_after_meta.py -q` then `uv run pytest -m essential -q`.

## Open questions

None — batch cycle confirm covers Accept.
