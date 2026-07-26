# Issue #690: perf: speed up remote auto_use_file_list / OtherPath.rglob dump

Source: https://github.com/jepegit/cellpy/issues/690

## Original issue text

## Summary

After #688, remote batch discovery works again when project folders under `rawdatadir` are symlinks, but `Batch.auto_use_file_list=True` against a shared projects root is **very slow**.

Observed (odin, `rawdatadir=…/projects`):

```text
13:35:58  Searching for files matching: *
13:38:52  Found 18279 files
```

≈ **3 minutes** before journal matching; the subsequent per-cell `fnmatch` and loads were fine.

Related: #688 (correctness — symlink follow). This issue is **performance**.

## Why it’s slow

1. **Scope** — dump walks the entire `projects` tree (all symlink project dirs), not the batch’s project.
2. **Chatty SFTP** — `OtherPath._remote_rglob_walk` does many round-trips (`ls` per directory, `info` for cycle guard, `isdir` on links). Pre-UPath/Fabric listing was closer to a single remote `find`.
3. **Extra STATs** — `filefinder.find_in_raw_file_directory` calls `is_file()` on every `rglob("*")` hit (dirs match `*`), amplifying round-trips on large trees.

## Expected improvements (any subset welcome)

- Prefer a **single remote find** / bulk listing when the backend supports it (Paramiko/SFTP exec or fsspec `find` with symlink follow), falling back to the current walk.
- When `ls(detail=True)` already provides `type=file` / `type=directory`, **do not** call `is_file()` again for filtering in `find_in_raw_file_directory`.
- Avoid redundant `info()` calls in the walk when `ls` detail is enough for cycle keys (path / destination).
- Optional: cache the file list for the session / journal recreate.
- Document that `auto_use_file_list` over a huge shared root is expensive; point users at project-scoped `rawdatadir` or the project-subdir search issue (companion issue).

## Acceptance criteria

- [ ] Dumping a remote `…/projects` tree with ~10k–20k files is substantially faster than today (order-of-magnitude goal: seconds–tens of seconds, not minutes), or we clearly document + warn when the dump will be huge.
- [ ] No regression on #688 symlink-following behaviour.
- [ ] Unit/integration tests cover the fast path (or mocked round-trip counts) where practical.
- [ ] Docs note performance trade-offs for `auto_use_file_list`.

## Workarounds (current)

- Set `rawdatadir` to the project folder (`…/projects/LongLife`), or
- Set `auto_use_file_list: false`.

## Comments (curated summary)

- **Clarifications / constraints**: Project-scoped search with fuzzy folder hints is out of scope here — tracked as companion #691.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-26._
