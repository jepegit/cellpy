# Issue 307 – Status

**Issue:** Interpolation in get_cap() removes steps when there are multiple charge or discharge steps (e.g. taper). Artefacts at charge/discharge transition. BatchCyclesCollector uses interpolation by default.

## Done

- [x] **Root cause:** `get_cap(..., interpolated=True)` called `interpolate_y_on_x()` on the full charge and full discharge curve. With multiple steps (CC + taper), the x-axis (e.g. voltage) is not strictly monotonic (constant V during taper), so `scipy.interp1d` either failed or produced wrong/merged behaviour and steps were lost.
- [x] **Fix:** Added `interpolate_y_on_x_per_monotonic_segments()` in `cellpy/readers/core.py` that:
  - Splits the curve into segments where x is strictly monotonic (segment starts when monotonicity breaks).
  - For strictly monotonic segments: interpolates with existing `interpolate_y_on_x()`.
  - For constant-x segments (e.g. taper): keeps the segment as-is (no interpolation).
  - Concatenates all segments to preserve steps.
- [x] **Integration:** `get_cap()` in `cellpy/readers/cellreader.py` now uses `interpolate_y_on_x_per_monotonic_segments()` instead of `interpolate_y_on_x()` when `interpolated=True` (for both first and last step processing).
- [x] **Test:** Added `test_interpolate_y_on_x_per_monotonic_segments_preserves_taper_steps` in `tests/test_cell_readers.py` (CC + taper synthetic curve).
- [x] **Regression:** `test_get_capacity`, `test_get_cap_usteps` pass.

## Status

- [x] Done

## Files touched

- `cellpy/readers/core.py`: new `interpolate_y_on_x_per_monotonic_segments()`
- `cellpy/readers/cellreader.py`: `get_cap()` uses it when `interpolated=True`
- `tests/test_cell_readers.py`: new unit test for per-segment interpolation
