# Issue #867 — status

- [x] Done

## What was done

`raw_plot` is no longer unbounded. Both knobs from the issue were implemented,
as confirmed up front in the cycle's consolidated confirm.

- `RawPrepareConfig` gained `cycles` and `max_points`; both default to `None`,
  so existing behaviour is unchanged.
- `prepare()` filters on the raw cycle-index column **before** `.copy()`, so a
  cycle subset no longer pays for copying the whole frame.
- New `decimate()` helper in `cellpy/plotting/prepare/raw.py`: positional
  buckets over the time-ordered frame, keeping each y column's per-bucket argmin
  and argmax plus the first and last row. The bucket count is scaled by the
  number of traces (`max_points // (2 * n_y)`) so the union lands near the
  budget rather than overshooting by the trace count.
- `raw_plot` exposes `cycles=` / `max_points=` explicitly, so they are not
  swallowed by `**kwargs` and forwarded to the backend.

## Measured effect (bundled `example_data.cellpy_file()`, 155 754 raw rows)

| call | figure JSON |
|---|---|
| `plot_type="full"` (unchanged default) | 18.06 MiB |
| `max_points=5000` | 0.33 MiB |
| `max_points=2000` | 0.17 MiB |
| `cycles=[1, 2]` | 0.29 MiB |

## Tests

Four new `essential` tests in `tests/test_raw_cycle_info_prepare.py`: cycle
selection (list and bare int), thinning within budget, endpoint and per-trace
min/max preservation (the property that distinguishes bucketed decimation from
striding), the no-op path when the frame is already small, and the public
signature. Full `uv run pytest -m essential` gate green.

## Remaining work

None.
