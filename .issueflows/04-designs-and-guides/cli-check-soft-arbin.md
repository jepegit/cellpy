# Soft checks in `cellpy info --check` (#1111)

## Context

Scheduled Windows pip CI failed on `cellpy info --check` because the
Arbin `.res` ODBC probe reported one failure and the CLI exited 1. Missing
Access ODBC / mdbtools is optional capability (#938), not a broken install.

## Decision

- `_CheckOutcome.required` (default `True`): soft misses use `ui.warn` and
  do not increment the exit-code failure count.
- `_check_import_pyodbc` miss paths return `required=False`.
- Imports and configuration stay required (hard fail → exit 1).
- Summary still shows `N of M checks passed` counting soft misses against
  `N`; process exit follows hard failures only.

## Alternatives

- CI `|| true` / `continue-on-error`: rejected — scripts and CI must share
  one meaning.
- Install Access ODBC on Windows runners: out of scope / impractical.
