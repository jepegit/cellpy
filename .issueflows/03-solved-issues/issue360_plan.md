# Plan for issue #360: CI pipeline problems

## Goal

Make the failing CI runs (GitHub Actions **and** AppVeyor) stop complaining. Two independent root causes, fixed independently:

1. **GitHub Actions pip-install workflows** (Linux + macOS-14, all of 3.10/3.11/3.12): `pyarrow` is missing at runtime when the Neware nda backend calls `polars.DataFrame.to_pandas()`.
2. **AppVeyor**: the env solve fails (`numpy>=2.2.6` not found) because the base Miniconda on AppVeyor is 32-bit and numpy 2.x has no win-32 builds.

The GitHub Actions conda workflows already pass.

## Root cause #1 (pyarrow missing, GitHub Actions pip-install)

All failing pip-install runs share one error in `tests/test_neware.py::test_get_neware_from_nda`:

```
cellpy/readers/instruments/neware_nda.py:284: in _run_fastnda
    raw_data = raw_data.to_pandas()
...
polars/dataframe/frame.py:2668: ModuleNotFoundError
E       ModuleNotFoundError: No module named 'pyarrow'
```

Polars 1.40's `DataFrame.to_pandas()` requires `pyarrow` at runtime. `pyarrow` is declared in the conda env files but **not** in `setup.py`'s `install_requires`, so:

- conda workflows (`pytest_*.yml`) → install via [github_actions_environment.yml](github_actions_environment.yml) which has `pyarrow>=23` → pass.
- pip-install workflows (`pip-install-posix.yml`, `pip-install-macos-14.yml`) → only install what `setup.py` declares → no pyarrow → fail.
- `pip-install-win.yml` happens to pass because it only runs `tests/test_maccor.py`, skipping the neware test path.

Latest `master` CI confirms: 2 pip-install jobs `failure`, conda jobs `success`/`in_progress`.

## Root cause #2 (AppVeyor: 32-bit Miniconda)

From `local/dump/logs/appveyor/log.txt`:

```
platform : win-32
channel URLs : https://repo.anaconda.com/pkgs/main/win-32
                  https://repo.anaconda.com/pkgs/main/noarch
                  ...
conda env create -f github_actions_environment.yml python=3.10
Solving environment: ...working... failed
ResolvePackageNotFound:
  - numpy[version='>=2.2.6']
```

The AppVeyor image uses `MINICONDA: C:\Miniconda3`, which is the 32-bit install (conda 4.13.0, Python 3.7 base). conda-forge has not shipped `win-32` builds for years and numpy 2.x has no 32-bit Windows wheels, so the env file cannot be solved. Same failure on every Python version in the matrix (3.10, 3.11, 3.12, 3.13).

## Constraints

- KISS: smallest change that fixes the failures. No refactor of `neware_nda.py` or polars→pandas plumbing.
- Don't break the conda workflows (they're green; leave them alone).
- Keep `setup.py` as the source of truth for runtime deps; `pyproject.toml` only defines build-system + tooling here.
- Don't add `pyarrow` only inside the CI yamls — it would mask the real fact that the Neware nda backend needs it at runtime for any pip-only user.

## Approach

### Fix #1 — `pyarrow` in `install_requires`

Add `pyarrow` as a runtime requirement of the package so any install path (pip, conda, uv) gets it. Mirror the conda env's pin.

Single edit in [setup.py](setup.py), inside `install_requires`, alongside `polars`:

```python
"polars",
"pyarrow>=16",
```

(Conda env pins `pyarrow>=23`; we pin `>=16` for cellpy because polars 1.x added the arrow IPC dependency around pyarrow 16. Both are compatible.)

### Fix #2 — AppVeyor: switch to 64-bit Miniconda + trim matrix

Per your decision, fix AppVeyor **and** trim the matrix to one Python version as a smoke check (3.12; matches the GH Actions main target and is the python supported by the conda env).

Edits in [appveyor.yml](appveyor.yml):

```yaml
image: Visual Studio 2022

environment:
  MINICONDA: C:\Miniconda3-x64
  PYTHON_ARC: "64"
  matrix:
    - PYTHON_VERSION: "3.12"
```

Notes:

- `Visual Studio 2022` is AppVeyor's current image and ships a recent `C:\Miniconda3-x64`. Modern conda + win-64 channels means `numpy>=2.2.6` resolves.
- Dropping 3.10/3.11/3.13 from the matrix is intentional: AppVeyor becomes a Windows-conda smoke check; full-matrix coverage stays on GitHub Actions.
- Keep the rest of the file (install/test steps) as-is. The same `github_actions_environment.yml` is reused, so we don't double-maintain env definitions.

### Optional / deferred (not required to close the issue)

- `fastnda` is in the conda env (`pip:` section) but not in `setup.py`. The neware_nda backend currently goes through `USE_LOCAL_FASTNDA = prms._use_local_fastnda` which uses the bundled `cellpy/libs/local_fastnda/`, so tests don't need the PyPI `fastnda` package. Leave as-is.
- `sqlalchemy-access` already has a `platform_system=="windows"` marker — fine.
- The `test-win.yml` and `pytest_win.yml` workflows have `NOT WORKING` / `DID NOT WORK` in their names but are gated to `workflow_dispatch` only, so they don't affect CI status. Leave as-is.

## Files to touch

- [setup.py](setup.py) — add `"pyarrow>=16",` to `install_requires` (one line, next to `"polars"`).
- [appveyor.yml](appveyor.yml) — add `image: Visual Studio 2022`, change `MINICONDA` to `C:\Miniconda3-x64`, trim matrix to `3.12`.

## Test strategy

- Local sanity: `uv run pytest tests/test_neware.py::test_get_neware_from_nda` (env already has pyarrow) — confirms the test passes against the current code.
- CI verification on push:
  - Previously red GH Actions workflows must go green:
    - `Installing using pip on posix` (3.10, 3.11, 3.12)
    - `Installing using pip on Mac M chip` (3.10, 3.11, 3.12)
  - Conda workflows must stay green (no regression).
  - AppVeyor must produce one successful 3.12 build.
- No new test needed: existing `tests/test_neware.py::test_get_neware_from_nda` is the regression guard for fix #1, and the AppVeyor build outcome is the guard for fix #2.

## Open questions

None blocking.

- Pinning for pyarrow: `>=16` (permissive) vs `>=23` (mirror conda env). Default `>=16`.
- AppVeyor matrix: keeping just `3.12`. If you'd rather have a wider matrix later, we can add versions back once the 64-bit fix is confirmed working.
