# Issue #372 - Plan: Test infra, coverage baseline & triage (broad-shallow, tests-first)

Confirmed plan for the first iteration of #372 ("code cleanups and test improvements before shipping").

Priority chosen: **test-suite improvements**. Scope chosen: **broad shallow sweep** - set up
test infra + coverage baseline + triage across the whole repo first, then a small slice of new
tests. Bug-fixing and large refactors are explicitly deferred to later iterations of #372.

## Phase 1 - Make the test suite runnable under uv
- `.venv` was empty and `pyproject.toml` has no `[project]` table, so `uv sync` cannot manage
  cellpy's `setup.py` deps. Populate `.venv` via `uv pip install -e ".[all]"` plus test tooling
  (`pytest pytest-timeout pytest-benchmark lmfit coverage`).
- Confirm `uv run pytest` works and document the canonical command.

## Phase 2 - Coverage baseline + run health
- Use the already-present `coverage` dep (`uv run coverage run -m pytest` + `coverage report`).
- Add `[tool.coverage.run]` / `[tool.coverage.report]` to `pyproject.toml` (source=cellpy, omit
  libs/legacy, branch coverage, show_missing).
- Run the default-selected suite, capture pass/fail and per-module coverage as the baseline.

## Phase 3 - Triage gated/skipped tests
- Enumerate every `skip/xfail` and custom marker plus the CI-ignored
  `tests/test_plotutils_summary_plot.py`.
- Classify each (broken / intentional-local / safe-to-enable). Do not mass-unskip.

## Phase 4 - Land a small representative slice of new tests
- Add 2-4 focused, fixture-free unit tests on high-value uncovered pure functions.
- Goal: a proven pattern + measurable coverage bump, not exhaustive coverage.

## Deliverables
- Working `uv run pytest` + coverage command, coverage config in `pyproject.toml`.
- `issue372_status.md`: baseline numbers, skipped-test triage table, prioritized gap backlog.
- A durable testing/coverage guide under `.issueflows/04-designs-and-guides/`.

## Out of scope (this iteration)
- Fixing flagged correctness TODOs, large refactors (e.g. `dataset`->`cell` rename), broad
  lint/type-hint cleanups. Logged in the status backlog for later #372 passes.
