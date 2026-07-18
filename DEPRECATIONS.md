# Deprecations

Auto-generated table of registered deprecations. Regenerate with:

```shell
uv run python -m cellpy._deprecation
```

| Name | Replacement | Introduced | Removal |
| --- | --- | --- | --- |
| `legacy header attribute access (headers_normal / _summary / _step_table)` | `the native cellpycore schema column names` | 2.0 | 2.1 |
| `make_new_cell` | `CellpyCell.vacant` | 2.0 | 2.1 |
