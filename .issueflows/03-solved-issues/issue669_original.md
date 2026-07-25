# Issue #669: bad warnings in v1 collectors

Source: https://github.com/jepegit/cellpy/issues/669

## Original issue text

## Batch cycles collector

When running this in a Jupyter Lab notebook:

```python
cells_collected = collectors.BatchCyclesCollector(
    b,
    # cycles_to_plot=range(1, 11),  # plot the first 10 cycles, but collect all (e.g. for exports to csv)
    # collector_type="forth-and-forth",
)
```

We receive all these warnings (way too much):

```
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1370 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 217 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1832 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 423 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1940 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 356 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1232 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1415 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 141 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1816 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 429 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1945 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 337 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1103 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1387 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 282 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1832 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 414 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1779 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 271 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 768 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1419 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 144 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1822 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 491 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1954 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 273 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1349 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3024 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1035 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 987 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3106 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1086 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1084 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 454 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3399 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 465 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1770 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 444 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1697 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 110 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 149 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 126 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 394 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3255 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 389 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1685 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 380 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1517 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 117 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 501 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3157 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 402 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1759 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 402 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1607 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 130 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3040 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1120 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1019 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 2888 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 998 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1032 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3201 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1135 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1031 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 3289 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1189 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 1136 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
WARNING:root:interpolate_y_on_x_per_monotonic_segments: 149 segments exceeds max_segments=100; returning dataframe unchanged (likely noisy x-data).
```

Same problem when running the collector with `plot_type="fig_pr_cycle"`

## Batch ICA collector

Running for example `cells_collected = collectors.BatchICACollector(b, plot_type="fig_pr_cell")`

We get some warnings without error message:

```
WARNING:root:Error in dqdv_cycle - first half-cycle
WARNING:root: - error-message: ''
WARNING:root:Error in dqdv_cycle - last half-cycle
WARNING:root: - error-message: 'voltage is empty'
WARNING:root:Error in dqdv_cycle - first half-cycle
WARNING:root: - error-message: ''
WARNING:root:Error in dqdv_cycle - first half-cycle
WARNING:root: - error-message: ''
WARNING:root:Error in dqdv_cycle - first half-cycle
WARNING:root: - error-message: ''
WARNING:root:Error in dqdv_cycle - last half-cycle
WARNING:root: - error-message: 'voltage is empty'
WARNING:root:Error in dqdv_cycle - last half-cycle
WARNING:root: - error-message: 'voltage is empty'
```

## Comments (curated summary)

- **Clarifications / constraints**:
  - Also reproduces on `v2.0.0rc1` (not v1-only).

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-24._
