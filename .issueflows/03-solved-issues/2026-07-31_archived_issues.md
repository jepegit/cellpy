# Archived issues — 2026-07-31

Pre-archive git ref: `1e3d04d3716eeb0639fa4735a06dc5d40daff063`
Recover any archived file with `git show <sha>:<path>` (or browse `git log -- <path>`).

## Issue #345: batch - read custom json

- Source: https://github.com/jepegit/cellpy/issues/345
- Archived files: issue345_original.md, issue345_plan.md, issue345_status.md
- Summary: The batch utility should be able to get info from other JSON files than the currently supported ones. We also need to allow for file searching after reading the JSON file. Make **custom / BatBase-style JSON** a first-class way to build a batch journal on the blessed `cellpy.batch` API, including **file search after read** so `raw_file_names` / `cellpy_file_name` are populated like `Batch.from_db(...)` already does for Excel/BatBase. Marked done and archived after close.

## Issue #372: code cleanups and test improvements

- Source: https://github.com/jepegit/cellpy/issues/372
- Archived files: issue372_original.md, issue372_plan.md, issue372_status.md
- Summary: before shipping we should go through the code, look for errors and improve our test suite to make sure it covers relevant use-cases. Continue the tests-first hardening of #372: add offline unit tests for the highest-value uncovered pure functions in `cellpy/utils/helpers.py` and path logic in `cellpy/readers/filefinder.py`, and fix two small test-suite quality nits from the iteration-1 backlog.

## Issue #375: Add support for remote paths for raw data and cellpy data access

- Source: https://github.com/jepegit/cellpy/issues/375
- Archived files: issue375_original.md, issue375_plan.md, issue375_status.md
- Summary: - Loading raw data from remote locations - Searching/listing remote raw-data directories - Reading and possibly writing cellpy files stored remotely - handling of authentication and credentials - when direct remote access is not possible: Predictable local caching / temporary copy behavior - Which remote schemes do we want to support initially? - ssh:// - sftp:// - scp:// **Status:** Accepted (2026-07-17) — ready for `/iflow-start`. Ship usable remote raw/cellpy path workflows (`ssh`/`sftp`/`scp`) by replacing the Fabric-heavy `OtherPath` implementation with a thin cellpy API wrapper around [`universal_pathlib.UPath`](https://github.com/fsspec/uni… Marked done and archived after close.

## Issue #381: Refactor module naming to prevent name clash with cellpy core

- Source: https://github.com/jepegit/cellpy/issues/381
- Archived files: issue381_original.md, issue381_plan.md, issue381_status.md
- Summary: Since we are going to extract core features of cellpy to cellpy-core, it will improve the codebase if we renamed all other things in cellpy that accidentally has been named core. Rename the two modules in `cellpy` that are accidentally named `core` so they no longer collide conceptually with the new `cellpy-core` package: - `cellpy/readers/core.py` -> `cellpy/readers/data_structures.py` - `cellpy/internals/core.py` -> `cellpy/internals/connections.py` Marked done and archived after close.

## Issue #391: BatchSummaryCollector default y-axis scaling

- Source: https://github.com/jepegit/cellpy/issues/391
- Archived files: issue391_original.md, issue391_plan.md, issue391_status.md
- Summary: The BatchSummaryCollector defaults to matching the y-axes of the generated subplots. This can be disabled by setting the argument `plotter_arguments={"match_axes": False}`; however, since this matching is only suitable for specific plot combinations, while it is not suitable for the majority of cases, I propose to have this setting default to False. The `BatchSummaryCollector` currently defaults to matching y-axes across subplots. This happens because: 1. `BatchSummaryCollector` uses `summary_plotter` as its plotter function 2. `summary_plotter` calls `_cycles_plotter` passing through `**kwargs` 3. Marked done and archived after close.

## Issue #407: Do not use appveyor

- Source: https://github.com/jepegit/cellpy/issues/407
- Archived files: issue407_original.md, issue407_plan.md, issue407_status.md
- Summary: Lets try to stop using appveyour for testing if things works on windows. I am pretty sure there exists solutions on github actions now. The main difficulty is maybe the odbc driver stuff requiring some microsoft things (we need to read .res files - they are MS access db files). Retire AppVeyor as the Windows CI provider and run the same conda-based pytest smoke check on GitHub Actions instead, including whatever is needed to read Arbin `.res` files (MS Access via ODBC). Marked done and archived after close.

## Issue #415: Bump pandas

- Source: https://github.com/jepegit/cellpy/issues/415
- Archived files: issue415_original.md, issue415_plan.md, issue415_status.md
- Summary: Bump pandas from 2.3.3 to 3.0.3 results in broken tests - in particular bdf export functionallity. Fix it. Raise the `pandas` dependency from 2.3.3 to 3.0.3 and fix all test regressions so the suite is green. Primary breakage called out in the issue is BDF export (`cellpy.exporters.bdf`); reproduction shows **42 failures** across four test modules on pandas 3.0.3. Marked done and archived after close.

## Issue #425: Iterative fixes: get() docstring units

- Source: https://github.com/jepegit/cellpy/issues/425
- Archived files: issue425_original.md, issue425_status.md
- Summary: Interactive `/iflow-fix` session. Individual fixes are recorded in the issue status markdown and landed together via `/iflow-close`. First fix: document `cellpy_units` defaults for `nominal_capacity` and `area` in `cellpy.get()` docstring. Interactive `/iflow-fix` session. - **2026-07-08** — Document `cellpy_units` defaults for `mass`, `nominal_capacity`, `loading`, and `area` in `cellpy.get()` docstring (`cellpy/readers/cellreader.py`). Marked done and archived after close.

## Issue #428: Stage 0.1: Golden-fixture convention and regeneration tooling

