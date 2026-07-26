# Issue #688 — Status

- [x] Done

## What's done

- Symlink-following remote walk in `OtherPath.rglob` (+ deep `listdir`), cycle guard via inode/destination/path
- `find_in_raw_file_directory` keeps regular files only; clearer zero-file critical log
- `NullData` import in `batch_helpers.join_summaries`
- Unit tests: `tests/test_otherpath_symlink_rglob.py`, filefinder files-only, NullData raise
- Docker SFTP fixture: rw volume + `project_link` symlink; `onlylocal` test added
- Docs: `docs/getting_started/remote_paths.md`, `otherpath-upath.md`, docker README
- Live smoke on odin: finds files under `projects/LongLife` symlink
- Essential suite green (628 passed); HISTORY bullet added

## Remaining work

- None
