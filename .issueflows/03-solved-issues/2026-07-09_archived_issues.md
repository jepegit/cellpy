# Archived issues — 2026-07-09

Pre-archive git ref: `7e2c074c6d4cc047855a2888c6582030bb75cbdf`
Recover any archived file with `git show 7e2c074c6d4cc047855a2888c6582030bb75cbdf:<path>` (or browse `git log -- <path>`).

## Issue #354: update build procedure

- Source: https://github.com/jepegit/cellpy/issues/354
- Archived files: issue354_original.md, issue354_plan.md, issue354_status.md
- Summary: Replaced `setup.py`, `requirements*.txt`, and `MANIFEST.in` with a single `pyproject.toml` managed through `uv` (hatchling backend, git-tag dynamic versioning via `uv-dynamic-versioning`). Runtime version now comes from `importlib.metadata`; a Docker-based local build test (`docker/Dockerfile.build-test`, `scripts/build_test.sh`) was added. Legacy build files removed and design recorded in `.issueflows/04-designs-and-guides/build-and-versioning.md`. CI/conda migration deferred to a follow-up.

## Issue #356: Export bdf for dsToolbox

- Source: https://github.com/jepegit/cellpy/issues/356
- Archived files: issue356_original.md, issue356_plan.md, issue356_status.md
- Summary: Added Battery Data Format (BDF) export for raw time-series data with optional cycle filtering, targeting UiA's dsToolbox and other BDF-aware tools. Shipped `CellpyCell.to_bdf`, new `cellpy/exporters/` and `cellpy/filters/` packages, pint-driven unit conversion, preferred-label and machine header styles, and CSV/Parquet output. Established the layering rule that `CellpyCell` imports from `cellpy.exporters`/`cellpy.filters`, never from `cellpy.utils`.

## Issue #360: CI pipeline problems

- Source: https://github.com/jepegit/cellpy/issues/360
- Archived files: issue360_original.md, issue360_plan.md, issue360_status.md
- Summary: Fixed two independent CI failures. Added `pyarrow>=16` to `install_requires` so pip-install workflows no longer fail when polars calls `to_pandas()` in the Neware nda backend. Switched AppVeyor to 64-bit Miniconda (`Visual Studio 2022` image, `C:\Miniconda3-x64`) and trimmed the matrix to Python 3.12 as a Windows-conda smoke check.

## Issue #363: Add filtering possibility to plotters in plotutils

- Source: https://github.com/jepegit/cellpy/issues/363
- Archived files: issue363_original.md, issue363_plan.md, issue363_status.md
- Summary: Added generic summary-row filtering in `cellpy/filters/summary.py` with a registry-based extension point, exposed via `CellpyCell.filter_summary` and a `filters=` parameter on `summary_plot`. New `*_with_rate` predefined y-sets add a C-rate subplot; optional `nominal_capacity` rescales rate columns before plotting. Design recorded in `.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`.

## Issue #365: units when exporting in bdf

- Source: https://github.com/jepegit/cellpy/issues/365
- Archived files: issue365_original.md, issue365_plan.md, issue365_status.md
- Summary: Added a `bdf_units` keyword argument to `to_bdf` (exporter and `CellpyCell` wrapper) so callers can control units written into BDF column labels and values. Default behaviour remains strict BDF spec; overrides produce non-compliant files with an INFO log and hard-fail on pint-incompatible units. Docstring examples and design-doc Q7 row added.

## Issue #366: bug-plotutils-summary-plot

- Source: https://github.com/jepegit/cellpy/issues/366
- Archived files: issue366_original.md, issue366_status.md
- Summary: Fixed a crash when calling `summary_plot` with `formation_cycles=False` or `0` on pec example data (`TypeError: bad operand type for unary ~: 'slice'`). Added `SummaryPlotConfig.__post_init__` to coerce `formation_cycles` and force `show_formation=False` when below 1, mirroring legacy normalisation. Regression tests cover both Plotly and Seaborn backends.

## Issue #377: Prepare cellpy to consume cellpy-core (isolate the Data object via a core seam)

- Source: https://github.com/jepegit/cellpy/issues/377
- Archived files: issue377_original.md, issue377_status.md
- Summary: Established the cellpy-core integration seam: `CellpyCell` delegates Data ownership and the summary pipeline to `OldCellpyCellCore`. Raised Python floor to 3.13, added cellpycore as a git dependency, updated CI/env files, and added `tests/test_slim.py` acceptance tests. Required companion fixes in cellpy-core (legacy bridge bugs, header alignment, summary column pruning). Full suite green on Python 3.13.

## Issue #378: Add header/unit parity contract tests between cellpy and cellpy-core

- Source: https://github.com/jepegit/cellpy/issues/378
- Archived files: issue378_original.md, issue378_plan.md
- Summary: Added parametrized contract tests in `tests/test_core_settings_parity.py` asserting dataclass field names and defaults match between `cellpy.parameters.internal_settings` and `cellpycore.legacy` for `HeadersNormal`, `HeadersSummary`, `HeadersStepTable`, and `CellpyUnits`. Test skips gracefully when cellpy-core is not installed; failures name the drifted fields.
