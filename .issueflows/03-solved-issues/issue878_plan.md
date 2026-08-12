# Plan — #878: `Batch.export_project`

## Goal

Add a public `Batch.export_project(destination)` that writes each loaded cell
to `<destination>/<label>.cellpy`, rewrites journal `cellpy_file_name` to those
**relative** paths, and saves the journal (`Batch.save()` semantics). Replace
the hand-rolled cookiecutter “Packaging data” snippet and document it as the
2.x stand-in for 1.x `duplicate_cellpy_files`.

## Constraints

- Reuse [`_persist_cells`](cellpy/batch/facade.py) — do not copy its save/journal
  loop. Extend it with a `force_rewrite` flag so export always writes (persist
  after `batch.load` still skips rewrite when the cell was loaded from an
  existing `.cellpy`).
- Do **not** resurrect `duplicate_cellpy_files` as a `warn_once` shim (already
  gone). Docs + cookie only.
- Path strings in the journal: **posix** (`Path.as_posix()`), matching
  [this-project.md](../04-designs-and-guides/this-project.md) (cross-platform
  metadata).
- Public Batch surface change: mention in migration docs. `agents.md` has no
  Batch recipe today — skip unless we add a one-liner under a batch note.
- Cookie file on disk is
  `01_{{cookiecutter.notebook_name}}_processing.ipynb`, not `01_..._loader.ipynb`
  (issue text is slightly wrong).
- Follow [batch-load-orchestrator.md](../04-designs-and-guides/batch-load-orchestrator.md):
  journal default is cwd `cellpy_batch_{name}.json`.

### Prior art

- `_persist_cells` / `_should_rewrite_cellpy` / `_default_cellpy_path` —
  `cellpy/batch/facade.py`. **Migrate later / extend:** add `force_rewrite`;
  export points `cellpy_file_name` at dest then calls persist.
- `Batch.save` / `export_journal` — journal JSON only. **Coexist:** keep
  `export_journal`; new method is cells + journal rewrite.
- Persist tests in `tests/test_batch.py`
  (`test_persist_skips_rewrite_when_loaded_from_cellpy`,
  `test_persist_rewrites_when_loaded_from_raw`). **Mirror** with an export
  round-trip test; do not change skip-rewrite defaults.
- Cookie “Packaging data” cell still comments `# b.duplicate_cellpy_files(...)`.
- Toolbox (`00-tools/`): none relevant.
- Graphify: `graphify-out/` not present.

## Approach

```python
b.export_project("data/interim")           # journal → cwd/cellpy_batch_{name}.json
b.export_project(dest, journal_path=path)  # tests / explicit journal location
```

1. `destination.mkdir(parents=True, exist_ok=True)`.
2. **Unloaded cells:** raise `ValueError` listing labels (do not skip, do not
   auto-`update()` — that can hit remote raw and is #890 territory).
3. Rewrite `cellpy_file_name` to `{destination}/{label}.cellpy`, stored
   **relative to cwd** when possible (`Path.resolve().relative_to(cwd)`), else
   absolute; always `.as_posix()`.
4. Call `_persist_cells(batch, journal_path, force_rewrite=True)` so every
   loaded cell is written even if `result.source == "cellpy"` and dest already
   exists.
5. `_persist_cells`: when writing the column back, keep posix relative strings
   (today `str(dest)` can become absolute/backslash on Windows).
6. Return the journal `Path` from `batch.save`.

**Out of scope (issue open questions, decided):**

| Question | Decision |
|---|---|
| Relative vs absolute `cellpy_file_name` | Relative to cwd (portable bundle). |
| Copy raw / clear `raw_file_names` | Neither. AUTO + existing `.cellpy` is enough (#825). Author-local raw paths may remain; they are unused if cellpy files exist. |
| Unloaded cells | Error, do not skip or auto-load. |

## Files to touch

| Path | Change |
|---|---|
| `cellpy/batch/facade.py` | `Batch.export_project`; `_persist_cells(..., force_rewrite=False)`; posix path write-back |
| `tests/test_batch.py` | Round-trip essential test; persist skip-rewrite still holds when `force_rewrite` is default |
| `docs/getting_started/migration_v1_to_v2.md` (and/or `migration_v2.0_to_2.1.md` batch table) | `duplicate_cellpy_files` → `Batch.export_project` |
| `examples/cellpy project template/.../01_*_processing.ipynb` | Packaging cell → `b.export_project("data/interim")` |

No `DEPRECATIONS.md` row (no shim). No new toolbox script.

## Test strategy

```bash
uv run pytest tests/test_batch.py -k persist or export_project -m essential
uv run pytest -m essential
```

New test (mark **essential** — journal path invariant, same class as persist tests):

1. Build a tiny `Batch` with one loaded fake/real cell (same stub pattern as
   persist tests, or `example_data` if cheap).
2. `export_project(tmp_path / "interim")` with cwd = tmp (or `journal_path=`).
3. Assert each `.cellpy` exists under destination.
4. `read_journal` the written JSON; every `cellpy_file_name` is relative/posix
   and resolves inside destination; `cellpy.get` / `Batch` load from those
   paths succeeds (or stub `save` wrote bytes that round-trip).

Keep existing persist skip-rewrite tests green (default `force_rewrite=False`).

## Open questions

None blocking — table above is the recommended set. Confirm or override on Accept.
