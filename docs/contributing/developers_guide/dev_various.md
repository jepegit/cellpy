# Various

## Running tests

Prefer `uv` so the project `.venv` and lockfile are used:

```shell
uv sync
uv run pytest                  # full suite (default marker filters apply)
uv run pytest -m essential     # fast smoke — same subset as CI essential job
```

Default `addopts` in `pyproject.toml` deselects several markers
(`slowtest`, `smoketest`, `unimportant`, `unfinished`, `onlylocal`). Opt in
explicitly when you need those, e.g. `uv run pytest -m onlylocal`.

Benchmarks are separate (`pytest -m benchmark` or the `benchmarks/` tree) —
see [GitHub workflows](#github-workflows) below.

More detail on golden fixtures and suite layout:
[`tests/README.md`](https://github.com/jepegit/cellpy/blob/master/tests/README.md).

### The `essential` marker

`@pytest.mark.essential` marks tests that every PR must keep green. Use it for:

- read → step table → summary pipeline smoke
- cellpy / cellpy-core parity contract
- golden-fixture oracles under `tests/data/goldens/`
- other regressions you cannot leave to the weekly scheduled run

Keep the set small so the essential job stays fast. Platform-specific paths
(Windows ODBC, macOS-only skips) usually stay in the full suite unless you add
a targeted essential job for that platform.

### Using `pytest` fixtures

#### Retrieve constants during tests

There is a fixture in `conftest.py` named `parameters` that exposes variables
defined in `tests/fdv.py`. Add new test constants by editing `fdv.py`.

#### Other

Check `tests/conftest.py` for other fixtures.

#### Example

```python
from cellpy import prms

# using the ``parameters`` and the ``cellpy_data_instance`` fixtures.

def test_set_instrument_selecting_default(cellpy_data_instance, parameters):
    prms.Instruments.custom_instrument_definitions_file = parameters.custom_instrument_definitions_file
    cellpy_data_instance.set_instrument(instrument="custom")
```

## GitHub workflows

| Workflow | When | What |
|----------|------|------|
| [`.github/workflows/ci.yml`](https://github.com/jepegit/cellpy/blob/master/.github/workflows/ci.yml) | PRs and pushes to `master` | **essential** — `uv run pytest -m essential`, then `cellpy setup` / `info --check`. **full** — `uv run pytest` (default filters) with batch extras. Doc-only path changes under `docs/`, `*.md`, `.issueflows/`, etc. are skipped. |
| [`.github/workflows/ci-scheduled.yml`](https://github.com/jepegit/cellpy/blob/master/.github/workflows/ci-scheduled.yml) | Weekly + manual **Run workflow** | Conda / pip platform matrix, notebook smoke, conda-forge install check. Does not block merges. |
| [`.github/workflows/release.yml`](https://github.com/jepegit/cellpy/blob/master/.github/workflows/release.yml) | GitHub release published | Tag validation → `pytest -m essential` → PyPI publish. |
| [`.github/workflows/benchmarks.yml`](https://github.com/jepegit/cellpy/blob/master/.github/workflows/benchmarks.yml) | Manual / separate from merge gate | Performance benchmarks vs baselines. |
| [`.github/workflows/docs.yml`](https://github.com/jepegit/cellpy/blob/master/.github/workflows/docs.yml) | Docs changes | Zensical build + link/issue checks. |

On a PR, treat **essential** and **full** as the linux/`uv` merge signals. Run
the scheduled workflow manually before a release if the weekly run is stale.

## Adding another config parameter

Session config lives in **`cellpy.config`** (pydantic models + layered TOML).
`cellpy.parameters.prms` is a deprecated shim — do not add new fields there, and
do not hand-edit `.cellpy_prms_default.conf` as the source of defaults.

1. Add the field (with type and default) on the right section model in
   [`cellpy/config/models.py`](https://github.com/jepegit/cellpy/blob/master/cellpy/config/models.py).
2. Read it as `cellpy.config.<section>.<field>` (or via `get_config()`).
3. Regenerate the user-facing reference:

   ```shell
   uv run python -m cellpy.config.reference
   ```

4. If the new key is a path that setup/CLI must treat as `OtherPath`, also add
   it to `OTHERPATHS` in `cellpy/parameters/internal_settings.py`. That file is
   for headers, meta helpers, and path-key lists — not general session config.

During the v2 window, `cellpy setup` may still dual-write legacy YAML and
`cellpy.toml`. When a user TOML is present, it wins over `.cellpy_prms_*.conf`.

See also [Setup and configuration](../../getting_started/configuration.md),
[Configuration reference](../../getting_started/configuration_reference.md),
and [Coming from cellpy 1.x](../../getting_started/migration_v1_to_v2.md).

## Installing pyodbc on Mac without conda

If you do not want to use `conda`, you might miss a couple of libraries.

The easiest fix is to install `unixodbc` using `brew` as explained in
[Stack Overflow #54302793](https://stackoverflow.com/questions/54302793/dyld-library-not-loaded-usr-local-opt-unixodbc-lib-libodbc-2-dylib).
