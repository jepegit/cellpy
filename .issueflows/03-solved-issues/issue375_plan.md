# Plan: Issue #375 (+ #371) — Remote paths via `universal_pathlib`

**Status:** Accepted (2026-07-17) — ready for `/iflow-start`.

## Goal

Ship usable remote raw/cellpy path workflows (`ssh`/`sftp`/`scp`) by replacing the Fabric-heavy `OtherPath` implementation with a thin cellpy API wrapper around [`universal_pathlib.UPath`](https://github.com/fsspec/universal_pathlib) (issue [#371](https://github.com/jepegit/cellpy/issues/371)), then documenting and testing the acceptance criteria from [#375](https://github.com/jepegit/cellpy/issues/375).

This **combines #375 and #371** in one delivery: UPath is the remote backend *and* the way we get real `exists`/`is_file`/`glob`/copy semantics.

## Constraints

- **Preserve the cellpy `OtherPath` public surface** used by config, filefinder, loaders, and batch: `is_external`, `uri_prefix`, `location`, `original` / `full_path`, `raw_path`, `copy()` → local `pathlib.Path`, plus pathlib-like ops callers already use (`/`, `name`, `parent`, `glob`, `exists`, `is_file`, `is_dir`, …). Prefer delegation over rewriting call sites.
- **Copy-then-load stays.** Instrument loaders and HDF5 still receive a **local** `pathlib.Path` after `OtherPath.copy()` / `resolve_hdf5_path` / `copy_to_temporary`. Do not teach readers remote open.
- **URI / env back-compat:** `ssh://`, `sftp://`, `scp://` strings and `CELLPY_KEY_FILENAME` / `CELLPY_PASSWORD` (+ host/user where used) keep working; map into UPath/fsspec `storage_options` (Paramiko kwargs).
- **Architecture G7 update:** Prior note said “keep Fabric OtherPath, fsspec later” ([`cellpy2-configuration-and-parameters-plan.md`](../../../architecture-plan/cellpy2-configuration-and-parameters-plan.md) §5b). **This work supersedes that:** wrap UPath now; keep a single external→local seam so backends can still change later. Record the decision in `.issueflows/04-designs-and-guides/` during `/iflow-start` (short note + link to #375/#371).
- **No broad loader rewrite.** Touch other packages only where `isinstance(..., pathlib.Path)` / Fabric assumptions break.
- **KISS:** One wrapper module; delete Fabric path helpers once tests pass; do not add S3/GCS/etc. product support in this issue even if UPath can open them.

### Prior art

| Hit | Role | Plan |
| --- | --- | --- |
| [`cellpy/internals/otherpath.py`](../../cellpy/internals/otherpath.py) | Fabric `OtherPathNew`/`Legacy`; stub external `exists`/`is_file` | **Replace guts** with UPath wrapper; drop dual New/Legacy if possible |
| [#371 body sketch](https://github.com/jepegit/cellpy/issues/371) | Thin `OtherPath` → `_upath`; `copy` via `fs.get` | **Adopt** as implementation outline |
| [`cellpy/internals/connections.py`](../../cellpy/internals/connections.py) | `OtherPath` export, `check_connection` | Retarget probe to UPath/`exists` or thin fs ping |
| [`cellpy/readers/filefinder.py`](../../cellpy/readers/filefinder.py) | Remote discovery (SSH `find` / glob) | Prefer UPath `glob`/`iterdir`; remove Fabric `find` if redundant |
| [`…/instruments/base.py`](../../cellpy/readers/instruments/base.py) `copy_to_temporary`, [`cellpy_file/read.py`](../../cellpy/readers/cellpy_file/read.py) `resolve_hdf5_path` | External → local | Keep call shape; ensure `OtherPath.copy()` still returns local `Path` |
| [`cellpy_file/write.py`](../../cellpy/readers/cellpy_file/write.py) / `CellpyCell.save` | Local write | **Reject** remote save targets |
| Config `OtherPathField` + `CELLPY_*` env | Path coercion / secrets | Wire credentials into UPath `storage_options`; docs |
| [`tests/test_otherpaths.py`](../../tests/test_otherpaths.py) | Characterization + Fabric monkeypatches | **Expand first** (API contract), then retarget mocks to fsspec/UPath |
| `isinstance(..., pathlib.Path)` call sites (`batch_journals`, `prmreader`, `config/types`, …) | Assume Path subclass | Audit + fix — UPath wrapper likely **not** a `pathlib.Path` subclass (#371 note) |
| `fabric` in `pyproject.toml` | Current remote transport | **Remove** once UPath+Paramiko path is green (Paramiko already transitive / explicit) |
| `universal-pathlib` | Not yet a dependency | **Add** (+ ensure `paramiko` for ssh/sftp) |

## Approach

### Product decisions (recommended)

1. **Schemes in scope for “supported”:** `ssh://`, `sftp://`, and `scp://` (alias `scp` → `sftp`/`ssh` for UPath if needed). Other URI prefixes: either clear “not supported by cellpy” error **or** pass through to UPath only if zero extra deps — **default: supported set only** for documented workflows; unknown schemes raise clearly.
2. **Auth:** `CELLPY_KEY_FILENAME` → Paramiko `key_filename`; `CELLPY_PASSWORD` → `password`; host/user from URI and/or `CELLPY_HOST`/`CELLPY_USER`. Document SSH agent / `~/.ssh/config` as Paramiko default behavior.
3. **Unreachable remote:** Fail fast (no always-True stubs).
4. **Cellpy files:** remote **read** via temp copy; remote **save** rejected with clear error.
5. **`isinstance(x, pathlib.Path)`:** Prefer fixing call sites to accept `OtherPath` / `os.PathLike` / explicit conversion over pretending to subclass `pathlib.Path` (UPath’s model). Keep `isinstance(x, OtherPath)` working everywhere it already does.

### Implementation order (matches #371 guidance)

1. **Characterization tests** — lock current public `OtherPath` behavior (URI parse, properties, local ops, external `copy`/`glob` contracts, credential env errors) with mocks; note which tests encode Fabric-specific internals.
2. **Add deps** — `universal-pathlib` (+ pin policy consistent with project); ensure `paramiko` available for ssh/sftp.
3. **Rewrite `otherpath.py`** — thin wrapper around `UPath` preserving cellpy properties/methods; `_credentials_from_env()` → `storage_options`; `copy()` uses `fs.get` (or equivalent) to temp local path.
4. **Call-site audit** — fix `isinstance(..., Path)` / pickle / pydantic `OtherPathField` / `check_connection` / filefinder remote search to work with wrapper (minimal diffs).
5. **Remove Fabric path** — delete `_*_with_fabric` helpers; drop `fabric` dependency if nothing else needs it; simplify `get_otherpath_class()` (no 3.12 Legacy/New split if wrapper is version-agnostic).
6. **#375 productization** — remote save rejection; user docs (URI, env, rawdatadir, temp-copy model, save policy); HISTORY note (backend change + truthful `exists`/`is_file`).
7. **Close linkage** — PR references both #375 and #371; close #371 when merged (or mark duplicate of #375).

### Out of scope

- Product support for S3/HTTP/SMB/GCS as rawdatadir (even if UPath can open them)
- Remote upload / save-back
- Teaching instrument readers to open remote file handles
- Full redesign of filefinder / batch path layout
- Migrating Secrets into a new pydantic model beyond wiring env → `storage_options` (config plan Step 6 can refine later)

### Scope / split check

One issue-branch / one PR is the intent (user: combine with #371). Internally keep commits ordered: tests → wrapper → call sites → drop Fabric → docs. If the PR becomes unreviewable, split **docs/AC polish** only — do **not** ship Fabric hardening without UPath.

## Files to touch

| Path | Change |
| --- | --- |
| `pyproject.toml` / lock | Add `universal-pathlib`; drop `fabric` when unused; ensure `paramiko` |
| `cellpy/internals/otherpath.py` | UPath-backed `OtherPath`; remove Fabric implementation |
| `cellpy/internals/connections.py` | `check_connection` / exports |
| `cellpy/readers/filefinder.py` | Discovery via UPath APIs; drop SSH `find` if obsolete |
| `cellpy/readers/cellreader.py` and/or `cellpy_file/write.py` | Reject remote save |
| `cellpy/config/types.py` (and related) | Coercion / isinstance fixes |
| Other isinstance call sites (as found) | Accept `OtherPath` without requiring `pathlib.Path` subclass |
| `tests/test_otherpaths.py` (+ filefinder / cell_readers as needed) | Contract tests; fsspec/UPath mocks |
| `docs/source/…` | Remote path user docs |
| `HISTORY.rst` (or project changelog) | User-visible notes |
| `.issueflows/04-designs-and-guides/` | Short G7 decision: OtherPath wraps UPath |

## Test strategy

```bash
uv run pytest tests/test_otherpaths.py -q
uv run pytest tests/test_filefinder.py tests/test_cell_readers.py -q
uv run pytest -m essential
```

- CI: mock fsspec/UPath filesystem (or monkeypatch `OtherPath._upath` / `fs.get`) — **no live SSH**.
- Optional live tests remain env-gated (`CELLPY_TEST_*`).
- Explicit tests: URI parse; env credentials → storage_options; external `exists`/`is_file` True/False; `copy` returns local `Path`; remote save raises; unsupported scheme error.

## Open questions

Confirm or revise:

1. **Combine #371 into this branch/PR?**  
   **Recommended (per your revise):** Yes — UPath first, then #375 ACs on top.

2. **Drop `fabric` in the same PR?**  
   **Recommended:** Yes, once tests pass on UPath+Paramiko.

3. **`scp://` handling?**  
   **Recommended:** Accept as alias to `sftp`/`ssh` for UPath (document alias).

4. **Cellpy remote save?**  
   **Recommended:** Reject with clear error (unchanged).

5. **`isinstance(..., pathlib.Path)` strategy?**  
   **Recommended:** Do **not** subclass `pathlib.Path`; fix call sites / use `OtherPath` or `PathLike` (matches #371 warning).

6. **Docs?**  
   **Recommended:** User-facing remote-paths section + HISTORY + design note under `04-designs-and-guides/`.

7. **Close #371 how?**  
   **Recommended:** Same PR `Closes #375` and `Closes #371` (or “Fixes #371 as part of #375”).

---

**Branch preflight (plan time):** `375-add-support-for-remote-paths-for-raw-data-and-cellpy-data-access`; sync with `origin/master` before `/iflow-start` as needed.
