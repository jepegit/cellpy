# Issue #863: No collect_dva: DVA is single-cell only, unlike summaries/cycles/ICA

Source: https://github.com/jepegit/cellpy/issues/863

## Original issue text

**cellpy version:** 2.1.2a3

## Summary

`cellpy.collect` exposes `collect_summaries`, `collect_cycles` and `collect_ica`, each returning a `Collection` that spans a batch of cells and plots through the collected path. **DVA has no equivalent** — `dva_plot(cell, ...)` takes a single cell, so differential voltage is the one analysis family that cannot be compared across cells.

```python
>>> import cellpy.collect as C
>>> [hasattr(C, f"collect_{k}") for k in ("summaries", "cycles", "ica", "dva")]
[True, True, True, False]
```

The `dva` plot family *is* registered (`registry.get("dva")` → `extras={'entry_point': 'dva_plot', 'kind': 'dva'}`), which makes the gap easy to trip over: the family shows up in the registry alongside `ica`, but there is no collector behind it.

## Why it matters for apps

We just added a DVA view to [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) next to the existing ICA view. ICA gets the full collected treatment — multiple cells, grouping, group-averaging, the whole `Collection` API. DVA had to be wired as a one-cell-at-a-time special case straight onto `dva_plot`, which means:

- no multi-cell DVA comparison, though that is exactly what you want when screening electrode formulations;
- a second code path in the app, with its own export (`dva_plot(return_data=True)` returns pandas, while collections are polars);
- the two sibling views behave differently for no reason the user can see.

`ica.dvdq` already produces the tidy per-cell frame (`cycle`, `direction`, `capacity`, `voltage`, `dvdq`), so the missing piece looks like the collector wrapper rather than the analysis.

## Wish

A `collect_dva(batch, options=IcaOptions(...))` returning a `Collection` the same way `collect_ica` does — same `Collection.plot()` entry, same grouping/spread behaviour, same polars frame for export. That would let apps treat ICA and DVA as the two halves of one feature instead of two unrelated ones.

Happy to help if useful.
