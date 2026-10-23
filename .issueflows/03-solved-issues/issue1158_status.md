# Issue #1158 — status

- [x] Done

## What's done

- Plan accepted 2026-10-23 ("Accept").
- Docstring and `docs/guides/plotting.md` state the real return value. The return contract stays: `None` unless `get_axes=True`. Plotly then returns the figure. Matplotlib returns an axes tuple.
- `loader.ipynb` is not in this repo. The cookiecutter notebook does not mention `get_axes`.
- Verification: `test_cycle_info_plot_backend_matplotlib` and `test_cycle_info_plot_plotly_returns_none_unless_get_axes` passed. `pytest -m essential` 1077 passed, 1 skipped. Two filefinder failures (`test_find_by_project_cellpy_range`, `test_find_by_project_otherpath_local`) search `*.h5` because `~/.cellpy_prms_ubuntu.conf` sets `cellpy_file_extension: h5`. Those two pass with that file moved aside. Both new and updated tests are essential. No version bump.
- PR: https://github.com/jepegit/cellpy/pull/1169

## Remaining work

- None.
