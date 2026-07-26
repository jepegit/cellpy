# Issue #690 — Status

- [x] Done

## What's done

- Plan accepted (include `find -L`, warn @ 5000, no cache).
- STAT diet on `_remote_rglob_walk`: reuse `ls(detail=True)` for cycle keys; probe links with `ls` instead of `isdir`+`info`.
- `rglob(..., files_only=True)` + `find -L … -type f` fast path with walk fallback.
- `find_in_raw_file_directory` uses `files_only=True` (no per-hit `is_file()`); warn at ≥5000 paths.
- Docs: `docs/getting_started/remote_paths.md`, `.issueflows/04-designs-and-guides/otherpath-upath.md`.
- Tests: `tests/test_otherpath_symlink_rglob.py`, `tests/test_filefinder.py`.
- Pytest: targeted suite green; `pytest -m essential` green on close.
- HISTORY.md `[Unreleased]` bullet added.

## Remaining work

- None (ship via PR).
