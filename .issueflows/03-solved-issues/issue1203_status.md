# Issue #1203 — status

- [x] Done

## What's done

- Plan accepted.
- `test_ica_collector_skips_an_empty_cycle_frame` locks public
  `ica_collector` for `cycles=(2, 3, 4)` and for omitted `cycles`. One
  empty cycle frame warns and is skipped; the good cell stays. Smoothing
  is off in the fixture so the synthetic line still yields a curve.
- No production change. The raise was already fixed in v2.1.5.post9
  (#1154 / #1152).
- Registry row added.
- GitHub comment on #1203: no cell limit; post8 aborts the batch; post9+
  skips; conda-forge is still post8.

## Remaining work

- None in this repo. The conda-forge feedstock is out of scope.
