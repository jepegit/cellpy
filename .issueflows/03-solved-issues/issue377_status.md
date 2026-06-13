# Status — Issue #377: Prepare cellpy to consume cellpy-core (core seam)

- [x] Done

## Summary

`CellpyCell` now delegates Data ownership and the per-cycle summary pipeline to
`cellpy-core` via the legacy bridge `OldCellpyCellCore`. The full cellpy test
suite is green (494 passed, 17 skipped, 13 xfailed) on Python 3.13, and the new
`tests/test_slim.py` acceptance tests pass.

## Decisions (confirmed with user)

- **Python floor:** raised cellpy's floor to **3.13** (matches cellpy-core).
- **Dependency style:** declared the git URL in `setup.py` `install_requires`
  (`cellpycore @ git+https://github.com/cellpy/cellpy-core.git@main`) and used a
  local editable install for development (`uv pip install -e ../cellpy-core`).

## Changes in `cellpy`

- `cellpy/readers/cellreader.py`
  - Import `OldCellpyCellCore` and `cellpycore.selectors`.
  - `__init__`: construct `self.core = OldCellpyCellCore(initialize=False, debug=debug)`.
  - Data ownership: the `data` getter/setter and `initialize()` now read/write
    `self.core._data`; removed the standalone `self._data`.
  - `_make_summary`: build the selector via `core_selectors.create_selector(...)`
    and delegate the summary pipeline to `self.core.make_core_summary(...)` +
    `self.core.add_scaled_summary_columns(..., to_units=self.cellpy_units)`. cellpy
    keeps selector setup, nominal-capacity resolution, step-table/dedup handling,
    and the final column-sort / cycle-index post-processing. The deprecated
    `use_cellpy_stat_file` special path now simply runs the selector.
- `setup.py`: added the cellpycore git dependency, `python_requires=">=3.13"`,
  trimmed classifiers to 3.13.
- `requirements.txt`: added the cellpycore git line (with an editable-install note).
- `tests/test_slim.py`: new acceptance tests (seam wiring, Data ownership,
  end-to-end `make_summary`, save round-trip, direct `make_core_summary`).

## CI / environment updates (Python 3.13 floor)

- `.github/workflows/*.yml` (8 files: `pytest_posix`, `pytest_win`, `pytest_macos`,
  `pytest_macos_14`, `pip-install-posix`, `pip-install-win`, `pip-install-macos-14`,
  `check_conda_forge`): matrix `python-version` changed from
  `["3.10", "3.11", "3.12"]` to `["3.13"]`. (`test-win.yml` is a disabled experiment
  with no Python version — untouched.)
- `github_actions_environment.yml`: added `cellpycore @ git+...@main` to the pip
  section (required — `cellpy` imports `cellpycore` at module load, so the conda
  `pytest` job would otherwise fail on import). Python is injected by the workflow
  matrix (now 3.13).
- `environment.yml`: `python >= 3.10` -> `>= 3.13`; added cellpycore git dep.
- `environment_dev.yml`: `python=3.12` -> `python=3.13`; added cellpycore git dep;
  renamed env `cellpy_dev_312` -> `cellpy_dev_313` (and updated the reference in
  `.cursor/rules/this-project.mdc`).
- `docs/environment_rtd.yml`: `python >=3.10` -> `>=3.13`.

Note: CI pulls `cellpycore` from `github.com/cellpy/cellpy-core@main`, so CI will
only pass once the cellpy-core changes listed below are pushed to that branch (and
the repo is accessible to CI).

## Changes in `cellpy-core` (separate repo — needs its own commit/PR)

These were required to make the legacy bridge actually run (it had latent,
never-exercised bugs since the summary pipeline had no end-to-end tests):

- `units.py`: fixed broken import (`from cellpycore.legacy import Data` ->
  `from cellpycore.cell_core import Data`) that crashed `OldCellpyCellCore`.
- `summarizers.py` / `selectors.py`: module-level header instances now use the
  legacy classes (`HeadersNormal`/`HeadersStepTable`/`HeadersSummary`) instead of
  the new `config.Cols`, since the function bodies use legacy column names and the
  bridge operates on cellpy's legacy-named DataFrames.
- `cell_core.py` `make_core_summary`: implemented the `select_columns` pruning
  (was a `not implemented yet` no-op) to match legacy cellpy output.
- `cell_core.py` `add_scaled_summary_columns`: removed the duplicate
  `c_rates_to_summary` call (it collided with the one in `make_core_summary`,
  producing `charge_c_rate_x/_y` columns); added a `to_units` parameter so
  consumer-selected output units are honoured.
- `summarizers.py` `generate_specific_summary_columns`: added `to_units` passthrough
  to `get_converter_to_specific` (fixes user-selected output units, e.g.
  `cellpy_units["charge"]`).
- `summarizers.py` `end_voltage_to_summary`: deduplicate charge/discharge steps to
  one per cycle (keep last) before merging, so multi-step cycles no longer multiply
  summary rows.

## Verification

- `cellpy`: full default suite green (494 passed) on Python 3.13.11.
- `cellpy-core`: `uv run pytest` green (6 passed).
- No linter errors in edited files.

## Follow-ups (separate issues/PRs — out of scope here)

- Contract tests asserting `cellpycore.legacy` headers/units equal
  `cellpy.parameters.internal_settings` field-by-field (jepegit/cellpy#378).
- Port `make_step_table` (with `CellpyLimits`) into cellpy-core.
- Column-header harmonization (`config.Cols` <-> legacy `Headers*`); the
  module-level legacy-header workaround in cellpy-core's summarizers/selectors is a
  bridge measure until that lands.
- Pin the cellpycore dependency to a tag/commit before any cellpy release.
- Commit/PR the cellpy-core changes in that repo.
