# Issue #912 — status

- [x] Done

## What's done

- `_frame_to_parquet_bytes` writes zstd level 3 (`PARQUET_COMPRESSION` / `PARQUET_COMPRESSION_LEVEL`).
- Essential tests: new save is ZSTD + ZIP_STORED; snappy members still load.
- `pytest tests/test_cellpy_file_v9.py` — 10 passed.
- HISTORY + test-registry updated.

## Remaining work

None.
