# Issue #669 plan

## Goal

Stop collector notebooks from flooding with per-cycle `WARNING:root` spam when
noisy voltage curves hit the max-segments fallback or half-cycle ICA fails —
keep one visible signal, demote repeats.

## Constraints

- Do not change interpolation / ICA numeric behaviour (still skip / empty arrays).
- Keep backport-friendly (`v1 and v2` / `v1x` labels): small logging change only.
- ### Prior art
  - `interpolate_y_on_x_per_monotonic_segments` in `cellpy/readers/data_structures.py` (emits the segment spam via bare `logging.warning`).
  - `_dqdv_cycle_impl` in `cellpy/ica.py` (per half-cycle `logging.warning`).
  - Module loggers already used elsewhere (`getLogger(__name__)`); deprecation `warn_once` is wrong tool (DeprecationWarning API).

## Approach

1. Switch both call sites to `logging.getLogger(__name__)`.
2. Process-level once-flag: first hit → `warning` (with note that further hits are DEBUG); later hits → `debug`.
3. ICA: collapse the two-line warning into one message; same once-per-process pattern for first/last half-cycle failures.

## Files to touch

- `cellpy/readers/data_structures.py` — module logger + once-flag for max_segments.
- `cellpy/ica.py` — module logger + once-flag for half-cycle failures.
- `tests/test_cell_readers.py` (or small new assertion) — assert at most one WARNING from repeated max_segments fallbacks.
- `.issueflows/01-current-issues/issue669_*` — tracking.

## Test strategy

- `uv run pytest tests/test_cell_readers.py::test_interpolate_y_on_x_per_monotonic_segments_max_segments_fallback -q` plus a new warn-once test.
- `MPLBACKEND=Agg uv run pytest -m essential` before close.

## Open questions

- None (yolo auto-confirm).
