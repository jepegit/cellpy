# Issue #446 — status

- [x] Done

## What's done

- Branch `446-format-spec` created from `master`.
- `cellpy/readers/cellpy_file/format.py` — `CellpyFileFormat`, `FORMAT_V4`–`FORMAT_V8`, `get_format()`.
- `prms._cellpyfile_*` rewired as aliases onto `FORMAT_V8`.
- Template registry → `cellpy/utils/template_registry.py`; `cli.py` updated.
- Example-data URL constants → `cellpy/utils/example_data.py`.
- Dead `_globals_*` removed from `prms.py`.
- `tests/test_cellpy_file_format.py` added (parity + limits-prefix + version dispatch).
- Tests: 14/14 cellpy-file format+roundtrip green; 78/79 essential (1 pre-existing `loader_pec_csv` datetime dtype flake, unrelated).
- Grep: `prms._cellpyfile_*` are aliases only; `"/CellpyData"` literal only in `batch_helpers` comment (Stage 1.4).

## Remaining work

- [ ] `/iflow-close` when ready (PR + push).

## Judgment calls (plan open questions)

- Template registry: direct `cli.py` import only (no `prms` alias).
- `CellpyFileFormat.version` field included on each frozen instance.
- Version ints duplicated in `format.py` (not imported from `internal_settings`) to avoid `prms` import cycle.
