# History

## [Unreleased]

* Matplotlib backend; retire SeabornPlotBuilder; unify backend= (#639).

* Port summary prepare path and flip summary_plot to prepare→spec→render (#638).

* Generic plotly panel/formation layout backend (#637).

* Add FigureSpec dataclasses and a PlotFamily registry (#636).

* Tier-3 loader close-out: `biologics_mpr` / `batmo_bdf` pass `check_loader`
  (native-projected adapters); `ext_nda_reader` parked; `local_instrument`
  confirmed as warn-only escape hatch (#561).

* Sync conda env files with `pyproject.toml`: pin `cellpycore ==0.2.3` from
  conda-forge (was PyPI 0.2.1), add `pyyaml` / `paramiko` / `universal-pathlib`,
  drop obsolete `fabric` (#628).

* Include plotting tests in the nightly Tier-3 matrix: drop the stale
  `test_plotutils_summary_plot` `--ignore` from `ci-scheduled.yml` and set
  `MPLBACKEND=Agg` on `conda-pytest` / `pip-install` (#594).

* Docs: expand the 1.x→2.x migration guide (support matrix, config/`c.schema`,
  ICA, plotting, alpha caveats, loader notes) and point at `DEPRECATIONS.md`
  (#572).

* **Maccor txt / 2.0.0a5:** zero capacities from a swallowed pandas-3
  `Series.update` failure (#580, fixed #581). Cellpy files saved from Maccor
  raw on 2.0.0a5 may have zeros baked in — re-load from raw after upgrading.
  Only `maccor_txt` (`split_capacity: True`) was affected.

* ICA redesign (#566): `ica.dqdv()` returns the long frame
  `cycle, direction, voltage, capacity, dqdv` (`dq` duplicate deprecated);
  new `ica.dvdq()`; failed half-cycles warn + `frame.attrs["failures"]`;
  old entry points shimmed to 2.1. Direction is **cell-centric** (#591).

* CLI: `cellpy convert` defaults to **v9**; `--to {v9,v8}` added; help is
  rich-formatted (Typer cutover #569). `click` is no longer a direct dependency.

* Plotting on 2.0.0a5: `raw_plot` / `cycle_info_plot` `KeyError: 'voltage'`,
  `summary_plot(x="cycle_index")`, and in-memory summary corruption from
  CV-split `y=` sets are fixed (#593 / #567 Phase 0). Re-load in-memory cells
  that hit the CV-split bug; disk files were unaffected.

* Dependency budget (#570): drop required `python-box` / `ruamel.yaml` /
  `python-dotenv`; move PyTables to `cellpy[legacy-files]` (conda still ships
  pytables). Missing extra raises `OptionalDependencyError` with the install
  hint.

* Loaders: unknown undeclared vendor columns warn once (#599); Maccor
  model-one `Watt-hr` maps to energy (`cumulative_charge_energy`), not power
  (#599). `harmonize()` raises if a schema cast empties a column; new
  `LoaderDeclarations.duration_columns` for string durations (loader authors).

## [2.0.0a6] - 2026-07-22

* **Breaking:** `CellpyCell.get_cap` now returns native `cellpycore` curve
  columns (#540, native-headers flip Stage 1): `voltage` → `potential` and
  `cycle` → `cycle_num` (`capacity` / `direction` unchanged). All in-repo
  consumers — `plotutils.cycles_plot`, the batch collectors, `ica`, and the
  CSV/Excel exporters — are updated; user code that indexes the `get_cap`
  frame directly must rename. See `docs/getting_started/migration_v1_to_v2.md`.

* Removed the deprecated `cellpy.utils.easyplot` module (#544). It was
  deprecated since 1.1 with removal scheduled for 2.0; use
  `cellpy.utils.plotutils` and `cellpy.utils.collectors` instead. The module,
  its tests, its docs entry, and its `DEPRECATIONS.md` row are gone.

* Step-type string literals use the `cellpycore` vocabulary (#543, native-
  headers Phase-0 prerequisite): `CellpyCell.list_of_step_types` is now
  `list(config.STEP_TYPES)` (was a hand-maintained duplicate of the 13
  step-type names), and the step-table `type` comparisons in `utils/ocv_rlx.py`
  / `utils/helpers.py` use `StepType.CHARGE.value` / `.DISCHARGE.value` instead
  of bare `"charge"` / `"discharge"` literals. Behavior-identical.

* Header column literals in `utils/helpers.py` and `filters/summary.py` use
  header-object attributes (#538, native-headers Phase-0 prerequisite): the
  base-name string-keyed `hdr_summary["charge_capacity"]`-style lookups become
  attribute access, and `filter_summary`'s `rate_columns` default is resolved
  from `HeadersSummary` (was a hard-coded `("charge_c_rate", "discharge_c_rate")`
  tuple). Postfix/specific columns (`*_gravimetric`, `areal_*`) keep string-key
  composition. Behavior-identical.

* Journal-page column literals use `HeadersJournal` attributes (#537, native-
  headers Phase-0 prerequisite): the string-keyed `hdr_journal["mass"]`-style
  lookups in `batch_plotters.py` and `helpers.py` become attribute access
  (`hdr_journal.mass`, …) so a journal-header rename touches the header class
  only. Behavior-identical.

* Remote paths via `universal_pathlib` (#375, #371): `OtherPath` is now a thin
  wrapper around `UPath` (fsspec/Paramiko) instead of Fabric. Supported schemes
  remain `ssh://` / `sftp://` / `scp://` (scp aliased to sftp). Remote
  `exists` / `is_file` / `is_dir` are truthful (no longer stubbed as always
  true). Saving a cellpy file to a remote URI raises a clear error. Credentials
  still come from `CELLPY_KEY_FILENAME` / `CELLPY_PASSWORD`. See
  `docs/getting_started/remote_paths.md`.

* Units are per-cell now (#427): `get_cellpy_units` returns a fresh
  `CellpyUnits` per call (optionally seeded from its argument, which used to
  be silently ignored), so changing units on one `CellpyCell` — directly, via
  the constructor, or via `cellpy.get(units=...)` — no longer changes them
  for every other cell in the session.

* Campaign merge supports `renumber_cycles=False` (#529, unblocked by
  cellpycore 0.2.2): sources keep their original cycle numbers — the
  identifying key becomes `(test_id, cycle)` and cycle-keyed consumers see
  the union of matching cycles; data points are still offset to stay
  globally unique. Steps/summary group and window per test, and the merged
  object round-trips through v9.

* Dependency-injection tail of V2-09 (#520): `CellpyCell(core=...,
  instrument_factory=...)` — the core seam and the loader registry are now
  constructor-injectable (defaults unchanged);
  `register_instrument_readers()` keeps an injected factory instead of
  silently rebuilding. ADR:
  `.issueflows/04-designs-and-guides/cellpycell-di-restructuring.md`.

* Split/drop-cycle helpers extracted from `cellreader.py` into
  `cellpy.readers.slicing` (#519, V2-09 follow-up): `split`, `split_many`,
  `drop_from`/`drop_to`, `from_cycle`/`to_cycle`, `drop_edges`,
  `with_cycles`, `mod_raw_split_cycle` moved verbatim (instance-first
  functions, thin delegates keep the public API); new pin tests added where
  coverage was thin.

* Exporter family extracted from `cellreader.py` into
  `cellpy.exporters.tabular` (#518, V2-09 follow-up): `to_csv` / `to_excel`
  and the `_export_*` helpers moved verbatim (instance-first functions, thin
  delegates keep the public API); the near-dead `_cap_mod_*` helpers moved
  along with their removal deferred to #520. A stray `print(externals)` debug
  line in `to_excel` was dropped.

* Native schema opt-in (#511, V2-11): `CellpyCell(native_schema=True)` keeps
  frames in native cellpy-core column names and runs the polars engine
  directly — no legacy rename sandwich. Supported pipeline: `from_raw` /
  `load` → `make_step_table` → `make_summary` → `save` (v9). Legacy path
  stays the default; legacy-named consumers (`get_cap`, exporters, plotting,
  campaign merge) are not supported on a native-schema cell yet.

* cellpycore 0.2.2 sync: the legacy bridge now carries `test_id` on steps and
  summary for all objects (core #136), so the #507 re-stamp workaround in
  `make_step_table` is removed and the campaign merger remaps the right-hand
  summary's `test_id` onto its new ids (previously the merged, pre-recompute
  summary showed `test_id=0` everywhere).

* Cellpy-file format v9 (#510, V2-13/14): default `save()` writes
  zip-of-parquet + `meta.json` (``.cellpy``); `load()` still reads v4–v8 HDF5
  and sniffs v9. Full `TestMetaCollection` (+ units/limits) persists on v9;
  campaign-merged multi-`test_id` objects round-trip. Escape: ``.h5`` /
  `cellpy_file_format="hdf5"`. Cellpy-owned `save_meta_archive` /
  `load_meta_archive` (core archive stubs stay stubs). User guide:
  `docs/getting_started/migration_v1_to_v2.md`.

* `make_summary` gains `exclude_step_types` (#509, v2 theme V2-12): step-type
  prefixes (e.g. `["cv_"]`) whose per-cycle capacity contribution is subtracted
  from cycle-end charge/discharge capacities before derived columns — the
  core-native replacement (cellpy-core #54) for the removed selector-based
  exclusion. The deprecated no-effect `exclude_types`/`exclude_steps`/
  `selector_type`/`selector` kwargs still only warn. Also fixes a latent load
  bug: older cellpy files with a double-nested `cycle_mode` (`[['anode']]`) are
  now unwrapped at the file-load boundary.
* Slim `CellpyCell` (#509, v2 theme V2-09): remove dead/experimental code —
  the `_dev_update*` family (broken call signatures, never wired), the
  module-level `_check*`/`__main__` dev-scratch harness, `_export_cycles_old`,
  `_select_steps`, the long-dead `select_steps`/`populate_step_dict`
  (raised `DeprecatedFeature` since 1.x), and the superseded `_select_without`
  legacy exclusion. The capacity/curve getters (`get_cap`, `get_ccap`,
  `get_dcap`, `get_ocv`) moved verbatim to the new
  `cellpy.readers.capacity_curves` module with thin delegate methods — public
  API unchanged, curve goldens byte-identical. `cellreader.py`: 5987 → 4778
  lines (−20%). Follow-ups tracked separately: exporter extraction, split/drop
  extraction, dependency-injection restructuring.
* Top-level API (#509, v2 theme V2-10): `cellpy.get` confirmed as the
  sanctioned entry point (stale removal-TODO dropped); `cellpy.merge_cells`
  and `cellpy.print_instruments` now exported at package level.

* Loaders emit per-test metadata (#508, v2 Phase 2, themes V2-05/06/08):
  `from_raw` now routes loader-parsed metadata (tester `test_ID`,
  `channel_index`, `creator`, `schedule_file_name`) into `meta_test_dependent`
  (so it persists and surfaces in `Data.tests`; the orphan attributes remain
  set for backward compatibility), stamps the compact `test_id` grouping key
  (0) onto raw (tester ids stay as provenance — note: this overwrites Arbin's
  per-row tester Test_ID values in the raw column), and records load
  provenance (`uuid` — new per load until #510 persists it, `source_kind`,
  `source_type`, `source_uri`, `raw_file_names`, `loaded_datetime`) that the
  derived `TestMeta` record now carries. Config-driven loaders stamp
  instrument `raw_units` on the returned `Data` (shared
  `internal_settings.merge_raw_units` helper). Arbin `Global_Table.Comments`
  now maps to `meta_common.comment`; the full vendor-column mapping (incl.
  deliberately dropped columns) is documented in the arbin_res module
  docstring. Loader goldens regenerated accordingly.

* Campaign merge (#507, v2 Phase 1-2, themes V2-03/V2-07): `CellpyCell.merge`
  is rewritten (old signature was dead code) — `merge(cells, mode="campaign")`
  folds different tests into one multi-test object: distinct compact `test_id`
  per source stamped on raw (overwrites tester-assigned ids; provenance stays
  in `meta_test_dependent.test_ID`), per-test metadata records in `Data.tests`,
  globally renumbered cycles, offset data points, unshifted timelines, and no
  cumulative carry-forward (summaries window per test on recompute).
  `mode="continuation"` keeps the classic fold (identical to
  `from_raw([f1, f2])`, which is untouched). New non-mutating `merge_cells()`
  helper and `test_meta.cycle_ranges_per_test()`. Step tables of campaign
  objects carry a `test_id` column so the engine groups and windows per test
  end-to-end. Also fixes latent bugs in `_append`'s `merge_step_table` branch.

* Per-test metadata API (#506, v2 Phase 1, themes V2-01/02/04): `Data.tests`
  exposes a `cellpycore.metadata.TestMetaCollection` keyed by `test_id`
  (active record derived from the legacy meta boxes, which stay authoritative;
  extra records stored in memory), with `Data.set_test_meta`,
  `Data.get_cycle_mode(test_id)` / `set_cycle_mode(mode, test_id)` and
  `Data.active_test_id`. v1-v8 cellpy files load as a single-test collection
  (`test_id=0`). Engine compute on objects mixing different `cycle_mode`s now
  raises `MixedCycleModesError` instead of silently applying one convention
  (per-test engine polarity: #507/#510). On-disk format v8 unchanged; only the
  active test's metadata is persisted (full collection persistence: #510).
  Adds the legacy<->core metadata mapping contract tests that
  `cellpycore.legacy.meta_mapping` assigns to cellpy. Future vocabulary/export
  alignment target: BattINFO (BIG-MAP).

* Header single source (#505, v2 Phase 0 gate): drop the redundant module-level
  `HEADERS_NORMAL` / `HEADERS_SUMMARY` / `HEADERS_STEP_TABLE` constants in
  `cellreader.py` and `data_structures.py`; use the instance attributes /
  `get_headers_*()` accessors from `internal_settings` instead.
* Decommission the in-repo legacy summary engine (#385, v2 Phase 0 gate):
  remove `_make_summar_legacy`, `_generate_absolute_summary_columns`,
  `_ir_to_summary`, `_end_voltage_to_summary` and the `make_summary(old=True)`
  branch — the cellpy-core engine is the only summary path. Breaking: the `old`
  kwarg is gone (1.x users keep it on the `v1.x` branch). The arbin_sql_h5 test
  now runs on the core path (verified value-identical; core prunes 13 duplicate
  raw rows, 47→34).

* Stage 3.3: single-file raw loads default to `harmonize(parse())`
  (`Reader.use_harmonized_raw=True`); Arbin wide-aux columns keep values under
  `aux_<quantity>_<name>`; vendor `datapoint_num` is preserved; `batmo_bdf`
  decode runs in `parse()`; `arbin_sql_h5` keeps all loader-stage rows. (#560)


## 1.1.0.post1 - 2026-07-15

* Sync conda env files (`environment.yml`, `environment_dev.yml`,
  `github_actions_environment.yml`) with `pyproject.toml`: pandas ≥3.0.3,
  `cellpycore==0.2.1` from PyPI, drop obsolete pip tooling
* Remove invoke `tasks.py`; `noxfile.py` installs from `pyproject.toml`
  (`.[all]` + dependency-group `dev`)
* Docs: require Python 3.13+, copyright 2026; remove scratch root notes /
  Jupyter ZMQ fix markdown; refresh developer folder-structure tree

## 1.1.0 - 2026-07-15

* Pin `cellpycore==0.2.1` (bridge honors `cycle_mode` for coulombic columns);
  regenerate `pipeline_smoke` goldens and fix native summary parity helper
* Stage 1.8: config migration — prms shim / legacy YAML path, migrate internal
  call sites, remove import-time config init (#453); `cellpy setup` writes
  `cellpy.toml` twin + `setup migrate`; `info --config` (#454)
* Stage 1.15 / 1.14: dormant native↔legacy frame translation (#458); Polars
  Phase A — de-index raw/summary/journal (#457)
* Stage 1.6: delegate duplicated unit converters to `cellpycore.units` (#451)
* Stage 1.7: parallel `cellpy/config/` pydantic-settings stack — typed models, layered TOML loader, provenance, `override()`, inventory parity vs #430; not wired into legacy `prms` yet (#452)
* Fix: full-suite test failures — `extract_fids` test uses module helper; external `check_file_ids` test avoids live SCP; Arbin `.res` loader closes ODBC connections (#491)
* Stage 1.10: replace hard-coded column-header literals with canonical `headers_*` lookups in journal pages, ocv_rlx/plotutils, and instrument loaders (priorities 1–3); delete dead easyplot block (#455)
* Stage 1.4: redirect out-of-band HDF5 readers to `cellpy_file.read_table` / `read_fid_table`; `CorruptCellpyFile` for missing keys; `cellpy convert` CLI for v<8 upgrades (#449)
* Stage 1.3: move cellpy-file read/write paths into `cellpy_file/` (#448)
* Units Phase 1: re-export ``CellpyUnits`` and ``Q`` from cellpycore; remove cellpy-local pint registry; rename ``cellreader`` ``data_structures`` alias to ``ds`` (#450)
* Deprecation: `cellpy.utils.easyplot` warns on import via `warn_once`; use `plotutils`/`collectors` instead (removed in 2.0, #438 decision 5) (#479)
* Fix: loader PEC golden compares all datetime columns by epoch-ns (Windows `datetime64[us]` vs `ns`); benchmark baseline gate warns above +20% slowdown and fails only above +100% (#476)
* Stage 1.1: extract cellpy-file format spec into `cellpy/readers/cellpy_file/format.py`; `prms._cellpyfile_*` aliases preserved; template registry and example-data URL constants moved to owning modules (#446)
* Stage 1.2: stateless cellpy-file helpers in `cellpy_file/`; explicit `LoadSelector`/`LoadLimits` replaces `self.limit_*` side channel during HDF5 extraction (#447)
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
