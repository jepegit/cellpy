# Issue #377: Prepare cellpy to consume cellpy-core (isolate the Data object via a core seam)

Source: https://github.com/jepegit/cellpy/issues/377

## Original issue text

## Goal

Prepare `cellpy` so it can delegate its core data processing (step/cycle table
building, summaries) to the new **`cellpy-core`** package, **without** requiring a PyPI
release of `cellpy-core` (use a git / editable dependency during development).

This issue tracks the *preparation work inside `cellpy`* — establishing a clean seam so
the monolithic `CellpyCell` can hand processing to a core object.

## Background

- The core "find steps and cycles + build per-step/per-cycle tables" logic currently
  lives in `cellpy/readers/cellreader.py` (~305 KB) and `cellpy/readers/core.py`.
- `cellpy-core` is the small, fast re-implementation of that logic.
- Branch `334-isolate-parts-needed-for-cellpy-core` is the **in-tree ancestor** of
  `cellpy-core` (it created `cellpy/slim/`) and already **proves the seam works**:
  - `self.core = CellpyCellCore(...)` on `CellpyCell`
  - `data` property returns `self.core._data` (Data ownership moved into core)
  - `make_summary` delegates to `self.core.make_core_summary(...)`
  - `tests/test_slim.py` exercises it
- The delegation contract is currently **byte-for-byte safe**: `cellpycore.legacy`'s
  `HeadersNormal` / `HeadersSummary` / `HeadersStepTable` and `CellpyUnits` are identical
  to `cellpy/parameters/internal_settings.py` (verified field-by-field).

## Strategy: mine branch 334, do NOT merge it

Branch 334 is ~136 ahead / 24 behind master with a ~1-year-old merge-base. Both sides
heavily rewrote `cellreader.py` in **overlapping regions** (class header/properties and
the summary methods, where master independently added `add_to_summary` and
cycle-selection methods). A raw merge is high-pain and risks silently dropping master
features. The seam is ~5 small edit points, so **re-derive it on fresh master** and keep
334 as a reference blueprint.

## Scope of this issue (first PR)

- [ ] Add `cellpy-core` as a **git / editable** dependency (track a branch during dev;
      pin to tag/commit for releases).
- [ ] On `CellpyCell`: construct `self.core = cellpycore.OldCellpyCellCore(...)`
      (the legacy bridge class that restores old headers/units).
- [ ] Move `Data` ownership: `data` property reads/writes `self.core._data`.
- [ ] Route `make_summary` (and the newer `add_to_summary` / cycle-selection methods)
      through `self.core`.
- [ ] Leave `make_step_table` in `cellreader.py` for now (not yet ported to core).
- [ ] Port `tests/test_slim.py` (from branch 334) as the seam acceptance test; keep the
      full suite green.

## Decisions to make early (cheap, unblocking)

- [ ] **Python floor.** `cellpy-core` requires `>=3.13`; `cellpy` supports 3.10–3.13.
      Either raise `cellpy`'s floor to 3.13 or lower `cellpy-core`'s. Decide before wiring.
- [ ] **Build backend** (separate, low-priority PR). Moving `cellpy` from
      setuptools+`requirements.txt`+`setup.py` to hatchling+uv (matching core) is
      desirable for tooling parity but independent of integration. Note `setup.py`
      carries `package_data`, `entry_points`, and `extras_require` to translate.

## Follow-ups (separate issues/PRs)

- [ ] **Contract tests** asserting `cellpycore.legacy` headers/units equal
      `internal_settings` field-by-field (prevent silent drift of the duplicated copies).
- [ ] **Port `make_step_table`** into `cellpy-core`. Note: `cellpy`'s `CellpyLimits`
      (step-type detection thresholds) is NOT copied into `cellpy-core` yet and must
      travel with this port.
- [ ] Settle the column-header harmonization (`config.Cols` ↔ legacy `Headers*`).

## Acceptance criteria

- `cellpy` depends on `cellpy-core` via git/editable install.
- `CellpyCell` owns its `Data` through `self.core`, and `make_summary` runs through
  `cellpy-core`, with the existing test suite green.
