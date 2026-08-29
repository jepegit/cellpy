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

### Same-session `drop` vs `unload` (#952)

- `CellStore.unload` only evicts the cache; the label stays and the next
  access reloads. That is memory management, not a journal edit.
- `Batch.drop` / `drop_cells_marked_bad` call `CellStore.remove`, which
  drops `_labels` / `_cache` / `_loaders`. Pages and store stay aligned so
  `plot` / `summaries` / `report` work without a following `update()`.
- `mark_as_bad` only appends `session["bad_cells"]`. The load path above
  still drops those labels before `update()`.

### Feedback on unknown labels (#950)

Where the signal goes depends on who calls:

- `mark_as_bad(label)` **raises `ValueError`** for a label that is not in
  `journal.cell_names`. It is direct user input, nothing on the load path
  calls it, and a name that does not exist can never drop anything later.
- `drop(label)` **warns** (`UserWarning`) and no-ops for an unknown label.
- `drop_cells_marked_bad()` **stays quiet** about `bad_cells` entries it
  cannot find. `session` is persisted by `write_journal`, so a cell dropped
  in an earlier session is still listed after a reload; `_finalize` calls
  this method on every `load`, so warning there would fire on a normal
  round-trip. `mark_as_bad` is the gate that keeps bad labels out.

`session["bad_cells"]` is deliberately **not** pruned when a drop succeeds —
it is the record that a later `load(drop_bad_cells=True)` replays.

### Feedback on values that are not cells (#939)

Same raise/warn split, one layer up — at the point a batch is built from
objects the caller already holds rather than from a journal:

- `Batch.from_cells` **raises `ValueError`** naming every value that is not a
  cell, with the type that arrived. It is direct user input, and a `Path` or an
  `int` in that mapping can only ever produce a thinner collection later.
- `collect_summaries` **warns** (`UserWarning`) and names the cells that
  contributed no rows. It is not always a mistake — `max_cycle` / `rate` /
  `remove_last` legitimately empty a cell — so it must not raise, but the
  narrowing has to be visible. Cells skipped by `only_selected` are a
  deliberate choice and are **not** reported.
- `CellStore.from_cells` is **not** validated: it is the internal loader path
  (`_store_from_result` hands it whatever the runner produced, including
  `None` placeholders from `executor="processes"`).

"Is a cell" is decided by duck-typing on `.data`, asked of the **type**, not
the instance — `CellpyCell.data` is a property that raises `NoDataFound` until
something is loaded, so an instance-level `hasattr` would both raise and answer
"not a cell" for a legitimately empty cell.

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

## `Batch.export_project` (#878)

Shareable bundle, distinct from persist-after-load:

- Always rewrite `.cellpy` under `destination/` (`force_rewrite=True`).
- Journal `cellpy_file_name` is cwd-relative posix when possible.
- Journal still lands in cwd (`cellpy_batch_{name}.json`) unless `journal_path=`.
- Unloaded cells raise. Raw files are not copied; `raw_file_names` is left as-is
  (AUTO prefers existing `.cellpy`).

## Links

- Issue #822; grill plan restore_batch.load_orchestrator.
