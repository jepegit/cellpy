# Issue #560 — status

- [x] Done

## What's done

- Plan accepted (2026-07-22): Phase C stacked PRs C1→C2→C3.
- Prior landings on `master`: declarations, oracle, loader ports, Phase B
  opt-in flip (#621).
- **C1** Harden flip: `_aux_map` / arbin aux, batmo decode in `parse()`,
  oracle covers aux/datapoint/h5 rows.
- **C2** `Reader.use_harmonized_raw` defaults to `True`.
- **C3** Try-harmonize-first for single-file raw; conformance check 7 in
  `check_loader`.
- Design note: `.issueflows/04-designs-and-guides/harmonized-raw-default.md`.
- `HISTORY.md` promoted to `[2.0.0a6] - 2026-07-22`.
- Essential suite: 525 passed (ignore pre-existing `test_arbin_variants_two_stage`
  `pyodbc` collection error on this host).

## Planned release tag

- **`v2.0.0a6`** (from `v2.0.0a5` + alpha bump) — create after merge on `master`
  via `/iflow-cleanup` (do not tag this issue branch).

## Remaining work

- None for #560. Multi-file native merge is a follow-up.
- Paste release-note bullets into #572 when convenient (also in HISTORY).

## Release-note bullets for #572

- Single-file raw loads default to `harmonize(parse())` (`Reader.use_harmonized_raw=True`); set `False` for the legacy rename fallback.
- Arbin wide-aux columns keep values under `aux_<quantity>_<name>` (e.g. `aux_0_u_C` → `aux_temperature_0`).
- Vendor `data_point` / `datapoint_num` is preserved (not re-minted as `0..n-1`).
- `arbin_sql_h5` keeps all 47 loader-stage rows through load+summary.
