# Issue #560 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-22): Phase C stacked PRs C1→C2→C3.
- Prior landings on `master` (not this branch): declarations, oracle, loader
  ports, Phase B opt-in flip (#621).
- **C1** Harden flip:
  - `_aux_map.py` + `arbin_res.declarations()` fill `aux_map` (wide-aux survives)
  - Oracle asserts datapoint preservation + aux value survival
  - `batmo_bdf.parse()` runs decode (hours→seconds etc.); parity green
  - `arbin_sql_h5` keep-all-rows encoded in oracle
- **C2** `Reader.use_harmonized_raw` defaults to `True` (config/prms/docs/tests)
- **C3** Try-harmonize-first for single-file raw (skip redundant `raw_to_native`);
  conformance kit check 7 (`check_reset_granularity`) wired into `check_loader`
- Essential suite: 525 passed (ignore pre-existing `test_arbin_variants_two_stage`
  `pyodbc` collection error on this host)

## Remaining work

- Paste release-note bullets into #572 during `/iflow-close`
- Multi-file native merge remains a follow-up (out of scope)

## Release-note bullets for #572 (draft)

- Single-file raw loads default to `harmonize(parse())` (`Reader.use_harmonized_raw=True`); set `False` for the legacy rename fallback.
- Arbin wide-aux columns keep values under `aux_<quantity>_<name>` (e.g. `aux_0_u_C` → `aux_temperature_0`).
- Vendor `data_point` / `datapoint_num` is preserved (not re-minted as `0..n-1`).
- `arbin_sql_h5` keeps all 47 loader-stage rows through load+summary (the old
  summary-side collapse to 34 is gone on the default harmonized path).
