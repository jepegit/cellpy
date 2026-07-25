# Issue #669 status

- [x] Done

## What's done

- Init + plan (yolo auto-confirm).
- Branch: `669-collector-warnings`.
- Warn-once (then DEBUG) for `interpolate_y_on_x_per_monotonic_segments` max_segments fallback.
- Warn-once (then DEBUG) for `_dqdv_cycle_impl` half-cycle failures; module loggers (no more `WARNING:root`).
- Essential test asserts a single WARNING across two fallback calls.
- HISTORY Unreleased bullet added.
- `MPLBACKEND=Agg uv run pytest -m essential` → 628 passed, 1 skipped.

## Remaining work

- None.
