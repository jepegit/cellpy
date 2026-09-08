# Issue #1017: journal_from_db(skip_file_search=True) crashes with the Excel reader

Source: https://github.com/jepegit/cellpy/issues/1017

## Original issue text

Found while diagnosing #1008.

`cellpy.batch.db.journal_from_db(name, project, db_reader="simple_excel_reader", skip_file_search=True)` raises

```
ValueError: All arrays must be of the same length
```

from `_dbengine.simple_db_engine` at `pd.DataFrame(pages_dict)`: `_create_pages_dict` seeds `raw_file_names` / `cellpy_file_name` as `[]` and only `find_files` fills them, so skipping the search leaves two zero-length columns next to the per-cell ones.

`skip_file_search` is documented for JSON readers that already carry the file columns, but the Excel path should either fill those columns with `None` per cell or reject the flag with a clear message.
