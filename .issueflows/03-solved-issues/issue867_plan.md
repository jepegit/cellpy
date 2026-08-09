# Issue #867 — plan

## Goal

Give `raw_plot` a bound on how much data it emits: both `cycles=` (the selector
the other families already have) and `max_points=` (min/max-per-bucket
decimation), plumbed through `RawPrepareConfig` so the reduction happens on the
prepare side rather than in every downstream app.

Direction confirmed up front in the cycle confirm: implement **both** knobs.

## Approach

`cellpy/plotting/prepare/raw.py`

- `RawPrepareConfig` gains `cycles: Optional[Any] = None` and
  `max_points: Optional[int] = None`.
- `prepare()` filters on the raw cycle-index column **before** the copy, so a
  cycle subset never pays for copying the whole frame.
- After the x column is derived (decimation must see the plotted columns), thin
  with min/max per bucket:
  - buckets are positional over the time-ordered frame;
  - `n_buckets = max_points // (2 * n_y)` so the union of per-column argmin /
    argmax rows lands near `max_points` rather than overshooting by a factor of
    the trace count;
  - the union keeps every column's extremes — spikes survive, unlike striding;
  - first and last rows are always kept so the x range does not shrink.
- No new `FigureSpec.extras` keys → the figure-spec snapshot is untouched.

`cellpy/utils/plotutils.py`

- `raw_plot` gains explicit `cycles=` / `max_points=` parameters (explicit, so
  they are not swallowed into `**kwargs` and forwarded to the backend) and
  passes them through to the config. Docstring updated.

Defaults stay `None` on both, so current behaviour is unchanged.

## Files to touch

- `cellpy/plotting/prepare/raw.py`
- `cellpy/utils/plotutils.py`
- `tests/test_raw_cycle_info_prepare.py`
- `HISTORY.md` (changelog bullet at close)

## Test strategy

New `essential` tests in `tests/test_raw_cycle_info_prepare.py`:

- `cycles=` restricts the prepared frame to the requested cycle numbers;
- `max_points=` cuts the row count to roughly the requested budget;
- decimation preserves the global min and max of a y column and both endpoints
  (the property that separates min/max bucketing from striding);
- both knobs reach `raw_plot` from the public signature and are not forwarded to
  the backend as stray kwargs.

Then the full `uv run pytest -m essential` gate.
