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
  - Fix the `maccor_txt_one` `Watt-hr` collision before switchover: drop the mistaken `power_txt: "Watt-hr"` mapping so derivation can yield native `cumulative_charge_energy` (see comment thread).
  - Implement per-loader `parse()` for remaining loaders (`arbin_res`, `neware_txt`, `pec_csv`, `custom`, then tier-2); only the `maccor_txt_native` pilot exists today.
  - Port still-missing post-processors needed for switchover parity: `split_capacity`, `split_current`, `set_cycle_number_not_zero`, `remove_last_if_bad`, `update_headers_with_units` (loader plan §2.7).
  - Decide fate of undeclared vendor columns before `harmonize()` becomes the load path (declare / passthrough / deliberate drop + release notes).
  - Land **cellpy-core#139** (energy legacy→native mapping), release + re-pin, then do the ingestion switch.
  - Settle `date_time` parsing / `epoch_time_utc` production before flag day (metadata arc; overlaps #562/#563).
  - Add conformance kit check 7 (reset granularity) once several loaders are ported (deferred from #210).
- **Clarifications / constraints**:
  - Part 1 already landed in #583; there is **no `LegacyLoaderAdapter` class** to delete. The transitional mechanism is ingestion-time `to_native()` (around `cellreader.py:1368`); retiring it means routing `load()` through `harmonize(parse(...))` for every loader in one shared-path PR with full golden parity + benchmarks.
  - `arbin_res` needs ODBC — CI can only check against the committed fixture (loader plan risk table).
  - Value-parity oracle lives on branch `issue-560-value-parity-oracle` (`tests/test_loader_port_parity.py`); as of 2026-07-20, `neware_txt` has exact parity on 14 comparable columns; `maccor_txt` is green except columns owned by unported post-processors.
  - Ingestion-path rule from the oracle work: a step that can destroy data must not do it quietly (duration-cast / #580 shape).
  - `set_cycle_number_not_zero` needs an explicit 0- vs 1-based cycles product decision, not only a hook.
  - Oracle-found bugs (`PER_STEP` granularity; duration→null casts) are flag-day regressions caught before shipping — not user-facing on current legacy ingestion.
- **Superseded / retracted**:
  - Issue body wording "Delete `LegacyLoaderAdapter`" — superseded by the Part-1 status: retire `to_native()` instead.
  - Earlier claim that neware capacities on 2.0.0a5 were already wrong due to bug (1) — explicitly retracted; legacy ingestion still cumulates correctly.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 3, last comment by @jepegit on 2026-07-20._

