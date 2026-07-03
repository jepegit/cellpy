# Issue #391: BatchSummaryCollector default y-axis scaling

Source: https://github.com/jepegit/cellpy/issues/391

## Original issue text

The BatchSummaryCollector defaults to matching the y-axes of the generated subplots. This can be disabled by setting the argument `plotter_arguments={"match_axes": False}`; however, since this matching is only suitable for specific plot combinations, while it is not suitable for the majority of cases, I propose to have this setting default to False.

## Issue metadata

- Author: Asbjørn Ulvestad (asbjorul)
- Created: 2026-06-30
- State: OPEN
