# Issue #372 - Plan

## Iteration 2 (current): coverage slice on helpers + filefinder, plus two test-suite nits

### Goal

Continue the tests-first hardening of #372: add offline unit tests for the highest-value
uncovered pure functions in `cellpy/utils/helpers.py` and path logic in
`cellpy/readers/filefinder.py`, and fix two small test-suite quality nits from the
iteration-1 backlog.

### Constraints

- Tests-first: no behaviour changes to library code except the two named nits.
- Fixture-light: prefer fixture-free / `tmp_path`-based tests (see the reference pattern in
  `tests/test_pure_functions.py` and the guide
  [`testing-and-coverage.md`](../04-designs-and-guides/testing-and-coverage.md)).
- Keep the default-deselected suite green; do not mass-unskip anything.
- This environment is Linux (WSL); iteration 1 ran on Windows. `sqlalchemy-access` is
  Windows-only, so arbin `.res`-dependent tests may be skipped/failing here — do not chase
  them in this iteration.

#### Prior art

- `tests/test_pure_functions.py` — established fixture-free pattern from iteration 1;
  new pure-function tests should mirror it (extend it or a sibling file).
- `tests/test_helpers.py` — existing but thin (4 tests, all needing the `dataset` fixture);
  new offline helpers tests go in a separate fixture-free section/file so they stay fast.
- `tests/test_filefinder.py` (82 lines) and `tests/test_otherpaths.py` (306 lines) already
  exist — extend rather than duplicate.
- Toolbox `.issueflows/00-tools/`: empty, nothing to reuse.

### Approach

1. **Phase 0 — env sanity.** Verify `.venv` on this Linux machine can run the suite
   (`uv run pytest tests/test_pure_functions.py`); if the env is empty, populate it per
   `testing-and-coverage.md`. Record a fresh baseline for the files we touch.
2. **Phase 1 — `utils/helpers.py` offline tests.** Target pure summary/outlier functions
   operating on synthetic `pandas` frames (no data files):
   - `remove_outliers_from_summary_on_value`, `remove_outliers_from_summary_on_zscore`,
     `remove_outliers_from_summary_on_window`, `remove_outliers_from_summary_on_nn_distance`
   - `remove_first_cycles_from_summary`, `remove_last_cycles_from_summary`
   - `add_normalized_cycle_index`, `create_rate_column`, `create_group_names`
   Small synthetic summary frames built in-test; assert row filtering / added columns.
3. **Phase 2 — `readers/filefinder.py` tests.** Use `tmp_path` to build fake raw-file
   trees and exercise `search_for_files` / `list_raw_file_directory` glob + extension
   logic without touching real data dirs.
4. **Phase 3 — nits.**
   - `cellpy/utils/easyplot.py:524`: fix `SyntaxWarning: invalid escape sequence '\i'`
     (raw string or escaped backslash).
   - `tests/test_cell_readers.py:99`: change `@pytest.mark.xfail(WrongFileVersion)` to
     `@pytest.mark.xfail(raises=WrongFileVersion)`.
5. **Phase 4 — wrap-up.** Coverage re-check on the touched modules, update
   `issue372_status.md` (numbers + shrunken backlog), keep the guide doc current.

### Files to touch

- `tests/test_helpers.py` — new fixture-free tests (or a clearly separated section).
- `tests/test_filefinder.py` — new `tmp_path`-based tests.
- `tests/test_cell_readers.py` — xfail arg fix (1 line).
- `cellpy/utils/easyplot.py` — escape-sequence fix (1 line).
- `.issueflows/01-current-issues/issue372_status.md` — iteration-2 record.

### Test strategy

- `uv run pytest tests/test_helpers.py tests/test_filefinder.py tests/test_pure_functions.py`
  while iterating; full `uv run pytest` before closing.
- `uv run coverage run -m pytest && uv run coverage report` to quantify the bump on
  `helpers.py` / `filefinder.py`.

### Out of scope (stays on backlog)

- `utils/collectors.py` (0%) and `utils/example_data.py` (0%) tests.
- Stabilizing the flaky `test_cycling_summary_plotter`.
- Re-including `test_plotutils_summary_plot.py` in CI.
- `sqlalchemy-access` uv-on-Windows install reliability.
- TODO/FIXME triage in `readers/cellreader.py`.

### Open questions

- None — scope is a direct continuation of the confirmed iteration-1 backlog priorities.

---

## Iteration 1 (done): test infra, coverage baseline & triage (broad-shallow, tests-first)

Confirmed plan for the first iteration of #372 ("code cleanups and test improvements before shipping").

Priority chosen: **test-suite improvements**. Scope chosen: **broad shallow sweep** - set up
test infra + coverage baseline + triage across the whole repo first, then a small slice of new
tests. Bug-fixing and large refactors are explicitly deferred to later iterations of #372.

### Phase 1 - Make the test suite runnable under uv
- `.venv` was empty and `pyproject.toml` has no `[project]` table, so `uv sync` cannot manage
  cellpy's `setup.py` deps. Populate `.venv` via `uv pip install -e ".[all]"` plus test tooling
  (`pytest pytest-timeout pytest-benchmark lmfit coverage`).
- Confirm `uv run pytest` works and document the canonical command.

### Phase 2 - Coverage baseline + run health
- Use the already-present `coverage` dep (`uv run coverage run -m pytest` + `coverage report`).
- Add `[tool.coverage.run]` / `[tool.coverage.report]` to `pyproject.toml` (source=cellpy, omit
  libs/legacy, branch coverage, show_missing).
- Run the default-selected suite, capture pass/fail and per-module coverage as the baseline.

### Phase 3 - Triage gated/skipped tests
- Enumerate every `skip/xfail` and custom marker plus the CI-ignored
  `tests/test_plotutils_summary_plot.py`.
- Classify each (broken / intentional-local / safe-to-enable). Do not mass-unskip.

### Phase 4 - Land a small representative slice of new tests
- Add 2-4 focused, fixture-free unit tests on high-value uncovered pure functions.
- Goal: a proven pattern + measurable coverage bump, not exhaustive coverage.

### Deliverables
- Working `uv run pytest` + coverage command, coverage config in `pyproject.toml`.
- `issue372_status.md`: baseline numbers, skipped-test triage table, prioritized gap backlog.
- A durable testing/coverage guide under `.issueflows/04-designs-and-guides/`.

### Out of scope (this iteration)
- Fixing flagged correctness TODOs, large refactors (e.g. `dataset`->`cell` rename), broad
  lint/type-hint cleanups. Logged in the status backlog for later #372 passes.
