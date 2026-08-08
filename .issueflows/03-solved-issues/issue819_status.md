# Status: #819 — instrument wins over `.h5`/`.hdf5` auto-pick

- [x] Done

## What's done

- `get()` auto-pick: set `instrument=` skips native pick for `.h5`/`.hdf5`; `.cellpy`/`.cpy` still auto-pick; dropped `arbin_sql_h5` allow-list.
- Docstring + `basic_usage.md` + `agents.md` + `AGENTS.md`.
- Regression `test_get_h5_instrument_skips_native_autopick` (essential); registry row; `test_arbin_sql_h5` + `pytest -m essential` green.
- HISTORY `[Unreleased]` bullet.

## Remaining work

- None (close: commit / push / PR).
