# History

## [Unreleased]

* Stage 0 foundations complete — all linked characterization, oracle, baseline, convention, and decision-register issues closed; ready for Stage 1 (#439)
* Docs: Stage 0.11 decision register recorded in architecture-plan (timezone, curve-schema, v9 container, IR semantics, easyplot, v1.x maintenance) (#438)
* Conventions: `cellpy._deprecation.warn_once` helper, `DEPRECATIONS.md` registry, exception-tree stubs (`CellpyError` re-export plus `CorruptCellpyFile`, `ConfigurationError`, `UnitsError`, `LoaderError`), and `make_new_cell` wired as first consumer (#437, closes #456)
* Testing: legacy v4/v5 cellpy-file loads now covered in the v4–v7 characterization matrix (removed stale TypeError pin) (#466)
* CI: retry `setup-miniconda` in scheduled workflow on transient conda-forge download failures (#465)
* Testing: Stage 0.9 benchmark harness — opt-in `pytest-benchmark` suite under `benchmarks/`, committed v1.x baseline JSON, and dedicated CI job with ±20% regression gate (#436)
* Docs: Stage-0 AST inventory scanners (`scan_member_usage.py`, `scan_hardcoded_headers.py`) in `.issueflows/00-tools/` for consumer/header reports (#435) (`tests/parity.py::assert_value_parity`) — legacy vs native frames compared through `cellpycore.legacy.mapping` with dtype-tolerant mapped-column equality, named exception list, and trivial-pass essential tests on the current bridge (#434)
* Testing: curve-extraction golden snapshots for `get_cap` / `get_ccap` / `get_dcap` / `get_ocv` on the canonical Arbin cell, including labeled/interpolated/multi-cycle variants and NullData edge cases (#433)
* Testing: per-loader golden snapshots for tier-1 loaders (`arbin_res`, `maccor_txt`, `neware_txt`, `pec_csv`, `custom`) — raw frame, `raw_units`, and loader meta oracles under `tests/data/goldens/loader_*/` with parametrized essential regression tests (#432)
* Testing: prms configuration characterization tests — inventory parity contract, config round-trip/precedence, OtherPath coercion, `.env_cellpy` pickup, and `cellpy setup` dir/file creation (#430)
* Testing: cellpy-file HDF5 characterization tests — v8 round-trip (fid-populated fixture), limits-prefix trap, `max_cycle` selector, legacy version matrix, and missing-key failure mode (#429)
* Testing: golden-fixture convention under `tests/data/goldens/`, `dev/regenerate_goldens.py` suite registry, and `pipeline_smoke` essential oracle on the canonical Arbin `.res` (#428)
* Docs: clarify cellpy_units defaults in `cellpy.get()` and Google docstring formatting cleanup in `cellreader.py` (#425)
* Fix: bump pandas to 3.0.3 — BDF Unix-time export, batch journal string extraction, and post-processor datetime handling (#415)
* CI: move Windows conda pytest from AppVeyor to GitHub Actions (ACE x64 install with cache) (#407)
* Testing: new offline unit tests for `utils/helpers.py` (outlier removal, group names, rate column) and `readers/filefinder.py` (tmp-path raw-file trees) (#372)
* Fix: local `OtherPath.rglob()` did not recurse into subdirectories, so `search_for_files(..., sub_folders=True)` missed files in subfolders (#372)
* Fix: `remove_outliers_from_summary_on_nn_distance` crashed on pandas ≥ 2 (`TypeError` in 2-element window branch) (#372)
* Fix: `list_raw_file_directory(extension=...)` raised `TypeError` when filtering path objects (#372)
* Testing: silenced `easyplot` `SyntaxWarning` and corrected an `xfail` marker to use `raises=` (#372)

## 1.0.4a1 - 2026-07-03

First **alpha** on the automated GitHub release → PyPI pipeline. Install with
`pip install cellpy --pre` or `pip install cellpy==1.0.4a1`.

* Integration: `cellpycore` consumed from **PyPI** (pinned `0.1.2` for this release); core
  step/summary processing delegated via `OldCellpyCellCore` seam (#377, #400–#401)
* CI: `release.yml` — published GitHub release triggers test + PyPI trusted publishing (#403)
* Testing: `essential` pytest marker for read → step-table → summary smoke + parity contract
* Build: Python **≥ 3.13**; hatchling + uv-dynamic-versioning from git tags (#354)
* Removed dependency on cellpy-core's deprecated `create_selector` (#399)
* Plus fixes and features merged since `v1.0.3a6` (PEC reader #393, batch/config #392/#397,
  module rename #381, filters #363, BDF export #356, …)

## 1.0.3 (pre-release)

* Refactor: Renamed internal modules accidentally named `core` — `cellpy.readers.core` → `cellpy.readers.data_structures` and `cellpy.internals.core` → `cellpy.internals.connections` — to avoid a name clash with the new cellpy-core package (#381)
* Testing: Added header/unit parity contract tests asserting cellpy-core's settings copies (HeadersNormal, HeadersSummary, HeadersStepTable, CellpyUnits) stay in sync with cellpy's internal_settings (#378)
* Build: Migrated packaging to a single `pyproject.toml` (hatchling + git-tag dynamic versioning), managed with `uv`; removed `setup.py`/`requirements*.txt`/`MANIFEST.in` and added a Docker-based local build test (#354)
* Filters: add filtering possibility to plotters in plotutils (#363)
* Fix: clear leaky seaborn facet titles (`row = ... | cycle_type = standard`) in multi-row `summary_plot` panes when `show_formation=True`, while preserving x-tick labels on the bottom row (pre-existing bug surfaced by the new `_with_rate` y-sets)
* Exporters: New `CellpyCell.to_bdf(...)` exports raw time-series in [Battery Data Format](https://github.com/battery-data-alliance/battery-data-format) (CSV/Parquet) with optional cycle filtering, for use by UiA's dsToolbox and other BDF-aware tools (#356)
* Exporters: `to_bdf` now accepts an `extras` keyword for appending custom/auxiliary raw columns alongside the BDF payload (`extras=True` for all unmapped columns, or pass a list/string of column names). Extras are written verbatim with no unit conversion; the resulting file is no longer strictly BDF-compliant.
* General: New `cellpy.exporters` and `cellpy.filters` packages; the `CellpyCell` class layer no longer imports from `cellpy.utils`
* Batch: Batch plotting with multiple subfigures (#343, #344, #346)
* Batch: JSON db reader from batbase (`batbase_json_reader`) - new database reader for JSON-based batch files
* Batch: Improved batch load functionality
* Batch: Enhanced error handling and logging in batch processing with clearer exception messages
* Batch: Changed default output directory name from 'out' to 'dump'
* Batch: Use local folder for journal file as default
* Batch: Allow prms to pass during batch update when reloading cellpy files
* Batch: Improved `concat_summaries` with support for different averaging methods and filtering (low/high values)
* Batch: Added CV-share partitioning support in summary collector
* Batch: Added line hooks in summary plot
* Batch: Summary plot now supports fullcell standard
* Batch: Added possibility to drop columns and filter low/high for non-grouped data
* Batch: Added helper function `collectors.standard_gravimetric_collector`
* General: Require numpy >= 2
* General: Made explicit imports of parameters and readers in top init-file
* General: Allow additional arguments to plotly save images
* CLI: New label for create new projectdir in `cellpy new`
* Readers: JSON db reader now supports optional storage of raw JSON data via `store_raw_data` parameter
* Readers: Added `raw_pages_dict` and `pages_dict` properties to JSON db reader for accessing data as dictionaries
* Bug fixes: Fixed bug in pandas.ExcelWriter call (#347)
* Bug fixes: Fixed bug in summary collector (concat summaries) that mutated list of selected columns
* Bug fixes: Fixed bug in OtherPathsNew
* Bug fixes: Various other bug fixes and improvements
* CI: Fix failing CI pipelines (pyarrow runtime dep + AppVeyor 64-bit Miniconda) (#360)
* Bug fixes: Fix `TypeError: bad operand type for unary ~: 'slice'` in `plotutils.summary_plot` when called with `formation_cycles=False` or `0` (#366)
* Exporters: `to_bdf` accepts a `bdf_units` keyword to control units written into the BDF file (#365)

## 1.0.2

* Batch: `only_selected` keyword added for concatenating summaries choosing only selected cells in the pages (selected==1)
* General: Add option to specify custom_log_path and path to logging config json in get() (#326) by @morrowrasmus
* Batch: implement wide format for collectors to csv
* Batch: adding more columns to pages (model, selected, nom_cap_specifics)
* General: Implemented lazy import to speed up loading of cellpy
* General: Added _absolute cols in the summary
* General: Add basic support for reading parquet for custom instruments (#322) by @morrowrasmus
* Utils: General improvements in plotutils
* General: Dropped support for python 3.9 and added support for python 3.12 (and probably beyond) by upgrading `OtherPaths`
* Bug fixes.

## 1.0.1

* Utils: `example_data` now includes auto-download of example data
* General: supports only python 3.10 and up to 3.11
* Batch: `naked` and `init(empty=True)` easier method for creating batch with empty pages
* File handling: new fix in `find_files`
* Batch / Utils: refactored and updated `Collectors` (using `plotly`)
* Batch: new summary plotter (using `plotly`)
* Batch: new convenience function for automatically creating batch from batch-file if file exists.
* Batch: added `mark` and `drop` methods
* CLI: added possibility to use custom jupyter executable
* Added checks (`c.has_xxx`) for checking if data has been processed correctly / fix errors in raw/semi-processed data.
* Added possibility to filter on C-rates (`c.get_cycles`)
* Added experimental feature `c.total_time_at_voltage_level` for calculating total time at low/high voltage
* Added experimental instrument reader for neware xlsx files (hopefully not used much because it is very slow)
* Added try-except block for ica post-processing step and add if-clause (suggested by Vajee)
* Fixed several smaller bugs and improved some of the functionality (most notably in `c.get_cap`)
* Added CI for macOS
* Added conda package including `sqlalchemy-access`
* Improved plotting tools
* Improved documentation
* Improved feedback from the CLI

## 1.0.0 (2023)

* Unit handling: new unit handling (using pint)
* Unit handling: renaming summary headers
* Unit handling: new cellpy-file-format version
* Unit handling: tool for converting old to new format
* Unit handling: parsing input parameters for units
* Templates: using one repository with sub-folders
* Templates: adding more documentation
* File handling: allow for external raw files (ssh)
* Readers: neware.txt (one version/model)
* Readers: `arbin_sql7` (experimental, @jtgibson91)
* Batch plotting: collectors for both data collection, plotting and saving
* OCV-rlx: improvements of the OCV-rlx tools
* Internals: rename main classes (`CellpyData` -> `CellpyCell`, `Cell` -> `Data`)
* Internals: rename `.cell` property to `.data`
* Internals: allow for only one `Data` object pr `CellpyCell` object
* CLI: general improvements and bug fixes
* CLI: move editing of db-file to the edit sub-command


## 0.4.3 (2023)

* Neware txt loader (supports one specific format only, other formats will have to wait for v.1.0)

## 0.4.2 (2022)

* Changed definition of Coulombic Difference (negative of previous)
* Updated loaders with hooks and additional base class `TxtLoader` with configuration mechanism
* Support for Maccor txt files
* Supports only python 3.8 and up
* Optional parameters through batch and pages
* Several bug fixes and minor improvements / adjustments
* Restrict use of instrument label to only one option
* Fix bug in example file (@kevinsmia1939)

## 0.4.1 (2021)

* Updated documentations
* CLI improvements
* New argument for get_cap: `max_cycle`
* Reverting from using Documents to user home for location of prm file in windows.
* Easyplot by Amund
* Arbin sql reader by Muhammad

## 0.4.0 (2020)

* Reading arbin .res files with auxiliary data should now work.
* Many bugs have been removed - many new introduced.
* Now on conda-forge (can be installed using conda).

## 0.4.0 a2 (2020)

* Reading PEC files now updated and should work

## 0.4.0 a1 (2020)

* New column names (lowercase and underscore)
* New batch concatenating and plotting routines

## 0.3.3 (2020)

* Switching from git-flow to github-flow
* New cli options for running batches
* cli option for creating template notebooks
* Using `ruamel.yaml` instead of `pyyaml`
* Using `python-box` > 4
* Several bug-fixes

## 0.3.2 (2019)

* Starting fixing documentation
* TODO: create conda package
* TODO: extensive tests

## 0.3.1 (2019)

* Refactoring - renaming from `dfsummary` to `summary`
* Refactoring - renaming from `step_table` to `steps`
* Refactoring - renaming from `dfdata` to `raw`
* Refactoring - renaming `cellpy.data` to `cellpy.get`
* Updated save and load cellpy files allowing for new naming
* Implemented cellpy new and cellpy serve cli functionality

## 0.3.0 (2019)

* New batch-feature
* Improved make-steps and make-summary functionality
* Improved cmd-line interface for setup
* More helper functions and tools
* Experimental support for other instruments
* invoke tasks for developers

## 0.2.1 (2018)

* Allow for using mdbtools also on win
* Slightly faster find_files using cache and `fnmatch`
* Bug fix: error in sorting files when using `pathlib` fixed

## 0.2.0 (2018-10-17)

* Improved creation of step tables (much faster)
* Default compression on cellpy (hdf5) files
* Bug fixes

## 0.1.22 (2018-07-17)

* Parameters can be set by dot-notation (`python-box`).
* The parameter Instruments.cell_configuration is removed.
* Options for getting voltage curves in different formats.
* Fixed python 3.6 issues with Read the Docs.
* Can now also be used on posix (the user must install `mdb_tools` first).
* Improved logging allowing for custom log-directory.

## 0.1.21 (2018-06-09)

* No legacy python.

## 0.1.0 (2016-09-26)

* First release on PyPI.
