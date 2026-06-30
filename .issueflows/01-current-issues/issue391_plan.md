# Issue #391 - Plan: Change BatchSummaryCollector default y-axis scaling

## Problem Analysis

The `BatchSummaryCollector` currently defaults to matching y-axes across subplots. This happens because:
1. `BatchSummaryCollector` uses `summary_plotter` as its plotter function
2. `summary_plotter` calls `_cycles_plotter` passing through `**kwargs`
3. `_cycles_plotter` has `match_axes=True` as its default parameter
4. `BatchSummaryCollector` does not override this default

The current default (`match_axes=True`) is only suitable for specific plot combinations, not the majority of use cases.

## Proposed Solution

Add a `_default_plotter_arguments` class variable to `BatchSummaryCollector` with `match_axes` set to `False`:

```python
class BatchSummaryCollector(BatchCollector):
    _default_data_collector_arguments = {
        "columns": ["charge_capacity_gravimetric"],
    }
    
    _default_plotter_arguments = {
        "match_axes": False,
    }
```

This approach:
- Only affects `BatchSummaryCollector`, not other collectors (e.g., `BatchCyclesCollector`, `BatchICACollector`)
- Follows the existing pattern documented in the class comments (three levels of arguments)
- Users can still override by passing `plotter_arguments={"match_axes": True}` if needed
- Is backward compatible (users who explicitly set `match_axes=False` will see no change)

## Files to Modify

1. `cellpy/utils/collectors.py` - Add `_default_plotter_arguments` to `BatchSummaryCollector` class

## Testing Strategy

1. Check existing tests for `BatchSummaryCollector` to ensure they pass
2. Manually verify that the default behavior changes (axes are no longer matched)
3. Verify that explicit override still works: `plotter_arguments={"match_axes": True}`

## Out of Scope

- Changing defaults for other collectors (`BatchCyclesCollector`, `BatchICACollector`)
- Changing the `_cycles_plotter` function signature itself
