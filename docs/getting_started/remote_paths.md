# Remote paths (SSH / SFTP)

cellpy can load raw data (and read cellpy files) from a remote host using
`ssh://`, `sftp://`, or `scp://` URIs. Remotes are handled by
`cellpy.internals.otherpath.OtherPath`, a thin wrapper around
[`universal_pathlib.UPath`](https://github.com/fsspec/universal_pathlib)
(fsspec + Paramiko). Instrument loaders still receive a **local** file: cellpy
copies the remote object to a temporary directory first.

## Supported schemes

| Scheme | Notes |
| --- | --- |
| `ssh://` | Supported (Paramiko via fsspec) |
| `sftp://` | Supported |
| `scp://` | Accepted as an alias; implemented as SFTP |

Other URI schemes (HTTP, FTP, SMB, cloud object stores, …) are **not** supported
as `rawdatadir` / path inputs and raise a clear error.

Example URI:

```text
sftp://user@hostname/home/user/lab/raw/20160805_test001_45_cc_01.res
```

## Credentials

Set one of these environment variables (or in your `.env_cellpy` file):

| Variable | Purpose |
| --- | --- |
| `CELLPY_KEY_FILENAME` | Path to an SSH private key (preferred) |
| `CELLPY_PASSWORD` | Password fallback if no key is set |
| `CELLPY_HOST` / `CELLPY_USER` | Optional helpers used by some tools/tests |

Paramiko may also use your SSH agent for keys. Do not put passwords in the
cellpy YAML config file.

### OpenSSH `Host` aliases (known limitation, #687)

URIs that use a short **`Host` alias** from `~/.ssh/config` (for example
`scp://odin/...` when `Host odin` maps to a real `HostName`) often fail with
`getaddrinfo` / DNS errors after the OtherPath → UPath switch. OpenSSH resolves
the alias; Paramiko/fsspec as used today typically does **not**.

**Workaround (supported today):**

1. Put the **fully resolvable hostname** (or IP) in the URI, not the short alias.
2. Export the private key explicitly (OpenSSH `IdentityFile` alone is not enough
   for this path):

```bash
export CELLPY_KEY_FILENAME="/path/to/your/private_key"
```

```yaml
Paths:
  # use the real HostName from ssh config, not the Host alias
  rawdatadir: scp://d1-odin-01.example.org/home/user/projects
```

If an earlier failed run left journal `raw_file_names` empty, recreate the
journal after fixing the URI. Restoring full `~/.ssh/config` Host-alias support
is tracked in [#687](https://github.com/jepegit/cellpy/issues/687).

## Configuring a remote raw-data directory

In the config / parameters paths section:

```yaml
Paths:
  rawdatadir: sftp://user@hostname/home/user/lab/raw
  cellpydatadir: C:/data/cellpyfiles
```

Then normal discovery and load APIs work:

```python
from cellpy import get
from cellpy.internals.connections import OtherPath
from cellpy import filefinder

raw = OtherPath("sftp://user@hostname/home/user/lab/raw")
files = filefinder.find_in_raw_file_directory(raw_file_dir=raw, extension="res")
c = get(files[0])  # copies remote → local temp, then loads
```

Use `cellpy.utils.helpers.check_connection()` (or
`cellpy.internals.connections.check_connection`) to diagnose a remote path.

## Cellpy files

- **Read** from a remote `.cellpy` / `.h5` path is supported: the file is copied
  locally before HDF5/v9 open.
- **Save** to a remote path is **not** supported and raises `ValueError`. Save
  locally, then upload with your own tools if needed.

## Behaviour notes

- `exists` / `is_file` / `is_dir` query the remote filesystem (they no longer
  assume “always true”).
- `OtherPath.copy()` downloads to `tempfile.gettempdir()` (or a directory you
  pass) and returns a local `pathlib.Path`.
- `OtherPath` is **not** a subclass of `pathlib.Path`. Prefer
  `isinstance(x, OtherPath)` or `os.fspath(x)` for local paths.
- Remote `OtherPath.rglob` (and deep `listdir`) **follows directory symlinks**
  when walking a tree, with a cycle guard. This matters when `rawdatadir` is a
  shared projects root and each project folder is a symlink (common on some
  lab file servers). Plain fsspec/UPath `rglob` does not follow those links.
  Shallow `glob` / `listdir(levels≤1)` stay non-recursive and do not add extra
  follow behaviour.
- **`Batch.auto_use_file_list` / `find_in_raw_file_directory`:** dumping an
  entire shared `rawdatadir` (all projects) over SFTP can still be expensive
  even though cellpy follows symlinks. Prefer pointing `rawdatadir` at the
  project folder, or set `auto_use_file_list: false`. Remote dumps use a
  file-only listing (`files_only`) and, when the SSH session allows it, a
  single remote `find -L … -type f` for speed, with a walk fallback. A warning
  is logged if the dump returns thousands of paths. Smarter project-scoped
  search is tracked separately (issue #691).

## Live SFTP tests (Docker)

Property tests against a real SFTP server live in
`tests/test_otherpaths_sftp.py` (marker `onlylocal`, deselected by default).
They start `docker/sftp-test/compose.yml` automatically when Docker is available:

```bash
uv run pytest tests/test_otherpaths_sftp.py -m onlylocal
```

See `docker/sftp-test/README.md`.
