# Issue #688 — Plan

## Goal

Restore remote recursive discovery under a shared `rawdatadir` when project
folders are **symlinks** (UPath/fsspec currently skips them), so batch
`auto_use_file_list` / `search_for_files` populate `raw_file_names` again. Also
stop `find_in_raw_file_directory` from counting directories as “files”, and fix the
secondary `NullData` NameError in empty-summary joins.

## Constraints

- Keep the UPath-based `OtherPath` (do not bring Fabric back).
- Prefer fixing listing in `OtherPath` so all callers benefit (not filefinder-only).
- Shallow `glob` / `listdir(levels≤1)` stay on UPath; only `rglob` and deep
  `listdir` get the symlink-following walk.
- Follow directory symlinks with a **cycle guard** (visited set of resolved paths).
- `#687` (SSH Host aliases / credentials) is **out of scope**.
- Back-compat: `rglob` may still yield directory matches for patterns like `*`;
  file-only filtering belongs in `find_in_raw_file_directory`.

### Prior art

- `OtherPath.rglob` / `listdir` — [`cellpy/internals/otherpath.py`](cellpy/internals/otherpath.py)
  (thin UPath wrappers; no symlink follow today).
- Design: [`.issueflows/04-designs-and-guides/otherpath-upath.md`](.issueflows/04-designs-and-guides/otherpath-upath.md).
- Callers: [`cellpy/readers/filefinder.py`](cellpy/readers/filefinder.py)
  (`find_in_raw_file_directory`, `search_for_files` → `rglob`).
- Live SFTP fixture: [`tests/test_otherpaths_sftp.py`](tests/test_otherpaths_sftp.py)
  + [`docker/sftp-test/`](docker/sftp-test/) (`onlylocal`).
- Unit OtherPath tests: [`tests/test_otherpaths.py`](tests/test_otherpaths.py).
- Filefinder tests: [`tests/test_filefinder.py`](tests/test_filefinder.py).
- `join_summaries` raises `NullData` without importing it —
  [`cellpy/utils/batch_tools/batch_helpers.py`](cellpy/utils/batch_tools/batch_helpers.py).
- Toolbox: none relevant.
- Graph: `OtherPath` god-node / SFTP test community — confirms touch points above.

## Approach

Agreed in grill-me:

1. **Custom remote walk for `OtherPath.rglob`** (and deep `listdir` that already
   uses `rglob`):
   - `fs.ls(path, detail=True)` recursively.
   - `type=directory` → recurse.
   - `type=link` → if target is a directory (`info` / `isdir`), recurse; if file,
     treat as a file candidate.
   - `type=file` → candidate for pattern match (`fnmatch` on name / relative path
     consistent with current `rglob` semantics).
   - Cycle guard: track resolved absolute remote paths already visited.
2. **`find_in_raw_file_directory`**: after `rglob`, keep only `is_file()` matches;
   if zero files, `critical`/warn clearly (do not claim “Found N files” for dirs).
3. **`NullData`**: add `from cellpy.exceptions import NullData` in `batch_helpers.py`.
4. **Tests**:
   - CI unit test: mock fsspec-like `ls(detail=True)` where a child is `type=link`
     resolving to a dir that holds a matching file; assert `rglob` finds it;
     assert cycle does not loop.
   - `onlylocal` Docker: add symlink project dir under `docker/sftp-test` data
     (or create via SFTP in test setup) and assert `rglob` / `search_for_files`
     from the parent root finds the file inside the link.
   - Unit test for filefinder: dump that would include dirs → list is files-only
     and logs/warns on empty.
   - Tiny test or assert that empty `join_summaries` raises `NullData` (not
     `NameError`).
5. **Docs**: note symlink-following for remote `rglob` in
   `docs/getting_started/remote_paths.md` and
   `.issueflows/04-designs-and-guides/otherpath-upath.md`.

### Data flow (after)

```text
rawdatadir = scp://host/.../projects
  → OtherPath.rglob("*.h5" | "*")
  → walk follows projects/LongLife (symlink→dir)
  → filefinder match / auto_use_file_list
  → journal.raw_file_names populated
```

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/internals/otherpath.py` | Symlink-following remote `rglob` (+ deep `listdir` via same path); cycle guard |
| `cellpy/readers/filefinder.py` | File-only filter + clearer zero-file logging in `find_in_raw_file_directory` |
| `cellpy/utils/batch_tools/batch_helpers.py` | Import `NullData` |
| `tests/test_otherpaths.py` (or new focused unit module) | Mocked remote symlink / cycle tests |
| `tests/test_otherpaths_sftp.py` + `docker/sftp-test/` | Symlink fixture + `onlylocal` assertion |
| `tests/test_filefinder.py` | Files-only dump behaviour |
| `tests/test_batch_helpers.py` or existing batch helper tests | `NullData` on empty join (add if missing) |
| `docs/getting_started/remote_paths.md` | Symlink-follow note |
| `.issueflows/04-designs-and-guides/otherpath-upath.md` | Record decision |

## Test strategy

- CI: `uv run pytest -m essential` (or project default gate) including new unit tests
  (not `onlylocal`).
- Local/opt-in: `uv run pytest tests/test_otherpaths_sftp.py -m onlylocal` with Docker.
- Manual smoke (optional during build): point `rawdatadir` at
  `scp://d1-odin-01.ad.ife.no/home/jepe@ad.ife.no/projects` and confirm
  `search_for_files("20250709_lol079_01_cc", raw_extension="h5")` returns paths
  under `LongLife/`.

## Open questions

None remaining after grill-me. Deferred by agreement:

- **#687** — SSH-config Host aliases / key via config (separate issue).
- Upstream fsspec fix — not waiting on it; cellpy walk is the product fix.

## Grill-me decisions (summary)

| # | Decision |
| --- | --- |
| Q1 | Fix in `OtherPath.rglob` / deep listing (not filefinder-only, not upstream-only) |
| Q2 | Follow dir symlinks always + cycle guard |
| Q3 | Apply to `rglob` + deep `listdir` only; shallow `glob`/`listdir` unchanged |
| Q4 | `find_in_raw_file_directory`: files only + warn on zero |
| Q5 | Unit mock (CI) + Docker symlink (`onlylocal`) |
| Q6 | Docs in this PR |
| Q7 | Include `NullData` import; exclude #687 |
