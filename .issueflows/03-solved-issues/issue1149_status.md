# Issue #1149 status

- [x] Done

## What's done

- Captured the issue. Plan accepted: `get_raw_units()` follows fastnda column suffixes.
- `neware_nda.get_raw_units()` now reads those suffixes (`mA`, `mAh`, `mWh`, `mohm`, `V`). `mass` stays `g`. `nominal_capacity` falls back to `mAh/g`.
- Essential declaration tests passed. Local ndax load: `|current|` max 65.7, discharge capacity max ~934, `raw_units` `mA` / `mAh`.

## Remaining work

- None. Essential suite: 988 passed, 74 skipped.
