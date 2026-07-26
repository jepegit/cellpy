# Issue #688: Deal-breaker: remote OtherPath rglob / auto_use_file_list skips symlink project dirs under rawdatadir

Source: https://github.com/jepegit/cellpy/issues/688

## Original issue text

## Summary

After the switch from the self-built / Fabric-based `OtherPath` to `universal-pathlib` (`UPath` + fsspec/Paramiko), **recursive remote file search no longer follows symlink directories** under `rawdatadir`.

This breaks the normal batch workflow when project folders under the raw root are symlinks (common on our IFE `odin` layout, e.g. `projects/LongLife` → real storage). Journal creation then finds **zero matching raw files**, so `raw_file_names` stay empty and nothing loads.

**Severity:** deal-breaker for remote batch use. Needs a fix before we can rely on UPath-based remotes in production.

Related: #687 (SSH-config Host aliases / credentials) — separate problem; even with a DNS-resolvable host and working auth, this symlink/recursion bug still blocks loading.

## Observed behaviour (2.0.0rc2)

Config (after #687 workaround — full hostname):

```yaml
Paths:
  rawdatadir: scp://d1-odin-01.ad.ife.no/home/jepe@ad.ife.no/projects
Batch:
  auto_use_file_list: true
```

Log:

```text
Authentication (publickey) successful!
find_in_raw_file_directory: Found 70 files
...
raw_file_names: [None, None, ...]   # all cells
Raw file(s) not given in the journal.pages ...
```

Those “70 files” are **top-level project entries only** (directory/symlink names), not the `.h5` files inside them.

Per-cell match against that list (`*20250709_lol079_01_cc*.h5`) finds nothing.

## Evidence

From the parent `projects` listing, `LongLife` is a **symlink**:

```text
fs.ls(..., detail=True) → LongLife type=link
fs.info(.../LongLife)   → type=directory   # follows when opened directly
```

UPath/fsspec SFTP recursion from the parent does **not** descend into that link:

| Call | Result |
| --- | --- |
| `OtherPath(.../projects).rglob("*.h5")` | **0** |
| `OtherPath(.../projects).rglob("*")` | ~70 top-level names only |
| `filefinder.search_for_files(..., raw_file_dir=.../projects)` | **[]** |
| `OtherPath(.../projects/LongLife).rglob("*.h5")` / `search_for_files` | **works** (files found) |
| `fs.find(.../projects, maxdepth=2)` | lists `LongLife` as a leaf; **no** files under it |
| `fs.find(.../projects/LongLife, maxdepth=1)` | 332 files |

So both paths are broken when `rawdatadir` is the shared projects root:

1. `auto_use_file_list=True` → `filefinder.find_in_raw_file_directory` → `OtherPath.rglob("*")` → useless top-level list
2. `auto_use_file_list=False` → `search_for_files` → `OtherPath.rglob("<run>*.<ext>")` from the same root → still empty (no symlink follow)

This used to work with the pre-UPath OtherPath (Fabric / remote shell listing that followed links).

## Current workaround

Point `rawdatadir` at the concrete project path (the symlink path is OK if it is the search root):

```yaml
Paths:
  rawdatadir: scp://d1-odin-01.ad.ife.no/home/jepe@ad.ife.no/projects/LongLife
```

That is not acceptable as the long-term default: users keep a shared projects root and expect subfolder / symlink discovery.

## Expected behaviour

- Recursive remote discovery from `rawdatadir` **follows directory symlinks** the same way the old OtherPath did (at least one level of project-dir symlinks; ideally consistent with `find -L` / pathlib-on-local behaviour).
- `filefinder.find_in_raw_file_directory` and `search_for_files(..., sub_folders=True)` both find files under symlink project dirs.
- Prefer fixing in `OtherPath.rglob` / `glob` / listing so all callers benefit; if fsspec cannot follow links, implement an explicit follow-symlinks walk (e.g. `ls` + recurse into `type in {directory, link}` that resolve to dirs).

## Acceptance criteria

- [ ] With `rawdatadir` = remote `.../projects` and a symlink project dir (e.g. `LongLife`), `search_for_files("20250709_lol079_01_cc", raw_extension="h5", sub_folders=True)` returns the expected remote `.h5` path(s).
- [ ] `find_in_raw_file_directory()` / `auto_use_file_list=True` journal creation populates non-null `raw_file_names` for those cells.
- [ ] Regression test with a mocked SFTP (or local symlink fixture if equivalent) covering symlink project dirs.
- [ ] Docs note symlink-following behaviour for remotes.
- [ ] No silent “Found N files” where N is only top-level dirs when the intent was a recursive file dump (consider filtering to files only and/or warning when zero files match under symlink-heavy trees).

## Environment

- cellpy `2.0.0rc2` (UPath-based `OtherPath`)
- Remote: IFE odin SFTP (`d1-odin-01.ad.ife.no`)
- Instrument files: `arbin_sql_h5` under `projects/LongLife/` (symlink)
