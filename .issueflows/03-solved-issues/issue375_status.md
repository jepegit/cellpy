# Status: Issue #375 (+ #371)

- [x] Done

## What's done

- Plan accepted; UPath-backed `OtherPath` (combines #371); Fabric removed.
- Deps: `universal-pathlib`, `paramiko`; `fabric` dropped.
- Truthful remote `exists` / `is_file` / `is_dir`; `scp://` → sftp; unsupported schemes error.
- `check_connection` / `filefinder` on UPath; remote `CellpyCell.save` rejected.
- Unit/mock tests + Docker SFTP property tests (`onlylocal`).
- Docs: `remote_paths.md`, config link, `HISTORY.md`, G7 note `otherpath-upath.md`.
- Essential + otherpaths/filefinder green at close.

## Remaining work

- None (landing via PR).
