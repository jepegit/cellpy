# Issue #867 — raw_plot has no way to limit points (or select cycles)

**Source:** https://github.com/jepegit/cellpy/issues/867
**Labels:** yolo · **Milestone:** v.2.1.2 · **cellpy version:** 2.1.2a4

## Summary

`raw_plot` always plots the entire raw frame. `prepare_raw` does
`raw = c.data.raw.copy()` with no thinning and no cycle filter, and the public
entry point exposes neither. On the bundled `cellpy_file()` example (155 754 raw
rows) the resulting Plotly figure JSON is 7.0–18.1 MiB depending on `plot_type`
(`full` → 18.1 MiB). A real multi-week test is far larger.

Every other family has a natural bound — `summary_plot` is per cycle,
`cycles_plot` / `ica_plot` / `dva_plot` take `cycles=`. `raw_plot` is the only
one unbounded by construction.

## Why it matters for apps

In cellpy-simple-gui figures go over HTTP into a browser; an 18 MiB figure stalls
the tab. The app currently thins traces itself after `raw_plot` returns (every
Nth point: 18.5 MiB → 482 KiB), which means every app reinvents the same
post-processing, the cost of copying/converting the full frame is paid anyway,
and naive striding drops spikes that min/max-per-bucket decimation would keep.

## Wish (from the issue)

- `raw_plot(..., max_points=N)` — thin to roughly N points per trace, ideally
  min/max per bucket rather than plain striding;
- `raw_plot(..., cycles=[...])` — the same bound the other families already have;
- or plumb both through `RawPrepareConfig` so the reduction happens before the copy.
