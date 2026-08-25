# Batch

Load many cells, then work with the object you get back.

```python
from cellpy import batch

b = batch.load(name="my_experiment", project="my_project")
b.summaries
b.cells["my_cell_01"]
b.plot()
b.result.report()   # per-cell load outcomes
```

`b` is a [`Batch`](#batch). You do not need a separate "facade" type —
`cellpy.batch.facade` is only the implementation module.

## What `b` can do

| Want | Use |
| --- | --- |
| Journal table | `b.pages` |
| Cell labels | `b.cell_names` |
| One cell | `b.cells[label]` |
| Combined summaries | `b.summaries` |
| Summary plot | `b.plot()` |
| Load / reload | `b.update()` / `b.load()` |
| Per-cell load errors | `b.result.report()` |
| Drop a cell | `b.drop(label)` |
| Persist the journal | `b.save()` |

`cellpy.utils.batch` is a thin re-export of the same entry points.

## Entry points

::: cellpy.batch
    options:
      members:
        - load
        - Batch
        - from_journal
        - from_cells
        - Journal
        - LoadPolicy
        - BatchResult

## Batch

::: cellpy.batch.facade.Batch
    options:
      filters:
        - "!^_"
        - "!^experiment$"

## Journal

::: cellpy.batch.journal.Journal

## Aggregation

::: cellpy.batch.aggregate
    options:
      members:
        - combine_summaries
        - combine_tests
