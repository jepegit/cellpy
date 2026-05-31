# Issue #372 - Status

- [ ] Done

Broad-shallow, tests-first first iteration. Scope: test infrastructure, coverage baseline,
skipped-test triage, and a small slice of new unit tests. Code cleanups / bug fixes / large
refactors are deferred to later iterations (see backlog below).

## Done this iteration

### Phase 1 - Test infra under uv
- `.venv` was empty and `pyproject.toml` has no `[project]` table; populated the env with:
  `uv pip install -e ".[all]" pytest pytest-timeout pytest-benchmark lmfit coverage`.
- **Key finding:** `uv pip install -e ".[all]"` did **not** install the platform-conditional dep
  `sqlalchemy-access;platform_system=="windows"`. Without it, ~43 arbin `.res` tests fail with
  `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:access`.
  Installing `sqlalchemy-access` (pulls `pywin32`) fixes all of them - no MS Access Database
  Engine driver was needed in this environment.
- Canonical local command: `uv run pytest` (see the testing guide in `04-designs-and-guides/`).

### Phase 2 - Coverage baseline
- Added `[tool.coverage.run]` / `[tool.coverage.report]` to `pyproject.toml` (source=cellpy,
  branch coverage, omit libs/legacy/_version, show_missing).
- Baseline (default-deselected suite, with `sqlalchemy-access` installed):
  **475 passed, 0 failed, 0 errors, 17 skipped, 12 deselected, 13 xfailed** in ~4m23s.
- **Coverage: 44%** total (23,113 stmts, 12,324 missed, 6,906 branches).
  (Before installing `sqlalchemy-access`, with the res tests failing, it was 40%.)

Lowest-covered modules (top backlog targets):

| Module | Stmts | Cover |
| --- | --- | --- |
| `cellpy/utils/collectors.py` | 1327 | 0% |
| `cellpy/readers/sql_dbreader.py` | 379 | 0% |
| `cellpy/readers/instruments/neware_xlsx.py` | 269 | 0% |
| `cellpy/utils/example_data.py` | 128 | 0% |
| `cellpy/utils/batch_tools/sqlite_from_excel_db.py` | 117 | 0% |
| `cellpy/utils/batch_tools/batch_plotters.py` | 792 | 8% |
| `cellpy/utils/easyplot.py` | 764 | 11% |
| `cellpy/utils/helpers.py` | 671 | 11% |
| `cellpy/readers/instruments/maccor_txt.py` | 272 | 14% |
| `cellpy/internals/core.py` | 82 | 19% |
| `cellpy/utils/batch.py` | 1035 | 22% |
| `cellpy/readers/instruments/arbin_res.py` | 687 | 28% |
| `cellpy/readers/filefinder.py` | 212 | 31% |
| `cellpy/internals/otherpath.py` | 791 | 34% |
| `cellpy/utils/plotutils.py` | 2228 | 35% |
| `cellpy/cli.py` | 1129 | 39% |
| `cellpy/readers/cellreader.py` | 3481 | 52% |

### Phase 3 - Skipped/marker triage

| Test(s) | Marker | Reason | Verdict |
| --- | --- | --- | --- |
| `test_plotutils_summary_plot.py` (7 cases) | `skipif(not plotly/seaborn)` | auto-skip if optional plot deps missing | Intentional. Runs locally with `[all]` extras; CI `--ignore`s the file. |
| `test_batch.py::test_cycling_summary_plotter` | `skip` | "shaky test - fails sometimes on appveyor" | Flaky - investigate/stabilize later (backlog). |
| `test_batch.py::test_load_full_journal_excel...` | `skip_on_macos` | macOS CI flakiness | Intentional, keep. |
| `test_batch.py` `test_update_time`, `test_link_time` | `slowtest` | timing benchmarks | Intentional, deselected by default. |
| `test_cellpy_cmd.py` (8 `test_pull_*`, `test_cli_new*`) | `slowtest` | network pulls from GitHub / cookiecutter | Intentional, deselected. Some noted "breaks sometimes". |
| `test_cell_readers.py::test_load_step_specs` | `slowtest` | slow raw load | Intentional, deselected. |
| `test_cell_readers.py` 407/420/1075/1089 | `skip` | "only run locally" (external sftp paths, mdbtools) | Intentional - needs local resources. |
| `test_cellpy_method_integrity.py` 103/113/127 | `skip` | "only run locally" | Intentional - needs local raw cells. |
| `test_dbreader.py::test_convert_from_excel_to_sqlite` | `skip` | "experimental - only run locally" | Intentional. |
| `test_example_data.py` (8 tests) | `skip` | "not needed in CI/CD pipeline" (downloads data) | Intentional - reason `example_data.py` is 0%. Offline tests possible (backlog). |
| `test_cell_readers.py` version_4 / select_steps / populate_step_dict / cap_mod_summary_fail / get_ir / deprecations / set_nominal_capacity / xldate | `xfail` | deprecated / not-implemented behavior | Correct documentation of expected failures, keep. |
| `test_ica.py` none_data / short_data | `xfail` | error-path behavior | Correct, keep. |
| `test_instrument_registering.py` 2 tests | `xfail` | missing-file / default-not-defined paths | Correct, keep. |

No tests were genuinely broken once `sqlalchemy-access` was installed. None were mass-unskipped.

### Phase 4 - New tests
- Added `tests/test_pure_functions.py` (10 fixture-free unit tests, ~0s each) covering previously
  uncovered pure functions:
  - `cellpy.readers.core.interpolate_y_on_x` (default-columns, `number_of_points`, `direction=-1`,
    and the `(start, end, n)` tuple `new_x` branch).
  - `cellpy.internals.core.check_connection` (local-path short-circuit returns `{}`; no network).
  - `cellpy.utils.helpers.add_cv_step_columns` and `fix_group_names`.
- Confirmed these exercise lines that were in the baseline "missing" set (e.g. `internals/core.py`
  rose from 19% to 31% from this file alone; `helpers.add_cv_step_columns` / `fix_group_names`
  previously uncovered).

## Backlog for later #372 iterations

Test coverage (prioritized):
- Offline unit tests for `utils/helpers.py` (11%, many pure summary/outlier/interpolation funcs).
- `readers/filefinder.py` (31%) and `internals/otherpath.py` (34%) - path logic is unit-testable
  with `tmp_path`.
- `utils/collectors.py` (0%, 1327 stmts), `utils/example_data.py` (0%, offline-mockable).
- Stabilize the flaky `test_cycling_summary_plotter` (currently skipped).
- Consider re-including `test_plotutils_summary_plot.py` in CI now that `[all]` extras install.

Code-quality nits spotted (not fixed this round):
- `cellpy/utils/easyplot.py:524` emits `SyntaxWarning: invalid escape sequence '\i'`.
- `tests/test_cell_readers.py:99` `@pytest.mark.xfail(WrongFileVersion)` passes the exception class
  as the positional `condition` rather than `raises=WrongFileVersion`.
- ~330 `TODO/FIXME` markers (densest in `readers/cellreader.py`), incl. flagged correctness notes
  like "this breaks (gives 711 instead of 593)" - triage in a dedicated cleanup pass.

Infra:
- Decide how to make `sqlalchemy-access` install reliably under uv on Windows (it is declared in
  `setup.py` but skipped by `uv pip install -e ".[all]"`), so `uv run pytest` is green out of the box.
