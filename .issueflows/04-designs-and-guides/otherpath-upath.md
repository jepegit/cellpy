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
