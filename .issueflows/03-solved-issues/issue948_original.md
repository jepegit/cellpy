# Issue #948: Problems with custom_group_labels in summary_collector

Source: https://github.com/jepegit/cellpy/issues/948

## Original issue text

Running this:
```
cap_summaries = summary_collector(
    b,
    #max_cycle=50,
    columns=[
        "charge_capacity_gravimetric",
        "discharge_capacity_gravimetric",
        "coulombic_efficiency",
    ],
    group_it=True,
    custom_group_labels={
        1: "run-14",
        2: "run-15",
    },
)

cap_summaries.plot(height=800)
```

produces expected result with legend labels saying run-14 and run-15, while, if I do:

`cap_summaries.plot(height=800, spread=True)`

changing the the last line to include the standard deviation, the group labels go back to 1 and 2 (The custom_group_labels are still set to run-14 and run-15.) (Showing the standard deviation works)

## Comments (curated summary)

- **Additional tasks**:
  - Check that `spread=True` still accepts the supported per-panel y-limits (`y_ranges=` / `share_y=False`). The thread's `fig.update_yaxes(..., row=N)` workaround is not the public API and must not become the fix.
- **Clarifications / constraints**:
  - Std bands themselves work; only the legend text regresses.
  - Manual `row=` y-axis edits look wrong on spread because `spread_plot` builds `make_subplots` (row 1 = top) while the workaround assumed the non-spread facet row numbering.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @inger-emma on 2026-09-01._
