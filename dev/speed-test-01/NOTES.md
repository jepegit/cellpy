# Speed session notes (2026-08-15)

Anonymized timings from a Windows PC + remote SFTP lab store. 25-cell
`arbin_sql_h5` batch. Cookie `batch.load` ~9 min first run. [#895](https://github.com/jepegit/cellpy/issues/895).

No hostnames, usernames, project names, or cell IDs here.

## Import (cookie cell 1)

| Step | s |
| --- | ---: |
| `import cellpy` | 0.18 |
| `import numpy` | 6.7 |
| **`import pandas`** | **62.4** (cold); ~1 s warm |
| `matplotlib.pyplot` | 4.0 |
| `cellpy.config` | 5.0 |
| `config.paths.rawdatadir` (scp URI) | 0.16 |
| `from cellpy import batch` | 0.12 |
| `helpers` / `plotutils` | 4.4 / 1.7 |

`#837` light `import cellpy` holds. SSH at config load is not the wait. Cold
pandas is Windows/conda cache (same class as `#837`). Cookie imports pandas/mpl
before `batch.load` needs them.

## One-cell primitives (not `batch.load` as a blob)

| Step | s |
| --- | ---: |
| `read_journal` / `resolve_specs` | 0.03 / 0.00 |
| `cellpy.get` local `.cellpy` 22 MB (cold) | **15.3** |
| `load_cell` AUTO (warm) | 0.20 |
| `OtherPath.copy` remote `.h5` 76 MB | 2.6–8.1 |
| parse local raw, `auto_summary=False` | 5.7 |
| `make_step_table` / `make_summary` | 0.60 / 0.13 |
| `load_cell` RAW_ONLY | 11.0 |

Morning ~9 min ≈ 25 × (copy + parse + save). Second AUTO hits local `.cellpy`.

Side: pip `pyarrow==24` leftover on conda `pyarrow-core==25` broke `.cellpy`
load (DLL). Harmonize prefetch hit `WinError 32` and fell back to legacy.

## OtherPath

| Step | s |
| --- | ---: |
| `OtherPath()` | 0.003 |
| first `is_file()` | **0.55–0.81** (SSH handshake) |
| later `is_file` / `stat` | ~0.006 |
| warm `copy()` | 2.6–3.6 |
| OpenSSH `scp` same file | 2.97 |

Transfer ≈ OpenSSH (~25 MB/s). Extra cost is STATs + silence, not a 3× tax.
`from_raw` always `is_file()` then loader `copy()`; each builds a new
credentialed `UPath`. fsspec `get_file` also `isdir()` then `ftp.get`.

## Executors (`run(..., executor=)`)

Cookie / default `batch.load` does not set `executor`.

| Work | serial | threads | processes |
| --- | ---: | ---: | ---: |
| AUTO 25 local `.cellpy` (warm) | 5.2 | **2.0** | 8.8 |
| RAW_ONLY 3 remote `.h5` | 38.5 | 37.1 | 34.1 |

Threads help **reopen**. First remote load does not overlap on the wire.
Processes lose on Windows spawn.

## Filefinder / `find -L` / `auto_use_file_list`

Names: `config.batch.auto_use_file_list`; remote `find -L <root> -type f` inside
`OtherPath.rglob(..., files_only=True)` (#690). Used by
`find_in_raw_file_directory`, **not** by per-cell `search_for_files`.

v3 `journal_from_db` never reads the flag. Cookie `batch.load` skipped
filefinder (`raw_file_names` already in the journal).

Project folder (~276 `.h5`): `find -L` 0.02 s vs walk 0.08 s. 25× `fnmatch` on
a dump **0.014 s**; 25× project `rglob` 0.88 s.

Full shared `rawdatadir`: 25× `search_for_files` no list **68.9 s**. Raw
`find -L` listed ~18k files in 0.12 s but **exit 1** (permission on a sibling
dir) so stdout is discarded. Dump then walks (~3.4 s, ~2k `.h5`).

`search_for_files` never sets `files_only=True`.

## v9 `.cellpy` I/O (22 MB zip, 526k × 18 raw)

Almost all `raw.parquet` (33 MB inflated / 22 MB stored).

Warm load: inflate 0.14 s, pyarrow **0.97 s**, translate ~0. Cold 15 s is page
cache / Defender. `CellpyCell.save` v9 **3.84 s** (parquet encode 0.74 s; rest
is `ZIP_DEFLATED` on already-compressed parquet + copies). v8 HDF5 save 1.70 s
(18.7 MB). **25 first-load writes ≈ 95 s**.

## `arbin_sql_h5` parse (76 MB, 529k × 16)

`Date_Time` is `int64` 100 ns ticks.

| Step | s |
| --- | ---: |
| HDFStore select | 0.31 |
| drop_duplicates | 0.76 |
| `apply(from_arbin_to_datetime)` | **2.84** |
| `pd.to_datetime` on those strings | **1.90** |
| `parse()` + `harmonize(arbin_epoch)` | 1.4 + **0.11** |
| legacy `loader()` / `_post_process` | **8.67** |
| `cellpy.get` harmonize ON | **11.8** |
| `cellpy.get` harmonize OFF | **8.8** |

Default two-stage path still runs the full legacy loader, then discards that
raw. `parse()` does not cache HDF frames and ignores `refuse_copying=` kwargs.

## Likely package cuts (not done)

1. Cookie: defer pandas / mpl / `plotutils`.
2. Cache credentialed `UPath` / `fs`; skip pre-copy `is_file`; progress on `copy()`.
3. Document `executor="threads"` for reopen.
4. Wire `auto_use_file_list` (prefer `project_dir=`); keep `find` stdout on exit 1;
   `files_only` in `search_for_files`; project-scoped `rawdatadir` (#691).
5. v9: `ZIP_STORED` for parquet members.
6. When harmonize prefetch succeeds, skip `_post_process` / second HDF read;
   vectorize legacy datetime if it must stay.
