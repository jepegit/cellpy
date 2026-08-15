# Issue #912: Use zstd for v9 parquet members

Source: https://github.com/jepegit/cellpy/issues/912

## Original issue text

## Problem / context

#898 stopped zip-DEFLATE on parquet members (`ZIP_STORED`). Save dropped ~3.8 s → ~0.9 s on a 526k-row cell. Files grew ~22 MB → ~34 MB because pandas/pyarrow `to_parquet` still defaults to **snappy**, and snappy is fast, not dense.

The right place to compress is the parquet codec, not the zip. Bake-off on the same raw frame (pyarrow 25, this machine):

| Codec | Encode | Decode | Size |
| --- | ---: | ---: | ---: |
| snappy (current) | 0.36 s | 0.026 s | 33.3 MB |
| zstd:3 | 0.45 s | 0.026 s | 21.3 MB |
| zstd:7 | 1.00 s | 0.025 s | 20.9 MB |
| brotli | 4.7 s | 0.050 s | 19.7 MB |
| gzip | 15.7 s | 0.037 s | 22.4 MB |

`zstd:3` gets the old on-disk size back (slightly better) without the zip-DEFLATE CPU tax. Decode matches snappy. Writer: `cellpy/readers/cellpy_file/v9.py` (`_frame_to_parquet_bytes`). Tests: `tests/test_cellpy_file_v9.py`. Notes: `dev/speed-test-01/NOTES.md`.

## Spec

- Write parquet members with **`compression="zstd"`** and **`compression_level=3`**.
- Keep `ZIP_STORED` for parquet members; `meta.json` may stay `ZIP_DEFLATED`.
- Do not bump the on-disk schema version. Old snappy v9 files must still load.
- Keep atomic write + member verify. Do not change column translation.

## Acceptance criteria

- [ ] `_frame_to_parquet_bytes` (or the write path it feeds) uses zstd level 3.
- [ ] New or extended test writes a v9 file and asserts the parquet member is zstd (footer / pyarrow metadata), not snappy.
- [ ] Existing `tests/test_cellpy_file_v9.py` stays green, including load of a pre-existing snappy fixture if one is in-tree.
- [ ] No zip-level compressor on parquet members.

## Goal

New v9 files are ~snappy-speed to write and ~old-DEFLATE size on disk; old v9 files still open.

## Out of scope

Zip BZIP2/LZMA/DEFLATE on parquet. brotli/gzip. Changing the default file format (v9 stays). Dropping `Data.copy()` / `to_native`.

Follow-up to #898. Same milestone as epic #896.
