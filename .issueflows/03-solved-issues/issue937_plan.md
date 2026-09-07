# Issue #937 plan

## Goal

Drop `ipykernel` and `matplotlib` from the required pip install so a headless
app image does not pay ~90 MB for notebook/debug tooling it never uses.

## Constraints

- Do not change conda env files (conda-forge still ships the full stack).
- `uv sync` (dev group) must still install matplotlib so tests/CI keep working.
- Typed `OptionalDependencyError` naming the extra, same pattern as `legacy-files`.
- ### Prior art
  - `require_hdf5_support` in `cellpy/readers/cellpy_file/format.py` + `OptionalDependencyError`
  - `test_dependency_budget.py` manifest pins for extras moved out of required
  - `cellpy.plotting.collected` already `try/except ImportError` around matplotlib
  - `ipykernel` is never imported by library code; only listed in `[project.dependencies]`

## Approach

1. Remove `matplotlib` and `ipykernel` from `[project.dependencies]`.
2. Add extras `notebook = ["ipykernel", "ipython"]` and `plotting-mpl = ["matplotlib"]`.
3. Add both packages to the `all` extra; add `matplotlib` to the `dev` group (`ipykernel` is already there).
4. Add `require_matplotlib(context)` next to the matplotlib backend; call it from `get_backend("matplotlib")`.
5. Guard the four remaining module-scope matplotlib imports (`figures.py`, `batch_summary.py`, `plotutils.py`, `ocv_rlx.py`) with `try/except ImportError`.
6. Extend the dependency-budget tests; do not rewrite conda manifests.

## Files to touch

- `pyproject.toml` / `uv.lock` — extras + lock
- `cellpy/plotting/backends/mpl.py` — `require_matplotlib`
- `cellpy/plotting/backends/__init__.py` — call it from `get_backend`
- `cellpy/plotting/figures.py`, `cellpy/plotting/batch_summary.py`, `cellpy/utils/plotutils.py`, `cellpy/utils/ocv_rlx.py` — optional import
- `tests/test_dependency_budget.py` — pin the new extras
- `docs/getting_started/agents.md` — one install note
- `.issueflows/04-designs-and-guides/optional-plotting-notebook.md` — short decision

## Test strategy

`uv run pytest -m essential` plus the new dependency-budget tests. Full suite stays on CI.

## Open questions

None — extras names match the issue (`notebook`, `plotting-mpl`).
