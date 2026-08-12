# Issue #878: batch: add a Batch method to export a self-contained project

Source: https://github.com/jepegit/cellpy/issues/878

## Original issue text

## Context

`cellpy` 1.x had `b.duplicate_cellpy_files(location="standard")`, which copied the cellpy-files of
a batch into the project folder so the experiment could be shared. It is gone in 2.x, and the
`cellpy_cookies` `standard` template currently has to spell the replacement out by hand (see the
"Packaging data" section of `01_..._loader.ipynb`):

```python
destination = Path("data/interim")
destination.mkdir(parents=True, exist_ok=True)

cellpy_files = []
for label in b.cell_names:
    cellpy_file = destination / f"{label}.cellpy"
    b.cells[label].save(cellpy_file, overwrite=True)
    cellpy_files.append(str(cellpy_file))

b.journal.pages = b.pages.with_columns(pl.Series("cellpy_file_name", cellpy_files))
b.save()
```

The journal rewrite is the part users get wrong: copying the files alone leaves
`cellpy_file_name` pointing at the author's `cellpydatadir`, so the shared bundle silently reads
the originals (or fails on the recipient's machine). That invariant belongs in `cellpy`, not in a
notebook template.

## Spec

Add a public `Batch` method, e.g.

```python
b.export_project("data/interim")  # -> Path to the written journal
```

that

- writes each cell in the batch to `<destination>/<label>.cellpy`,
- rewrites the `cellpy_file_name` column of the journal to those (relative) paths,
- saves the journal (`b.save()` semantics, i.e. `cellpy_batch_<name>.json` in the cwd unless a
  path is given).

`cellpy/batch/facade.py::_persist_cells` already does almost exactly this - it writes cells to the
paths in `cellpy_file_name`, rewrites the column, and calls `batch.save(journal_path)`. It is
private and only reachable through `batch.load`'s `_finalize`. The new method should reuse it
rather than duplicate the logic.

Open questions to settle while implementing:

- relative vs absolute paths in the exported journal (relative is what makes the bundle portable;
  `write_journal` / `read_journal` do not normalise paths, so relative round-trips fine),
- whether to also copy raw files / clear `raw_file_names`,
- whether unloaded cells should be loaded on demand or skipped.

## Acceptance criteria

- [ ] Public method on `Batch` that writes the cellpy-files, re-points `cellpy_file_name`, and
      saves the journal.
- [ ] Test: export to a tmp dir, then read the journal back and confirm every `cellpy_file_name`
      resolves inside the destination and loads.
- [ ] Docs mention it as the 2.x replacement for `duplicate_cellpy_files`.
- [ ] `cellpy_cookies` `standard/01_..._loader.ipynb` "Packaging data" cell reduced to a call to
      the new method.
