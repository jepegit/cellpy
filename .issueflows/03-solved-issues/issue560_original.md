# Issue #560: Stage 3.3: port tier-1/2 loaders to declarations; retire LegacyLoaderAdapter

Source: https://github.com/jepegit/cellpy/issues/560

## Original issue text

## Goal

Port the tier-1 and tier-2 instrument loaders to the declaration + `harmonize()` design
and delete `LegacyLoaderAdapter`.

## Why

The adapter is the last place where legacy-dialect frames are manufactured on the
ingestion path. While it lives, every loader has two possible shapes and the parity
oracle has to cover both. Removing it is what makes "translation happens once, at I/O
boundaries" actually true.

Plan: `architecture-plan/cellpy2-loader-port-and-extraction-plan.md` (tiers);
architecture plan §6 row 3.5.

## Scope

- [ ] Tier 1: `arbin_res`, `neware_txt`, `neware_xlsx`, `pec_csv` (confirm the tier list
      against the loader plan before starting).
- [ ] Tier 2: the arbin_sql family, `custom`, `local_instrument`.
- [ ] Each ported loader ships a committed vendor sample + expected harmonized parquet
      (script-regenerated, convention F8) and passes `check_loader`.
- [ ] Delete `LegacyLoaderAdapter` and the ingestion-time `to_native()` call once no
      loader needs it.

## Acceptance

- Every tier-1/2 loader passes the conformance test-kit including the
  reset-granularity property test.
- `LegacyLoaderAdapter` no longer exists in the tree.
- Golden/parity suites green; benchmarks show no regression on the load path.

## Depends on

Loader `harmonize()` framework + pilot.

## Comments (curated summary)

- **Additional tasks**:
  - Fix `maccor_txt_one` `Watt-hr` mapping: drop the erroneous `power_txt: "Watt-hr"` so derivation yields native `cumulative_charge_energy` (before switchover).
  - Decide undeclared vendor columns that `harmonize()` drops (declare, passthrough, or deliberate drop + release notes).
  - Port remaining per-loader `parse()` implementations (tier-1: `arbin_res`, `neware_txt`, `pec_csv`, `custom`; then tier-2).
  - Land conformance kit check 7 (reset granularity) once several ported loaders exist.
  - Port or decide remaining post-processors: `split_capacity`, `split_current`, `set_cycle_number_not_zero`, `remove_last_if_bad`, `update_headers_with_units`.
  - Settle `date_time` / `epoch_time_utc` before flag-day (metadata arc #562/#563).
- **Clarifications / constraints**:
  - There is no `LegacyLoaderAdapter` class; the transitional mechanism is shared `to_native()` in `cellreader` — switchover is all loaders at once via `harmonize(parse(...))`.
  - Prefer cellpy-core#139 energy-column mapping released and re-pinned before switchover.
  - Ingestion-path rule: a step that can destroy data must not do so quietly (same shape as #580).
  - Value-parity oracle (`tests/test_loader_port_parity.py`) is the switchover gate; name-only declaration checks are insufficient.
  - Oracle-found bugs were pre-flag-day only (`harmonize` limited to the maccor pilot); not user-facing on 2.0.0a5 load path.
- **Superseded / retracted**:
  - Earlier claim that neware capacities on 2.0.0a5 were affected by the PER_STEP bug — retracted in the edited comment.
  - Literal "delete `LegacyLoaderAdapter`" acceptance — superseded by retiring the shared `to_native()` ingestion path.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 3, last comment by @jepegit on 2026-07-20._

