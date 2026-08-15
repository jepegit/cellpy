# Issue #912 — plan: zstd for v9 parquet members

Source: https://github.com/jepegit/cellpy/issues/912
Milestone: v.2.1.3

## Goal

New v9 `.cellpy` files write parquet with **zstd level 3** so on-disk size
returns to ~old ZIP_DEFLATED (~21 MB on the #895 cell) without putting a
second compressor on the zip. Old snappy v9 files still load. No format-version
bump.

## Constraints

- Keep `#898` `ZIP_STORED` on parquet members; `meta.json` may stay
  `ZIP_DEFLATED`.
- Do not bump `CELLPY_FILE_VERSION`. Reader already uses pyarrow and does not
  pin a parquet codec.
- Do not change column translation, atomic write, or member verify.
- No public `get` / `save` / schema / CLI surface change — no `agents.md` update.
- HISTORY is `/iflow-close`, not this plan.

### Prior art

- Toolbox (`.issueflows/00-tools/README.md`) — nothing for parquet codecs.
- [`cellpy/readers/cellpy_file/v9.py`](../../cellpy/readers/cellpy_file/v9.py)
  `_frame_to_parquet_bytes` — single write path; `to_parquet(..., engine="pyarrow")`
  with no `compression=` (snappy default).
- [`tests/test_cellpy_file_v9.py`](../../tests/test_cellpy_file_v9.py)
  `test_v9_parquet_members_are_stored_not_deflated` — sibling essential test
  for zip `compress_type`; mirror for codec.
- [`dev/regenerate_goldens.py`](../../dev/regenerate_goldens.py) pins
  `compression="snappy"` for **golden fixtures**, not `.cellpy` — leave it.
- `cellpy/libs/local_fastnda/btsda.py` brotli export — unrelated.
- No in-tree snappy v9 `.cellpy` fixture (testdata cellpy names are journal
  paths). Synthesize snappy members in the test.
- graphify community around `_frame_to_parquet_bytes` / v9 save — same module.

## Approach

1. In `_frame_to_parquet_bytes`, pass `compression="zstd"` and
   `compression_level=3`. Put those two values as module constants next to the
   helper (`PARQUET_COMPRESSION`, `PARQUET_COMPRESSION_LEVEL`) so the test
   imports them instead of magic strings.
2. Leave `save()` zip loop unchanged (`ZIP_STORED` parquet, DEFLATED meta).
3. Load path unchanged — `pandas.read_parquet(..., engine="pyarrow")` already
   decodes zstd and snappy.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/readers/cellpy_file/v9.py` | constants + `to_parquet` kwargs |
| `tests/test_cellpy_file_v9.py` | two essential tests (codec + snappy load) |

No new files. No `format.py` move (that module is HDF5/v9 **layout** keys).

## Test strategy

Project: conda `cellpy_dev_313` then `pytest` (or `uv run pytest`). Gate:

```bash
conda run -n cellpy_dev_313 pytest tests/test_cellpy_file_v9.py -q
```

New, `@pytest.mark.essential`, same v8-with-fids fixture as the #898 test:

1. **`test_v9_parquet_members_use_zstd`** — `save` a v9 file. For each
   `*.parquet` member: zip `compress_type == ZIP_STORED`, and
   `pyarrow.parquet.ParquetFile` metadata reports `ZSTD` (any column / row
   group).
2. **`test_v9_loads_snappy_parquet_members`** — save v9, rebuild a zip that
   swaps parquet members for the same frames encoded with `compression="snappy"`,
   `load_cellpy_file` succeeds and frames match. Proves old #898-era files
   still open.

Existing v9 essential tests stay green (round-trip, ZIP_STORED, atomic writes).

## Open questions

None — codec and level are in the issue Spec.
