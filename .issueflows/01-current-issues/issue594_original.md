# Issue #594: Nightly tier-3 matrix still excludes the plotting tests

Source: https://github.com/jepegit/cellpy/issues/594

## Original issue text

Follow-up from #593 (#567 Phase 0).

`ci.yml` (both required jobs) and `release.yml` now run the plotting tests with `MPLBACKEND=Agg`. `ci-scheduled.yml` still carries the old exclusion in five places:

```
--ignore=tests/test_plotutils_summary_plot.py
```

The stated reason — "plotutils summary plot needs a display" — is stale: the file selects the Agg backend itself and runs headless. That exclusion was hiding four real regressions on linux (see #593), and the nightly matrix is exactly where platform-specific plotting breakage would show up.

I left it alone because I could not verify macOS/Windows behaviour from a linux/Windows dev box, and a red nightly is noise if the cause is environmental rather than a real bug.

## Done when

- The `--ignore` is removed from `ci-scheduled.yml` and `MPLBACKEND: Agg` is set.
- One nightly run is observed across the matrix; anything that fails is either fixed or skipped with a *specific* reason (e.g. `skipif` on the platform), not a blanket file exclusion.

Note that tier-3 jobs may not install the `batch` extra, in which case the plotly/seaborn cases skip cleanly and the run is cheap.
