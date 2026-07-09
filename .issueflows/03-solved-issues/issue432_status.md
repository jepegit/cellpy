# Issue #432 — Status

- [x] Done

## What's done

- Branch `432-per-loader-golden-snapshots` from current `master`.
- `tests/loader_golden_support.py` — tier-1 loader spec registry, snapshot load/export, raw
  frame normalization, JSON-safe meta capture.
- `dev/regenerate_goldens.py` — registered suites `loader_arbin_res`, `loader_maccor_txt`,
  `loader_neware_txt`, `loader_pec_csv`, `loader_custom`.
- Committed golden artifacts under `tests/data/goldens/loader_*/` (`raw.parquet`,
  `raw_units.json`, `meta.json`, `metrics.json`).
- `tests/test_loader_goldens.py` — 20 parametrized `@pytest.mark.essential` tests; skip when
  source file, instrument file, or loader backend unavailable.
- `tests/data/goldens/README.md` — suite index updated.
- Determinism: `uv run python dev/regenerate_goldens.py --verify loader_*` passes.
- Tests: `tests/test_loader_goldens.py` + `tests/test_goldens.py` essential — 22 passed.

## Notes

- Tier-2 loaders (`arbin_sql*`, `neware_xlsx`, `neware_nda`) deferred; add when needed for
  Stage 0 exit or loader port Step 3+.
- Full suite has 2 pre-existing failures on `master` in
  `test_cellpy_file_roundtrip.py::test_legacy_v4_v5_currently_raise_typeerror_on_meta_extract`
  (stale xfail-style pin; unrelated to this issue).