- Source: https://github.com/jepegit/cellpy/issues/428
- Archived files: issue428_original.md, issue428_plan.md, issue428_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see [issue #439](issue439_original.md) / [GitHub #439](https://github.com/jepegit/cellpy/issues/439)). Plan documents live in the **`architecture-plan`** repository (`cellpy-workspace/architecture-plan/`, alongside `cellpy` and `cellpy-core`). Establish one shared golden-fixture convention for cellpy 2 Stage 0 work: committed artifacts under `tests/data/goldens/`, regenerated only via `dev/regenerate_goldens.py` (with per-suite registration), plus documentation and a toy suite exercised in CI through the existing `esse… Marked done and archived after close.

## Issue #429: Stage 0.2: Characterization tests — cellpy-file round-trip + legacy version matrix

- Source: https://github.com/jepegit/cellpy/issues/429
- Archived files: issue429_original.md, issue429_plan.md, issue429_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/code-reviews/` (alongside the `cellpy` and `cellpy-core` repos). Add characterization tests that lock current cellpy-file (HDF5 v8) load/save behavior and legacy version handling **before** the cellpy-file extraction refactor (Step 0 in [`cellpy-file-loading-refactor-plan.md`](../../architecture-plan/cellpy-file-loading-refactor-plan.md)). Marked done and archived after close.

## Issue #430: Stage 0.3: Characterization tests — configuration system (prms)

- Source: https://github.com/jepegit/cellpy/issues/430
- Archived files: issue430_original.md, issue430_plan.md, issue430_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/code-reviews/` (alongside the `cellpy` and `cellpy-core` repos). Lock current `prms` / `prmreader` / `cellpy setup` behavior in characterization tests **before** the pydantic-settings rework (Step 0 in [`cellpy2-configuration-and-parameters-plan.md`](../../architecture-plan/cellpy2-configuration-and-parameters-plan.md)). Marked done and archived after close.

## Issue #431: Stage 0.4: Unit-handling test groundwork — registry interop, converter parity, pint-optional guard

- Source: https://github.com/jepegit/cellpy/issues/431
- Archived files: issue431_original.md, issue431_plan.md, issue431_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/code-reviews/` (alongside the `cellpy` and `cellpy-core` repos). Three test deliverables that make the unit consolidation safe to start: 1. Land Stage 0.4 unit-handling test groundwork: a strict-xfail registry-interop test and legacy↔core converter parity fixtures in **cellpy**, plus confirmation that the **cellpy-core** pint-optional guard from STEP-12 is already covered (add only if a gap shows up). Marked done and archived after close.

## Issue #432: Stage 0.5: Per-loader golden snapshots of current loader outputs

- Source: https://github.com/jepegit/cellpy/issues/432
- Archived files: issue432_original.md, issue432_plan.md, issue432_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Commit golden snapshots of current tier-1 loader output (raw frame, `raw_units`, loader meta) under `tests/data/goldens/loader_<instrument>/`, regenerated via `dev/regenerate_goldens.py`, with parametrized regression tests. 1. Marked done and archived after close.

## Issue #433: Stage 0.6: Curve-extraction golden snapshots (get_cap family)

- Source: https://github.com/jepegit/cellpy/issues/433
- Archived files: issue433_original.md, issue433_plan.md, issue433_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Commit regenerable golden snapshots of `get_cap` / `get_ccap` / `get_dcap` / `get_ocv` outputs on the canonical Arbin `.res` cell, with parametrized essential regression tests. 1. Marked done and archived after close.

## Issue #434: Stage 0.7: Value-parity comparator — the mapped-columns oracle harness

- Source: https://github.com/jepegit/cellpy/issues/434
- Archived files: issue434_original.md, issue434_plan.md, issue434_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). A reusable test utility (e.g. `tests/parity.py::assert_value_parity(legacy, native, family, *, exceptions=...)` — the Phase-3 oracle harness comparing legacy-named pandas frames to native-named frames through `cellpycore.legacy.mapping`. 1. Marked done and archived after close.

## Issue #435: Stage 0.8: Extend consumer scans to filters/, exporters/, internals/

- Source: https://github.com/jepegit/cellpy/issues/435
- Archived files: issue435_original.md, issue435_plan.md, issue435_status.md
- Summary: > Part of **Stage 0 â€” foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Close gap **G5** by re-running the two Stage-0 inventory scans over `cellpy/filters/`, `cellpy/exporters/`, and `cellpy/internals/` (Data/CellpyCell consumers only), then append dated addenda to the existing reports and enrich the utils-migration triage table for anything found i… Marked done and archived after close.

## Issue #436: Stage 0.9: Benchmark harness + v1.x performance baselines

- Source: https://github.com/jepegit/cellpy/issues/436
- Archived files: issue436_original.md, issue436_plan.md, issue436_status.md
- Summary: > Part of **Stage 0 â€” foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Add a `pytest-benchmark` suite under `benchmarks/` (outside default `pytest` discovery), capture v1.x performance baselines on the canonical golden cells, and gate regressions in a dedicated Linux CI job with a ±20% band — closing **G8** and unblocking polars Phase A. Marked done and archived after close.

## Issue #437: Stage 0.10: Conventions bootstrap — deprecation helper, exception tree, DEPRECATIONS registry

- Source: https://github.com/jepegit/cellpy/issues/437
- Archived files: issue437_original.md, issue437_plan.md, issue437_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Bootstrap shared conventions machinery: `warn_once` deprecation helper with registry, `DEPRECATIONS.md` rendering, exception-tree stubs, and a contributing-doc checklist line. - No import-time logging changes (out of scope). Marked done and archived after close.

## Issue #438: Stage 0.11: Decision register — the calls that gate Stage 1+

- Source: https://github.com/jepegit/cellpy/issues/438
- Archived files: issue438_original.md, issue438_plan.md, issue438_status.md
- Summary: > Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Record all six Stage 0.11 maintainer decisions in their owning `architecture-plan/` documents with dated decision notes, so Stage 1 work (loaders, v9 format, core curves port, utils migration, release policy) starts from explicit choices rather than implicit PR defaults. Marked done and archived after close.

## Issue #439: Stage 0: foundations for cellpy 2 (tracking issue)

- Source: https://github.com/jepegit/cellpy/issues/439
- Archived files: issue439_original.md, issue439_plan.md, issue439_status.md
- Summary: Complete **Stage 0** of the cellpy 2 effort: pin current behavior with characterization tests, golden fixtures and performance baselines, and put the shared test/convention machinery in place â€” so that every subsequent stage (file-loading refactor, config rework, unit consolidation, header/polars flip, loader port, utils migration) starts against a trusted oracle instead of v… Confirm Stage 0 is complete: all linked cellpy issues (#428–#438) done, exit criteria verified on current `master`, and only **cellpy-core#114** remains — then close #439 (or document the single cross-repo blocker if #114 is not ready). Marked done and archived after close.

## Issue #446: Stage 1.1: Purge non-config constants from prms.py; create readers/cellpy_file/ with format.py

- Source: https://github.com/jepegit/cellpy/issues/446
- Archived files: issue446_original.md, issue446_plan.md, issue446_status.md
- Summary: > Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Extract the cellpy-file layout spec and other non-config `prms.py` constants into their proper owning modules, with `prms` aliases preserved so behavior stays identical. This is the shared Step 1 of the file-loading and configuration plans. Marked done and archived after close.

## Issue #447: Stage 1.2: File-loading — stateless helpers out, selector/limits side-channel dead

- Source: https://github.com/jepegit/cellpy/issues/447
- Archived files: issue447_original.md, issue447_plan.md, issue447_status.md
- Summary: > Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Execute file-plan **Steps 2 + 3** in two separate commits: (1) move stateless cellpy-file helpers into `cellpy/readers/cellpy_file/` with one-line `CellpyCell` delegators; Marked done and archived after close.

## Issue #449: Stage 1.4: File-loading — out-of-band redirects, typed errors, `cellpy convert` CLI

- Source: https://github.com/jepegit/cellpy/issues/449
- Archived files: issue449_original.md, issue449_plan.md, issue449_status.md
- Summary: > Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Complete Stage 1.4 (file plan Steps 6–7): redirect out-of-band HDF5 readers into `cellpy_file`, replace the bare `Exception("OH MY GOD! …")` with `CorruptCellpyFile`, narrow `CellpyCell.load()`'s blanket `AttributeError` handler, and add a `cellpy convert` CLI for v&lt;8 → v8 upg… Marked done and archived after close.

## Issue #450: Stage 1.5: Units Phase 1 — one CellpyUnits, one pint registry, rename the `core` alias

- Source: https://github.com/jepegit/cellpy/issues/450
- Archived files: issue450_original.md, issue450_plan.md, issue450_status.md
- Summary: > Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Single pint registry per process: re-export `CellpyUnits` and `Q` from cellpycore, remove cellpy-local registry in `data_structures.py`, rename confusing `core` alias in `cellreader.py`, flip interop test to hard pass. - No numeric behavior changes; parity tests must stay green. Marked done and archived after close.

## Issue #451: Issue #451 — Stage 1.6: Units Phase 2 — delegate the duplicated converters to cellpycore.units

- Source: https://github.com/jepegit/cellpy/issues/451
- Archived files: issue451_original.md, issue451_plan.md, issue451_status.md
- Summary: GitHub: https://github.com/jepegit/cellpy/issues/451 Labels: cellpy2-stage1, yolo Delete cellpy's duplicated converter bodies and wrap the cellpycore.units originals (unit plan Phase 2): `get_converter_to_specific`, `nominal_capacity_as_absolute`, `to_cellpy_unit` (→ `convert_value`), `unit_scaler_from_raw` (→ `calculate_scaler`), and the inline current-factor pint math in `_ma… 1. **Re-pin** `cellpycore==0.2.0` (the Stage-1 additive release carrying core#115 `convert_value` / `calculate_scaler` / `validate_units`) + `uv lock` / `uv sync`. Rides in this PR per the core-first merge order. 2. Marked done and archived after close.

## Issue #452: Stage 1.7: Config — build the pydantic-settings stack in parallel

- Source: https://github.com/jepegit/cellpy/issues/452
- Archived files: issue452_original.md, issue452_plan.md, issue452_status.md
- Summary: > Part of **Stage 1 â€” behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Build the parallel `cellpy/config/` pydantic-settings stack (config plan Step 2) next to today's `prms` system — typed models, layered TOML loader, provenance, `override()`, and inventory parity against the #430 contract Marked done and archived after close.

## Issue #453: Stage 1.8: Config — swap the engine under prms, migrate call sites, kill import-time init

- Source: https://github.com/jepegit/cellpy/issues/453
- Archived files: issue453_original.md, issue453_plan.md, issue453_status.md
- Summary: > Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Wire production code onto the #452 `cellpy/config/` stack: a deprecated `prms` shim for external/notebook callers, mechanical migration of internal `prms.*` sites to `cellpy.config.*`, and removal of import-time `prmreader.initialize()` so `import cellpy` performs zero file I/O. Marked done and archived after close.

## Issue #454: Issue #454 — Stage 1.9: Config — `cellpy setup` rewrite and migration UX

- Source: https://github.com/jepegit/cellpy/issues/454
- Archived files: issue454_original.md, issue454_plan.md, issue454_status.md
- Summary: GitHub: https://github.com/jepegit/cellpy/issues/454 Labels: cellpy2-stage1 Config plan Step 5: `cellpy setup` generates `cellpy.toml` from the models (single source of truth — docs render from the same models); detects an existing `.cellpy_prms_<user>.conf` and offers `cellpy setup migrate` (one-time YAML→TOML conversion); folder-creation logic unchanged; The heavy lifting (TOML writer, YAML→TOML converter, provenance registry, `model_dump_for_file` with secrets excluded) already landed with the parallel config stack (#452). This issue is CLI wiring: 1. Marked done and archived after close.

## Issue #455: Stage 1.10: Fix hard-coded column-header literals (report priorities 1–3)

- Source: https://github.com/jepegit/cellpy/issues/455
- Archived files: issue455_original.md, issue455_plan.md, issue455_status.md
- Summary: > Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Replace hard-coded column-header string literals in Stage 1.10 priority 1–3 files with canonical `headers_*` lookups. Behavior-preserving pure refactor; full essential suite green. 1. Marked done and archived after close.

## Issue #457: Issue #457 — Stage 1.12: Polars Phase A — de-index raw/summary/journal in place

- Source: https://github.com/jepegit/cellpy/issues/457
- Archived files: issue457_original.md, issue457_plan.md, issue457_status.md
- Summary: GitHub: https://github.com/jepegit/cellpy/issues/457 Labels: cellpy2-stage1 Polars plan Phase A: dissolve the three contract-level index conventions while still on pandas — raw no longer indexed by data_point, summary no longer indexed by cycle_index, journal pages keyed by a filename column — plus a warn-only index lint. *Keys live in columns, never in an index* (polars plan decision 3) applied in place, v1.x-safe: 1. **A1 raw:** `arbin_res._post_process` stops promoting `data_point` to the raw index. Marked done and archived after close.

## Issue #458: Issue #458 — Stage 1.15: translate.py — dormant native⇄legacy frame translation in cellpy_file/

- Source: https://github.com/jepegit/cellpy/issues/458
- Archived files: issue458_original.md, issue458_plan.md, issue458_status.md
- Summary: GitHub: https://github.com/jepegit/cellpy/issues/458 Labels: cellpy2-stage1 Native-headers plan Phase 1: build `to_native(data)` / `to_legacy(data)` in `cellpy/readers/cellpy_file/translate.py` over `cellpycore.legacy.mapping` (dormant on v1.x 1. **`cellpy/readers/cellpy_file/translate.py`** — all header knowledge comes from `cellpycore.legacy.mapping` (core#116 / cellpycore 0.2.0); Marked done and archived after close.

## Issue #465: conda pytest windows failed

- Source: https://github.com/jepegit/cellpy/issues/465
- Archived files: issue465_original.md, issue465_plan.md, issue465_status.md
- Summary: Ci schedueled failed: Info from agent: The job failed during the conda environment setup step due to a **502 Bad Gateway error** when trying to download package metadata from the conda-forge repository: ``` requests.exceptions.HTTPError: 502 Server Error: Bad Gateway for url: https://conda.anaconda.org/conda-forge/linux-64/1bde174b2b1b538da03d3e12ddb119cf61030b0cd0b41f7f3ea4d99… Harden `ci-scheduled.yml` against transient conda-forge metadata/download failures (502 Bad Gateway) during `setup-miniconda`, without changing test scope. Wrap each `conda-incubator/setup-miniconda@v3` step in `Wandalen/wretry.action@v3.5.0` (3 attempts, 30s delay). Marked done and archived after close.

## Issue #466: CI failed on pytest on linux

- Source: https://github.com/jepegit/cellpy/issues/466
- Archived files: issue466_original.md, issue466_plan.md, issue466_status.md
- Summary: CI scheduled failed. The test `test_legacy_v4_v5_currently_raise_typeerror_on_meta_extract` is failing because it expects a `TypeError` to be raised when loading legacy v4/v5 HDF5 files, but the code is no longer raising that exception. Restore green scheduled CI by aligning the v4/v5 characterization test with actual loader behavior: legacy v4/v5 files load successfully with `accept_old=True` (same contract as v6/v7). Marked done and archived after close.

## Issue #467: test: Stage 0.9 benchmark harness with v1.x baselines (#436)

- Source: https://github.com/jepegit/cellpy/issues/467
- Archived files: issue467_original.md
- Summary: > **Note:** GitHub `#467` is a **merged pull request** (not a standalone tracking issue). It closed jepegit/cellpy#436 (Stage 0.9 benchmark harness). - Adds an opt-in `pytest-benchmark` suite under `benchmarks/` measuring five v1.x performance metrics on committed golden cells (single-cell pipeline, 20-cell batch summary collection, v8 load, `get_cap`, peak RSS).

## Issue #476: golden test fails

- Source: https://github.com/jepegit/cellpy/issues/476
- Archived files: issue476_original.md, issue476_plan.md, issue476_status.md
- Summary: Part 1: loader_pec_csv golden fails on Windows (datetime64[ns] vs datetime64[us]. Fix it. Part 2: Benchmarks fail. Tests seem flaky. Either due to bad limits or floating benchmark values. Set to limits, warning + exception. Exception only with extreme slow-downs (> 100%). Fix the Windows `loader_pec_csv` essential golden failure and make the benchmark baseline gate tolerant of normal CI noise: **warn** on moderate slowdowns, **fail** only on extreme regressions (>100%). Marked done and archived after close.

## Issue #479: Stage 1.18: Deprecate utils/easyplot on v1.x (decision #438-5)

- Source: https://github.com/jepegit/cellpy/issues/479
- Archived files: issue479_original.md, issue479_plan.md, issue479_status.md
- Summary: > Follow-up mandated by the Stage-0 decision register (#438, decision 5) and the > Stage-1 tracking issue (#459). Plans: `cellpy-workspace/architecture-plan/` > ([repo](https://github.com/cellpy/architecture-plan)). Emit a module-level `DeprecationWarning` when `cellpy.utils.easyplot` is imported, using `warn_once`, register in `DEPRECATIONS.md`, point users to `plotutils`/`collectors`. No functional changes. - Use existing `cellpy._deprecation.warn_once` (#437/#456). Marked done and archived after close.

## Issue #491: Iterative fixes: full-suite test failures

- Source: https://github.com/jepegit/cellpy/issues/491
- Archived files: issue491_original.md, issue491_status.md
- Summary: Interactive `/iflow-fix` session addressing failures from `uv run pytest`: - `test_extract_fids_from_cellpy_file` â€” AttributeError: `_extract_fids_from_cellpy_file` moved to module function - `test_check_file_ids_external_not_accessible` â€” TimeoutError from live SCP connection attempt Interactive `/iflow-fix` session. - **2026-07-14** — `test_extract_fids_from_cellpy_file`: call module-level `extract_fids_from_cellpy_file` from `cellpy.readers.cellpy_file.read` instead of removed `CellpyCell._extract_fids_from_cellpy_file`. Marked done and archived after close.

## Issue #510: v2: cellpy file format v2 + metadata persistence + release (V2-13/14/15)

- Source: https://github.com/jepegit/cellpy/issues/510
- Archived files: issue510_original.md, issue510_plan.md, issue510_status.md
- Summary: **v2 Phase 4 — persistence and release** (epic #402: themes V2-13, V2-14, V2-15). Target branch: `master`. Depends on: Phases 1-3. Gates the v2.0 tag. - **V2-13** cellpy file format v2 (HDF5 layer): version bump; serialize `TestMetaCollection`; migration from v1 files. Done when the v1-to-v2-to-read round-trip test passes. Ship **v2 Phase 4**: a new on-disk cellpy-file that round-trips full `TestMetaCollection` (+ units/limits), cellpy-owned archive load/save (core stubs stay stubs), then release discipline (exact `cellpycore==` pin + v1→v2 migration guide) that gates the v2.0 tag. Marked done and archived after close.

## Issue #537: v2 pre-flip: replace hardcoded journal-page column literals with HeadersJournal

- Source: https://github.com/jepegit/cellpy/issues/537
- Archived files: issue537_original.md, issue537_plan.md, issue537_status.md
- Summary: Phase-3 flip prerequisite (native-headers plan Phase 0, item 2; hardcoded-column-headers-report Â§8 priority 1). Audited 2026-07-17 with `.issueflows/00-tools/scan_hardcoded_headers.py`; Remove the hard-coded journal column-name string literals flagged by `.issueflows/00-tools/scan_hardcoded_headers.py` as `HeadersJournal`, so a later header rename touches the header class only (native-headers Phase-0 prerequisite). Marked done and archived after close.

## Issue #560: Stage 3.3: port tier-1/2 loaders to declarations; retire LegacyLoaderAdapter

- Source: https://github.com/jepegit/cellpy/issues/560
- Archived files: issue560_original.md, issue560_plan.md, issue560_status.md
- Summary: Port the tier-1 and tier-2 instrument loaders to the declaration + `harmonize()` design and delete `LegacyLoaderAdapter`. The adapter is the last place where legacy-dialect frames are manufactured on the ingestion path. While it lives, every loader has two possible shapes and the parity oracle has to cover both. Finish Stage 3.3: make `harmonize(parse())` the **default** single-file raw ingestion path, with parity hardened beyond shared numeric columns, then retire the dual-path safety net where it is no longer needed. Marked done and archived after close.

## Issue #561: Stage 3.4: tier-3 loader decisions (biologics, batmo, ext_nda, local_instrument)

- Source: https://github.com/jepegit/cellpy/issues/561
- Archived files: issue561_original.md, issue561_plan.md, issue561_status.md
- Summary: Execute the tier-3 loader decisions before 2.0 so no instrument is left in an undefined state at release. Tier-3 loaders (`biologics_mpr`, `batmo_bdf`, `ext_nda_reader`, `local_instrument`) are the ones the loader plan flagged as needing a maintainer call rather than a mechanical port. Close the tier-3 loader decisions: confirm the settled port/park outcomes are on `master`, fill any remaining acceptance gap (notably `check_loader` for the two ports), and close #561. The supported-instrument matrix stays on #572. Marked done and archived after close.

## Issue #572: Stage 3.15: 2.0 migration guide, release notes, complete DEPRECATIONS.md

- Source: https://github.com/jepegit/cellpy/issues/572
- Archived files: issue572_original.md, issue572_plan.md, issue572_status.md
- Summary: Write the 2.0 migration guide and release notes — the document that tells a 1.x user what changed and what to do about it. 2.0 changes frames (polars), column names (native schema), the file format (v9), the config format (TOML), plotting entry points, and the instrument set. Every one of those is survivable with a shim; none of them is survivable without being told. Finish the Stage 3.15 docs package so a 1.x (and 2.0 alpha) user can find every user-visible break, what to do about it, and the deprecation schedule: expand [`docs/getting_started/migration_v1_to_v2.md`](../../../docs/getting_started/migration_v1_to_v2.md), land the accumulated… Marked done and archived after close.

## Issue #573: Stage 3.16: lock the file-format compatibility matrix (v8 read/write, v9, convert)

- Source: https://github.com/jepegit/cellpy/issues/573
- Archived files: issue573_original.md, issue573_plan.md, issue573_status.md
- Summary: Verify and lock the 2.0 file-format compatibility matrix end to end. The support matrix is a promise made in the release notes; it needs a test, not a sentence. Lock the cellpy **2.0 file-format support matrix** in one essential, parametrized suite (and align default `load` with that matrix), so #574’s release checklist can assert a test — not a sentence. Marked done and archived after close.

## Issue #574: Stage 3.17: cellpy 2.0.0 release checklist (benchmark acceptance, gates, tag)

- Source: https://github.com/jepegit/cellpy/issues/574
- Archived files: issue574_original.md, issue574_plan.md, issue574_status.md
- Summary: The 2.0 release checklist: benchmark acceptance, final gates, tag and publish. The release plan set a hard acceptance bar — **no metric slower than 1.x**, and the flip (bridge removal + parquet) is *expected* to win on load and summary; if it doesn't, that is a signal to investigate before shipping, not after. **Status:** draft 2026-07-26 (supersedes 2026-07-24 confirmed rc1 plan — Phases A–C done) Re-run the **2.0.0 release gates** on current `master`, fold release notes, then **tag/publish stable `v2.0.0`** from a clean `master`, bump **conda-forge feedstock**, and **start the 12-mon… Marked done and archived after close.

## Issue #594: Nightly tier-3 matrix still excludes the plotting tests

- Source: https://github.com/jepegit/cellpy/issues/594
- Archived files: issue594_original.md, issue594_plan.md, issue594_status.md
- Summary: Follow-up from #593 (#567 Phase 0). `ci.yml` (both required jobs) and `release.yml` now run the plotting tests with `MPLBACKEND=Agg`. Stop excluding `tests/test_plotutils_summary_plot.py` from the scheduled Tier-3 matrix, and run those jobs with `MPLBACKEND=Agg` so nightly catches platform plotting regressions the same way Tier-1 / release already do (#593 / #567 Phase 0). Marked done and archived after close.

## Issue #628: Iterative fixes: update conda yaml files

- Source: https://github.com/jepegit/cellpy/issues/628
- Archived files: issue628_original.md, issue628_status.md
- Summary: Interactive `/iflow-fix` session for syncing conda environment YAML files with `pyproject.toml` / `uv.lock`. Individual fixes are recorded in the local status markdown and landed together via `/iflow-close`. Interactive `/iflow-fix` session. Fixes logged below; landed via `/iflow-close`. - **2026-07-22** — Sync conda YAMLs with `pyproject.toml`: bump `cellpycore` `0.2.1`→`0.2.3`; Marked done and archived after close.

## Issue #636: Add FigureSpec dataclasses and a PlotFamily registry

- Source: https://github.com/jepegit/cellpy/issues/636
- Archived files: issue636_original.md, issue636_plan.md, issue636_status.md
- Summary: Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Phase 0–2a already landed (#593–#596). Move named `summary_plot` y-set selection behind a declarative `PlotFamily` registry in `cellpy.plotting`, and land the `FigureSpec` / `PanelSpec` / `AxisSpec` dataclasses the later Stage-1 issues will render. Marked done and archived after close.

## Issue #637: Generic plotly panel/formation layout backend

- Source: https://github.com/jepegit/cellpy/issues/637
- Archived files: issue637_original.md, issue637_plan.md, issue637_status.md
- Summary: Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Add `cellpy/plotting/backends/base.py` (render protocol) and `backends/plotly.py` with **one** generic panel/formation/facet layout engine that replaces the four `PlotlyPlotBuilder._configure_formation_{1,2,3,4}_rows` methods. Replace the four `PlotlyPlotBuilder._configure_formation_{1,2,3,4}_rows` methods with **one** N-row formation/facet layout engine in `cellpy.plotting.backends`, land a `Backend` render protocol, and wire `PlotlyPlotBuilder` through it without flipping the public `summary_plot` de… Marked done and archived after close.

## Issue #638: Port summary prepare path and flip summary_plot to prepare→spec→render

- Source: https://github.com/jepegit/cellpy/issues/638
- Archived files: issue638_original.md, issue638_plan.md, issue638_status.md
- Summary: Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Add `cellpy/plotting/prepare/summary.py` by extracting/reusing `SummaryPlotDataPreparer` (filters, rate rescaling, normalization, formation marking, CV partitioning → tidy long frame + `FigureSpec`). Make public `summary_plot` run **context → registry → prepare → backend.render** for the interactive (plotly) path: extract prepare into `cellpy/plotting/prepare/summary.py` (emitting a tidy frame + real `FigureSpec`), absorb `PlotlyPlotBuilder` into `PlotlyBackend.render`, and l… Marked done and archived after close.

## Issue #639: Matplotlib backend; retire SeabornPlotBuilder; unify backend=

- Source: https://github.com/jepegit/cellpy/issues/639
- Archived files: issue639_original.md, issue639_plan.md, issue639_status.md
- Summary: Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Add `cellpy/plotting/backends/mpl.py` that renders the same `FigureSpec` (seaborn used only for palette/style helpers, not as a separate backend). Delete `SeabornPlotBuilder`. Add `cellpy/plotting/backends/mpl.py` that renders the same summary `(frame, FigureSpec)` as plotly, delete `SeabornPlotBuilder`, and switch public `summary_plot` to `backend="plotly"|"matplotlib"` with `interactive=` as a `warn_once` alias (removal 2.1). Marked done and archived after close.

## Issue #646: Port cycles_plot to prepare→spec→render

- Source: https://github.com/jepegit/cellpy/issues/646
- Archived files: issue646_original.md, issue646_plan.md, issue646_status.md
- Summary: Part of epic #567 (Stage 2 — Other plot families on the same skeleton). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Add `prepare/curves.py` (voltage–capacity; prefer `cellpycore.curves` output, with fallback to `c.get_cap` if needed — same trick as the validation notebooks). Route `cycles_plot` through registry/spec/backends. Route public `cycles_plot` through **context → registry → prepare → backend.render**: add `cellpy/plotting/prepare/curves.py` (voltage–capacity frame + `FigureSpec`), register a cycles family, move the private plotly/matplotlib layout forks into the shared backends, and collapse… Marked done and archived after close.

## Issue #647: Port raw_plot and cycle_info_plot

- Source: https://github.com/jepegit/cellpy/issues/647
- Archived files: issue647_original.md, issue647_plan.md, issue647_status.md
- Summary: Part of epic #567 (Stage 2 â€” Other plot families on the same skeleton). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Add `prepare/raw.py` and `prepare/steps.py`; route both public functions through the shared backends. Keep `cycle_info_plot`'s matplotlib single-cycle limitation unless expanding it is trivial and oracle-covered. Route public `raw_plot` and `cycle_info_plot` through **context → registry → prepare → backend.render**: add `prepare/raw.py` and `prepare/steps.py`, register two families, move private plotly/matplotlib layout into shared backends (`kind` branches), and replace hand-composed uni… Marked done and archived after close.

## Issue #648: Add ica_plot / dva_plot families on the new pipeline

- Source: https://github.com/jepegit/cellpy/issues/648
- Archived files: issue648_original.md, issue648_plan.md, issue648_status.md
- Summary: Part of epic #567 (Stage 2 â€” Other plot families on the same skeleton). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. ICA redesign: #566 / migration notes. Register ICA/DVA figure families that consume the specced long frames from `cellpy.ica` (`dqdv` / `dvdq`). Implement prepare modules that do not re-invent the math. Register ICA/DVA figure families that consume the specced long frames from [`cellpy.ica`](cellpy/ica.py) (`dqdv` / `dvdq`), add prepare + backend `kind` branches, and expose public `ica_plot` / `dva_plot` (plotutils + re-exports). New figure-spec oracle cases green. Marked done and archived after close.

## Issue #651: Complete cli_api extraction for remaining CLI commands (new, serve, setup, â€¦)

- Source: https://github.com/jepegit/cellpy/issues/651
- Archived files: issue651_original.md, issue651_plan.md, issue651_status.md
- Summary: Finish the library-first `cli_api` extraction that #568 started. Remaining command logic still lives in `cellpy/cli.py` and is not callable from scripts without shelling out. Plan of record: [`architecture-plan/cellpy2-cli-redesign-plan.md`](https://github.com/jepegit/cellpy/blob/master/../architecture-plan) Phase 1 (command-by-command). Parent extraction: #568 / PR #586. Move the remaining CLI command logic (`info`, `serve`, `edit`, `pull`, `new`, `setup` + `migrate`) out of [`cellpy/cli.py`](cellpy/cli.py) into [`cellpy/cli_api.py`](cellpy/cli_api.py) so scripts can call the same behaviour without a Typer context. Marked done and archived after close.

## Issue #654: bug: summary CV-split plots show full capacity for with-CV / without-CV (dead selector_type)

- Source: https://github.com/jepegit/cellpy/issues/654
- Archived files: issue654_original.md, issue654_plan.md, issue654_status.md
- Summary: `summary_plot(y=\"capacities_*_split_constant_voltage\")` draws three rows (all / without CV / with CV) that are essentially **identical**. Expected: `capacity â‰ˆ capacity_without_cv + capacity_with_cv`. Discovered while visually previewing figures on the #648 branch (`dev/preview_summary_plots.py`). 1. Make CV-split summary series real again: **without-CV** via `make_summary(exclude_step_types=["cv_"])`, **with-CV** as `full − non_cv` on the selected capacity columns — so `capacities_*_split_constant_voltage` (and related helpers) stop drawing three identical panels. Marked done and archived after close.

## Issue #657: Re-base collectors' drawing half onto `cellpy.plotting`

- Source: https://github.com/jepegit/cellpy/issues/657
- Archived files: issue657_original.md, issue657_plan.md, issue657_status.md
- Summary: Part of epic #567 (Stage 3 — Collectors drawing half, Batch.plot, retire batch_plotters). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` (plus batch redesign §4.7 and collectors redesign §3.3 for the hand-offs). Collection, caching, autonaming, and frame persistence stay in collectors (out of scope to redesign). Re-base collectors' drawing half onto `cellpy.plotting`: already-collected tidy frames (`cell` / `group` / `sub_group`) render through prepare→spec→render with `layout=` / `kind=` options; delete local plotter bodies; Marked done and archived after close.

## Issue #658: Wire `Batch.plot()` to plotting and delete `batch_plotters.py`

- Source: https://github.com/jepegit/cellpy/issues/658
- Archived files: issue658_original.md, issue658_plan.md, issue658_status.md
- Summary: Part of epic #567 (Stage 3 — Collectors drawing half, Batch.plot, retire batch_plotters). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` (batch redesign §4.7). Closes the epic acceptance criteria together with #657: one drawing home, batch facade unchanged, `batch_plotters.py` gone. Wire `Batch.plot()` into `cellpy.plotting` (multi-cell cycle-life summary: capacity + CE + optional IR/rate panels), delete `cellpy/utils/batch_tools/batch_plotters.py`, and document backend triage — without breaking the batch facade (`b.plot(...)`, `b.plotter.figure`). Marked done and archived after close.

## Issue #669: bad warnings in v1 collectors

- Source: https://github.com/jepegit/cellpy/issues/669
- Archived files: issue669_original.md, issue669_plan.md, issue669_status.md
- Summary: When running this in a Jupyter Lab notebook: ```python cells_collected = collectors.BatchCyclesCollector( b, ) ``` We receive all these warnings (way too much): ``` WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1370 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data). Stop collector notebooks from flooding with per-cycle `WARNING:root` spam when noisy voltage curves hit the max-segments fallback or half-cycle ICA fails — keep one visible signal, demote repeats. - Do not change interpolation / ICA numeric behaviour (still skip / empty arrays). Marked done and archived after close.

## Issue #673: Iterative fixes: docs cleanup

- Source: https://github.com/jepegit/cellpy/issues/673
- Archived files: issue673_original.md, issue673_status.md
- Summary: Interactive `/iflow-fix` session for iterative documentation cleanup. Individual fixes are recorded in the local status markdown and landed together via `/iflow-close`. Interactive `/iflow-fix` session. Fixes recorded below; landed together via `/iflow-close`. - 2026-07-24: Fill `docs/getting_started/index.md` with short intro + links matching Getting started `nav` (installation → setup → checkup → basic usage → migration). Marked done and archived after close.

## Issue #675: Iterative fixes: pin-cellpycore

- Source: https://github.com/jepegit/cellpy/issues/675
- Archived files: issue675_original.md, issue675_plan.md, issue675_status.md
- Summary: Interactive `/iflow-fix` session (landing via `/iflow-close yolo`). Individual fixes are recorded in the status markdown and landed together in one PR. **First fix:** pin `cellpycore` from `0.2.3` â†’ `0.2.4` in `pyproject.toml` / `uv.lock` (new cellpy-core release on PyPI). Pin `cellpycore` to the new PyPI release `0.2.4`. 1. Bump `"cellpycore==0.2.3"` → `"cellpycore==0.2.4"` in `pyproject.toml`. 2. Regenerate lock with `UV_NO_SOURCES=1 uv lock` (no path override). 3. Smoke with `uv sync --no-sources` + `pytest -m essential`. Marked done and archived after close.

## Issue #676: Update docs and batch-loader examples for native step/raw headers (cellpy 2.0)

- Source: https://github.com/jepegit/cellpy/issues/676
- Archived files: issue676_original.md, issue676_plan.md, issue676_status.md
- Summary: On cellpy 2.0.0rc1 (native headers), common batch post-processing notebooks fail because they still hard-code 1.x column names. Reproducer (standard batch-loader template pattern): ```python discharge = steps.query("type=='discharge'") ``` raises `UndefinedVariableError: name 'type' is not defined` because the step table column is now `step_type`. Make cellpy 2.0 docs teach **native** frame headers and the `c.schema.*` API so batch/notebook code that still hard-codes 1.x names (`type`, `cycle_index`, `discharge_capacity`, …) has an obvious, correct migration path Marked done and archived after close.

## Issue #679: bug in BatchICACollector

- Source: https://github.com/jepegit/cellpy/issues/679
- Archived files: issue679_original.md, issue679_plan.md, issue679_status.md
- Summary: Bug in v2.0.0rc1. Running the following cell in batch loader notebook: ```python cycles_collected = collectors.BatchICACollector( b, plot_type="fig_pr_cycle", cycles=[1, 2, 3], palette="Viridis", data_collector_arguments={"voltage_resolution": 0.01}, ) ``` Error message: ```python WARNING:py.warnings:[C:\Users\jepe\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\utils\collectors.… Make `BatchICACollector(..., plot_type="fig_pr_cycle")` render without `KeyError: 'cycle_num'`, matching the already-working `fig_pr_cell` / `film` paths on the same ICA frame. Marked done and archived after close.

## Issue #680: Update docs about data structure

- Source: https://github.com/jepegit/cellpy/issues/680
- Archived files: issue680_original.md, issue680_plan.md, issue680_status.md
- Summary: The chapter about data structures looks like it is outdated. Update it reflecting the v2 structure Bring the user-facing **Data structure** fundamentals chapter up to date with cellpy **2.x** object layout (`CellpyCell` / `Data` / frames / metadata / `c.schema`), without redoing the column-header work already landed in #676. - Docs only — no runtime / API changes. Marked done and archived after close.

## Issue #682: chapter for agents

- Source: https://github.com/jepegit/cellpy/issues/682
- Archived files: issue682_original.md, issue682_plan.md, issue682_status.md
- Summary: We should provide a chapter for agents on how to use cellpy. Tasks: - Search for examples of how it is done in other projects (web) - Decide on a structure and content. - Remember that the agents need to find it. - It's probably good to include many examples. Give coding agents a discoverable, example-heavy guide for **using cellpy as a library** (primary persona: researcher building a small app/GUI), plus a maintenance hook so future API work updates that guide. Marked done and archived after close.

## Issue #688: Deal-breaker: remote OtherPath rglob / auto_use_file_list skips symlink project dirs under rawdatadir

- Source: https://github.com/jepegit/cellpy/issues/688
- Archived files: issue688_original.md, issue688_plan.md, issue688_status.md
- Summary: After the switch from the self-built / Fabric-based `OtherPath` to `universal-pathlib` (`UPath` + fsspec/Paramiko), **recursive remote file search no longer follows symlink directories** under `rawdatadir`. This breaks the normal batch workflow when project folders under the raw root are symlinks (common on our IFE `odin` layout, e.g. `projects/LongLife` → real storage). Restore remote recursive discovery under a shared `rawdatadir` when project folders are **symlinks** (UPath/fsspec currently skips them), so batch `auto_use_file_list` / `search_for_files` populate `raw_file_names` again. Marked done and archived after close.

## Issue #690: perf: speed up remote auto_use_file_list / OtherPath.rglob dump

- Source: https://github.com/jepegit/cellpy/issues/690
- Archived files: issue690_original.md, issue690_plan.md, issue690_status.md
- Summary: After #688, remote batch discovery works again when project folders under `rawdatadir` are symlinks, but `Batch.auto_use_file_list=True` against a shared projects root is **very slow**. Make remote `Batch.auto_use_file_list` / `find_in_raw_file_directory` dumps over a large shared `rawdatadir` (e.g. `…/projects` with symlink project dirs) substantially faster (seconds–tens of seconds, not minutes), without regressing - Keep UPath-based `OtherPath`; Marked done and archived after close.

## Issue #695: Iterative fixes: check docs for mistakes

- Source: https://github.com/jepegit/cellpy/issues/695
- Archived files: issue695_original.md, issue695_plan.md, issue695_status.md
- Summary: Interactive `/iflow-fix` session to check the documentation for spelling, logic errors, outdated information, and other polish. Individual fixes are recorded in the issue status markdown and landed together via `/iflow-close`. Run an interactive `/iflow-fix` pass over the cellpy documentation: find and fix spelling, broken/outdated facts, and small logic/clarity mistakes. Land everything in one PR via `/iflow-close`. Marked done and archived after close.

## Issue #724: include marimo notebooks

- Source: https://github.com/jepegit/cellpy/issues/724
- Archived files: issue724_original.md, issue724_plan.md, issue724_status.md
- Summary: This issue only relates to documentation. Let us try to also include marimo notebooks in the docs. There might be supported way to do it in zensical. Prove that marimo notebooks can ship in the Zensical docs: editable sources under `docs/examples/marimo/`, pages in the Tutorials nav via [`marimo-md-export`](https://jmarshrossney.github.io/marimo-md-export/), documented render workflow. Marked done and archived after close.

## Issue #768: Release v2.1

- Source: https://github.com/jepegit/cellpy/issues/768
- Archived files: issue768_original.md, issue768_plan.md, issue768_status.md
- Summary: Tasks 1. Make sure all tests run (including CI) 2. Release v2.1.0 to PyPI 3. Merge changes from documentation in master to v2-docs-stable 4. Create conda version for v2.1.0 if auto creation (bot) failed. Ship **cellpy 2.1.0** (stable) from clean `master`: green tests/CI → PyPI via `gh release create v2.1.0` → sync docs to `v2-docs-stable` → conda-forge `2.1.0` (bot or manual feedstock bump). Marked done and archived after close.
