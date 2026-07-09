# Testing and coverage (running the suite under uv)

Durable guide for running cellpy's test suite and coverage locally. Established in issue #372.

## Environment setup

`pyproject.toml` has no `[project]` table (cellpy is a legacy `setup.py` project), so `uv sync`
cannot resolve the runtime/test dependencies. Populate the uv `.venv` with an editable install plus
test tooling:

```bash
uv pip install -e ".[all]" pytest pytest-timeout pytest-benchmark lmfit coverage
```

On Windows, also install the Access dialect (declared in `setup.py` as a platform-conditional dep,
but **not** pulled in by the editable install above):

```bash
uv pip install sqlalchemy-access
```

Without `sqlalchemy-access`, every test that reads an arbin `.res` file fails with
`sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:access` (~43 tests).
Installing it (it pulls `pywin32`) makes them pass; no MS Access Database Engine ODBC driver was
required in our environment.

Note: the very first import after a fresh install builds the matplotlib font cache and can take a
couple of minutes. Subsequent runs are fast.

## Running tests

Golden-fixture convention and the `essential` marker are documented in [`tests/README.md`](../../tests/README.md).

```bash
# Canonical local run (uses the marker deselection in pyproject.toml addopts)
uv run pytest

# A single file / test
uv run pytest tests/test_pure_functions.py
uv run pytest tests/test_cellpy.py::test_load_and_save_res_file
```

The default `addopts` in `pyproject.toml` deselects slow/local/unfinished tests:
`-m "not slowtest and not smoketest and not unimportant and not unfinished and not onlylocal"`.

### Marker policy
- `slowtest` - benchmarks and network/GitHub/cookiecutter pulls; deselected by default.
- `skip(reason="only run locally")` - needs local resources (sftp, mdbtools, real raw data).
- `skip(reason="...not needed in CI/CD...")` - downloads example data; run manually when needed.
- `skip_on_macos` - macOS CI flakiness.
- `xfail` - documents deprecated / not-implemented behavior; expected to fail.
- CI additionally `--ignore=tests/test_plotutils_summary_plot.py`; that file runs fine locally once
  the `[all]` extras (plotly/seaborn/kaleido) are installed.

## Coverage

Coverage config lives in `pyproject.toml` (`[tool.coverage.run]` / `[tool.coverage.report]`,
source = `cellpy`, branch coverage on, libs/legacy omitted). Uses the `coverage` dep (no
`pytest-cov` needed):

```bash
uv run coverage run -m pytest      # collect
uv run coverage report             # per-module summary with missing lines
uv run coverage html               # browseable htmlcov/ report
uv run coverage xml                # coverage.xml (for CI tooling)
```

Coverage artifacts (`.coverage`, `coverage.xml`, `htmlcov/`) are already in `.gitignore`.

Baseline (issue #372, default-deselected suite, `sqlalchemy-access` installed): 475 passed,
**44% total coverage**. See `01-current-issues/issue372_status.md` (or the archived copy) for the
per-module breakdown and the coverage backlog.

## Writing low-cost tests

Prefer fixture-free unit tests for pure functions (no data files, network, or `CellpyCell`
fixtures) - they are fast and deterministic. `tests/test_pure_functions.py` is the reference
pattern (interpolation helpers, path short-circuits, list transforms).
