# Plan — issue #458 (Stage 1.15)

1. **`cellpy/readers/cellpy_file/translate.py`** — all header knowledge comes
   from `cellpycore.legacy.mapping` (core#116 / cellpycore 0.2.0); nothing is
   declared locally:
   - frame-level: `raw/steps/summary_to_native` and `_to_legacy` (summary
     renames include the `{col}_{mode}` specific variants via
     `mapping.expand_specific_columns`); renames touch only columns present.
   - Data-level: `to_native(data)` injects `test_id = 0` where absent (native
     composite group keys, D3); `to_legacy(data)` strips it again from
     steps/summary so v8 → native → v8 is exact.
   - `classify_legacy_columns(columns, family)` — the totality guard:
     mapped / legacy-only / unknown.
2. **Dormant scope:** lossless renames only. `date_time` → `epoch_time_utc`
   derivation and the drop-and-recompute policy for summary cruft belong to
   the Phase-3 importer, not this layer — round trips here are exact by
   construction.
3. **Quirks the totality guard surfaced (now documented classifications):**
   the bridge's `index`-column sort quirk on steps (native-headers D4), and
   `shifted_*_{gravimetric,areal}` summary variants in old files (legacy
   `specific_columns` included the shifted capacities; the base is
   legacy-only, so the variants are too).
4. **Tests** (`tests/test_translate.py`): v8 golden round-trip
   (`assert_frame_equal`, exact columns/order/dtypes), totality (unknown
   column fails), #434 `assert_value_parity` green per family through the
   translation, specific-variant two-way translation, family validation.
