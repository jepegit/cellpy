# Issue #938 status

- [x] Done

## What's done

- `require_mdb_export` / `mdb_export_unavailable_reason` in `arbin_res.py`;
  posix `.res` load raises `OptionalDependencyError` naming mdbtools.
- `list_instruments()` walks registered ids; failed creates emit
  `available=False` + `reason`; expected skips stay omitted; quiet (#786).
- `arbin_res` listed unavailable when posix `mdb-export` is missing.
- Tests (essential), `agents.md`, design note `instrument-availability.md`.
- `examplesdir` deferred (not a missing tool).

## Remaining work

- None.
