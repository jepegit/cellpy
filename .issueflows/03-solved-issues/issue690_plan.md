# Issue #690 — Plan

## Goal

Make remote `Batch.auto_use_file_list` / `find_in_raw_file_directory` dumps
over a large shared `rawdatadir` (e.g. `…/projects` with symlink project dirs)
substantially faster (seconds–tens of seconds, not minutes), without regressing
#688 symlink-following behaviour, and document the remaining cost/trade-offs.

## Constraints

- Keep UPath-based `OtherPath`; do not bring Fabric back
  ([otherpath-upath.md](../04-designs-and-guides/otherpath-upath.md)).
- Preserve #688 semantics: remote `rglob` / deep `listdir` follow directory
  symlinks with a cycle guard; shallow `glob` / `listdir(levels≤1)` stay
  UPath passthrough.
- `#691` (project-scoped / fuzzy folder search) is **out of scope** — only
  mention as the recommended alternative when the dump root is huge.
- Session/journal file-list cache is **optional / deferred** unless a tiny
  hook falls out for free; not required for acceptance.
- Prefer fixing listing in `OtherPath` so all callers benefit; filefinder
  should stop paying extra remote STATs when the walk already knows `type`.

### Prior art

- Hot path: [`OtherPath._remote_rglob_walk`](../../cellpy/internals/otherpath.py)
  — per-dir `fs.info` (cycle key) + `fs.ls(detail=True)` + `fs.isdir` on every
  `type=link`; yields dirs and files for `*`.
- Caller: [`filefinder.find_in_raw_file_directory`](../../cellpy/readers/filefinder.py)
  — `rglob("*")` then **`match.is_file()` per hit** (another remote STAT for
  every path, including directories).
- Batch wiring: [`Batch.create_journal`](../../cellpy/utils/batch.py)
  (`auto_use_file_list=True` → dump once, then local `fnmatch`).
- #688 solution + design note:
  [issue688_plan](../03-solved-issues/issue688_plan.md),
  [otherpath-upath.md](../04-designs-and-guides/otherpath-upath.md),
  docs in [`remote_paths.md`](../../docs/getting_started/remote_paths.md).
- Tests to extend: [`tests/test_otherpath_symlink_rglob.py`](../../tests/test_otherpath_symlink_rglob.py)
  (fake FS with call-count hooks), [`tests/test_filefinder.py`](../../tests/test_filefinder.py),
  optional [`tests/test_otherpaths_sftp.py`](../../tests/test_otherpaths_sftp.py)
  / [`docker/sftp-test/`](../../docker/sftp-test/).
