# OtherPath wraps universal_pathlib (G7)

**Decision (issues #375 / #371):** `cellpy.internals.otherpath.OtherPath` is a thin
compatibility wrapper around `upath.UPath` (fsspec backends). Remote raw/cellpy
*reads* still go through a single external → local temp copy seam; loaders never
speak SSH/SFTP.

**Supersedes:** architecture-plan “keep Fabric OtherPath, revisit fsspec later”
(configuration plan §5b, 2026-07-09). Fabric is removed once the wrapper is green.

**Supported product schemes:** `ssh://`, `sftp://`, `scp://` (`scp` aliased to
`sftp`). Other schemes are rejected with a clear error even if UPath could open them.

**Credentials:** `CELLPY_KEY_FILENAME` / `CELLPY_PASSWORD` (and host/user env where
used) map into fsspec/Paramiko `storage_options`. SSH agent / `~/.ssh/config` follow
Paramiko defaults.

**Not a `pathlib.Path` subclass:** call sites must accept `OtherPath` / `PathLike`
explicitly; do not rely on `isinstance(x, pathlib.Path)`.

**Symlink-following remote walk (issue #688):** fsspec SFTP `rglob` / `find` treat
directory symlinks as leaves, which breaks `rawdatadir=…/projects` when project
dirs are links. `OtherPath.rglob` (and deep `listdir`) therefore use an explicit
`ls(detail=True)` walk that recurses into links that resolve to directories, with a
visited-set cycle guard (inode / link destination / path). Shallow `glob` /
`listdir(levels≤1)` remain UPath passthrough. `filefinder.find_in_raw_file_directory`
keeps only regular files so directory matches are not counted as “files”.

**Remote dump performance (issue #690):** Chatty per-directory SFTP STATs made
`auto_use_file_list` dumps over a huge shared projects root very slow. Mitigations:
(1) reuse `ls(detail=True)` metadata for cycle keys / link targets instead of
extra `info`/`isdir` round-trips; (2) `rglob(..., files_only=True)` filters by
listing `type` so the dump does not call `is_file()` per path; (3) when Paramiko
`exec_command` is available, prefer a single remote `find -L <root> -type f`
and fall back to the optimized walk. Document that huge shared roots remain
expensive; prefer project-scoped `rawdatadir` (companion #691 for smarter scoping).
