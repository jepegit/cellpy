# Status for issue #360: CI pipeline problems

- [ ] Done

## What landed

- **[setup.py](../../setup.py)** — added `"pyarrow>=16",` to `install_requires` right after `"polars"`. This fixes the GitHub Actions pip-install workflows that were failing on `tests/test_neware.py::test_get_neware_from_nda` with `ModuleNotFoundError: No module named 'pyarrow'` (polars 1.40's `DataFrame.to_pandas()` requires pyarrow).
- **[appveyor.yml](../../appveyor.yml)** — switched to `image: Visual Studio 2022`, changed `MINICONDA: C:\Miniconda3` → `C:\Miniconda3-x64`, and trimmed the matrix to a single `PYTHON_VERSION: "3.12"`. The previous 32-bit Miniconda couldn't solve `numpy>=2.2.6` (no win-32 wheels; conda-forge dropped `win-32` years ago). AppVeyor is now a Windows-conda smoke check; the full matrix lives on GitHub Actions.

## Verification

- Local: `pytest tests/test_neware.py::test_get_neware_from_nda -v` → **PASSED** in `cellpy_dev_312` conda env (which has pyarrow), confirming the test code itself is unchanged and works against the current `neware_nda.py`.
- CI verification (on push) — what to look for:
  - GH Actions `Installing using pip on posix` (3.10/3.11/3.12) flips red → green.
  - GH Actions `Installing using pip on Mac M chip` (3.10/3.11/3.12) flips red → green.
  - GH Actions conda workflows (`Run pytest on linux/macos/macos-M (conda)`) stay green (no regression).
  - AppVeyor produces one successful 3.12 build.

## What remains

- Push the branch and watch the CI run; that's the actual verification.
- If AppVeyor reports that `C:\Miniconda3-x64` doesn't exist on the `Visual Studio 2022` image, fall back to a versioned path (e.g. `C:\Miniconda38-x64`, `C:\Miniconda39-x64`, or whatever AppVeyor currently ships).

## Out of scope (intentional)

- Refactoring the polars→pandas path in [`cellpy/readers/instruments/neware_nda.py`](../../cellpy/readers/instruments/neware_nda.py) (the dep declaration is the right level).
- Adding `fastnda` to `install_requires` — tests go through the bundled `cellpy/libs/local_fastnda/` via `USE_LOCAL_FASTNDA`, so the PyPI package isn't needed.
- The `*-NOT WORKING*` workflows (`test-win.yml`, `pytest_win.yml`) — gated to `workflow_dispatch`, no effect on CI status.
