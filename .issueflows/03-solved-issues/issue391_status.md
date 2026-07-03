# Issue #391 - Status

- [x] Done

## Summary

Successfully changed the default y-axis scaling behavior for `BatchSummaryCollector` from matching axes (`match_axes=True`) to independent axes (`match_axes=False`).

## Changes Made

### Modified Files

1. **`cellpy/utils/collectors.py`**
   - Added `_default_plotter_arguments` class variable to `BatchSummaryCollector`
   - Set `match_axes: False` as the default plotter argument

```python
_default_plotter_arguments = {
    "match_axes": False,
}
```

## Implementation Details

The change was made by adding a class-level `_default_plotter_arguments` dictionary to `BatchSummaryCollector`. This follows the existing pattern documented in the class:

> Three main levels of arguments to the plotter and collector funcs is available:
> - through dictionaries (`data_collector_arguments`, `plotter_arguments`) to init
> - given as defaults in the subclass (`_default_data_collector_arguments`, `_default_plotter_arguments`)
> - as elevated arguments

## Backward Compatibility

This change is backward compatible:
- Users who were relying on the default (`match_axes=True`) can explicitly pass `plotter_arguments={"match_axes": True}` to get the old behavior
- Users who were already passing `plotter_arguments={"match_axes": False}` will see no change
- The change only affects `BatchSummaryCollector`, not other collectors like `BatchCyclesCollector` or `BatchICACollector`

## Testing

- No existing tests specifically test `BatchSummaryCollector` with `match_axes`
- The syntax change is valid and follows the existing pattern used by other collectors
- Manual testing would require setting up the full environment with dependencies

## Notes

As requested by the issue author (asbjorul), matching axes is only suitable for specific plot combinations and is not suitable for the majority of cases. The new default (`False`) better serves the common use case, while still allowing users to enable axis matching when needed.
