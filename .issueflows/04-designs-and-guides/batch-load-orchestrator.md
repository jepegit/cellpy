# Orchestrated `batch.load` (#822)

## Context

Batch v3 initially made `cellpy.batch.load` a thin journal/DB constructor.
Notebooks expected the v1 flow: resolve journal → load cells → persist.

## Decision

`cellpy.batch.load` (and the `cellpy.utils.batch.load` shim) orchestrates again:

1. Resolve journal: explicit `journal_file` / `journal=` / `frame=`, else autoload
   `cellpy_batch_{name}.json` from `journal_dir` (default **cwd**), else DB.
2. `drop_bad_cells` (default True) removes `session["bad_cells"]`.
3. Always `Batch.update()` (legacy `link` is a no-op in v3).
4. Persist journal JSON when `save_cellpy=True` (default). Rewrite `.cellpy` only for cells loaded from raw (or `NEWEST` / `recalc`); skip rewrite when already loaded from an on-disk `.cellpy`.

### Journal location

- Default: `Path.cwd() / f"cellpy_batch_{name}.json"`.
- Override with `journal_dir=`.
- No IPython notebook-path sniffing: start the kernel with the notebook folder
  as cwd, or pass `journal_dir=` explicitly.

### Force flags / source preference

| Legacy / policy | `LoadPolicy.source` | Behavior |
|-----------------|---------------------|----------|
| (default) | `AUTO` | Use local `.cellpy` if the path exists; else raw. **No** freshness/FID check. |
| `policy=LoadPolicy(source=SourcePreference.NEWEST)` | `NEWEST` | Pass both paths to `cellpy.get` (raw vs cellpy FID/mtime check). |
| `force_raw_file=True` | `RAW_ONLY` | Raw only. |
| `force_cellpy=True` | `CELLPY_ONLY` | Cellpy path only (no existence short-circuit). |

Explicit `policy=` that conflicts with force flags raises `ValueError`.

`force_recalc=True` remakes the step table and summary after each successful load (summary C-rates come from steps; meta-only updates are not enough).

### Ignored kwargs

`export_cycles` / `export_raw` / `export_ica` are accepted and ignored
(one `UserWarning`).

## Alternatives

- Separate `load_batch` name — rejected; keep notebook call sites.
- Journal hit via noop `link` — rejected; store would stay empty.

## Links

- Issue #822; grill plan restore_batch.load_orchestrator.
