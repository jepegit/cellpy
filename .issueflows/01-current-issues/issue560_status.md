# Issue #560 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-22): Phase C stacked PRs C1→C2→C3.
- Prior landings on `master` (not this branch): declarations, oracle, loader
  ports, Phase B opt-in flip (#621).
- **C1** Harden flip (default still off):
  - `_aux_map.py` + `arbin_res.declarations()` fill `aux_map` (wide-aux survives)
  - Oracle asserts datapoint preservation + aux value survival
  - `batmo_bdf.parse()` runs decode (hours→seconds etc.); parity green
  - `arbin_sql_h5` keep-47-at-loader-stage encoded in oracle
  - Flip test covers arbin aux fixture; essential suite green (modulo
    pre-existing `pyodbc` collection issue on this host)

## Remaining work

- **C2** Default `use_harmonized_raw=True` + full suite / release-note bullets
- **C3** Try-harmonize-first dual-path cleanup + conformance check 7
