# Plan for issue #432: Per-loader golden snapshots

## Goal

Commit golden snapshots of current tier-1 loader output (raw frame, `raw_units`, loader
meta) under `tests/data/goldens/loader_<instrument>/`, regenerated via
`dev/regenerate_goldens.py`, with parametrized regression tests.

## Approach

1. Add `tests/loader_golden_support.py` — loader spec registry, load helper, JSON-safe meta
   export, raw-frame normalization (`data_point` index handling).
2. Extend `tests/golden_support.py` — `assert_raw_matches_golden` with datetime/timedelta
   tolerance (same ns slack as summary goldens).
3. Register one suite per tier-1 loader in `dev/regenerate_goldens.py`:
   `loader_arbin_res`, `loader_maccor_txt`, `loader_neware_txt`, `loader_pec_csv`,
   `loader_custom`.
4. Add `tests/test_loader_goldens.py` — parametrized `@pytest.mark.essential` tests; skip
   when source file or loader backend unavailable (ODBC for `arbin_res`).
5. Run `uv run python dev/regenerate_goldens.py` to commit artifacts; `--verify` for
   determinism.

## Files to touch

- `tests/loader_golden_support.py` (new)
- `tests/golden_support.py`
- `dev/regenerate_goldens.py`
- `tests/test_loader_goldens.py` (new)
- `tests/data/goldens/README.md`
- `tests/data/goldens/loader_*/` (generated)

## Test strategy

- `uv run pytest tests/test_loader_goldens.py -m essential`
- `uv run python dev/regenerate_goldens.py --verify loader_*`
- Full `uv run pytest` before close