- fsspec `find` **does not** follow symlink dirs (#688 evidence) — not a drop-in
  bulk fix unless we add our own follow or use remote shell `find -L`.
- Toolbox: none relevant. Graph: skipped (`graphify-out/` absent).

## Approach

Ship two complementary speedups in one PR; keep a clean fallback to today’s walk.

### 1. STAT diet on the existing walk (always on)

In `_remote_rglob_walk`:

- **Reuse `ls(detail=True)` metadata** when descending: pass ino / destination /
  type from the parent entry into `visit_key` so we do **not** call `fs.info`
  again for every directory we already listed.
- For `type=link`: prefer cycle key from `destination` / listing detail; avoid
  a separate `isdir` when we can decide “recurse vs file” with one attempt
  (e.g. `ls` on the link path, or cached detail). Keep cycle-guard behaviour
  identical to #688 tests.
- Do **not** change which paths `rglob("*")` yields (dirs may still match `*`)
  unless an explicit opt-in is used (below).

### 2. File-only dump path for `find_in_raw_file_directory` (always on)

- Add a small opt-in on remote listing, e.g. `rglob(..., files_only=True)` or a
  private helper used only by the dump, that **filters with walk `type`**
  (`file`, and links that resolve to files) and **never** calls `is_file()`
  per match.
- Local pathlib path: keep cheap `Path.is_file()` (or `files_only` via
  `Path.is_file()` once — local cost is fine).
- Log a clear warning when a remote dump returns a very large list (threshold
  constant, e.g. ≥5k) pointing at project-scoped `rawdatadir` and `#691`.

### 3. Bulk remote `find -L` fast path (preferred when available)

When the remote backend can run a shell command (Paramiko client /
  `fs` exec / similar), prefer a **single** remote listing for full-tree file
  dumps:

```text
find -L <root> -type f -print
```

(or equivalent that follows directory symlinks and lists files only).

- Map stdout lines → `OtherPath` / full paths; apply the same glob filter
  (`*` / extension) client-side.
- **Fallback** to the optimized walk on any failure (no shell, permission,
  non-POSIX remote, empty/error output).
- Scope: use for the dump / `files_only` case first; patterned `rglob("*.h5")`
  may stay on the walk unless the same fast path is trivial to reuse.
- Escape/quote the root path carefully; never interpolate untrusted patterns
  into the shell command beyond the already-trusted path string.

### 4. Docs + design note

- [`docs/getting_started/remote_paths.md`](../../docs/getting_started/remote_paths.md):
  note that `auto_use_file_list` over a huge shared root is expensive; prefer
  project-scoped `rawdatadir`; mention `#691` for smarter scoping; document
  fast-path + fallback briefly.
- Update [otherpath-upath.md](../04-designs-and-guides/otherpath-upath.md)
  with the perf strategy (STAT reuse + optional `find -L`).

### Data flow (after)

```text
auto_use_file_list=True
  → find_in_raw_file_directory(rawdatadir=…/projects)
  → remote files_only dump:
       try:  find -L … -type f   (1 round-trip)
       else: optimized ls-walk (no per-hit is_file / fewer info)
  → list[str] for journal fnmatch
  → warn if N huge; docs point at project-scoped root / #691
```

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/internals/otherpath.py` | STAT-efficient walk; optional `files_only`; `find -L` fast path + fallback |
| `cellpy/readers/filefinder.py` | Use file-only remote dump; large-N warning; drop redundant `is_file` STATs |
| `cellpy/utils/batch.py` | Optional: slightly clearer critical/info when dump is remote/huge (only if needed) |
| `docs/getting_started/remote_paths.md` | Perf trade-offs + workarounds |
| `.issueflows/04-designs-and-guides/otherpath-upath.md` | Perf note under symlink-walk section |
| `tests/test_otherpath_symlink_rglob.py` | Round-trip / call-count asserts; `files_only`; fast-path mock |
| `tests/test_filefinder.py` | Remote dump does not call `is_file` (mocked); large-N warn |
| `tests/test_otherpaths_sftp.py` | Optional smoke if Docker path stays cheap |

## Test strategy

```bash
uv run pytest -m essential
uv run pytest tests/test_otherpath_symlink_rglob.py tests/test_filefinder.py
# optional live:
uv run pytest tests/test_otherpaths_sftp.py -m onlylocal
```

- Keep all #688 symlink / cycle tests green.
- New unit tests: fake FS counters prove fewer `info` / `isdir` / `isfile`
  calls; `files_only` omits directories; mocked exec returns bulk list and walk
  is not used; exec failure falls back to walk.
- Mark merge-gate tests `@pytest.mark.essential` only if they stay fast and
  guard the dump contract (prefer extending existing essential filefinder /
  OtherPath tests carefully).

## Open questions

1. **Include `find -L` in this PR?** Recommended **yes** (biggest win for
   ~18k-file odin trees). Alternative: STAT diet + docs only in this PR, shell
   find as a follow-up. **Default if you Accept without comment: include it.**
2. **Large-N warn threshold?** Proposed **5000** files. OK?
3. **Cache** across journal recreates in one process? Proposed **defer** (out
   of this PR).

## Scope check

Single focused PR (listing perf + docs). Not mixing #691 project-scoped search.
If `find -L` proves messy on Windows-dev / Paramiko access, ship (1)+(2)+docs
and park (3) as a tiny follow-up issue — still meets “or document + warn” AC,
but may miss the order-of-magnitude goal on odin until (3) lands.
