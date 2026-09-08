# Instrument availability in `list_instruments` (#938)

## Context

Missing system tools (`mdb-export` / mdbtools, `libodbc.so.2`) used to fail
silently: Arbin `.res` load re-raised a bare `FileNotFoundError`, and
`list_instruments()` omitted loaders whose `create()` raised (SQL loaders
without unixODBC).

## Decision

- Missing `mdb-export` (posix PATH command only) raises
  `OptionalDependencyError` naming apt/brew. Windows bundled exe paths are
  unchanged.
- `list_instruments()` walks **registered** ids. Import/create failures still
  emit a row with `available=False` and `reason=<exception text>`. Expected
  skips (`local_instrument`, missing `DataLoader`) stay omitted.
- Additive keys only: `available` / `reason`. Existing keys stay.
- If `arbin_res` creates but posix `mdb-export` is missing, that row is
  `available=False` with the same mdbtools reason.
- Stay quiet (#786): failures stay at DEBUG.

## Alternatives

- New `CellpyDependencyError`: rejected — extra public type for one caller.
- Pip extras for mdbtools/unixodbc: rejected — system packages.
- Mix `InstrumentFactory` with entry-point `registry`: out of scope.
- Fix `examplesdir` cwd trap: deferred (not a missing tool; #960 is a
  different bug).
