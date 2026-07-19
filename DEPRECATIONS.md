# Deprecations

Auto-generated table of registered deprecations. Regenerate with:

```shell
uv run python -m cellpy._deprecation
```

| Name | Replacement | Introduced | Removal |
| --- | --- | --- | --- |
| `ica.Converter` | `cellpy.ica.transform_half_cycle with IcaOptions` | 2.0 | 2.1 |
| `ica.dqdv(cycle=...)` | `cellpy.ica.dqdv(cycles=...)` | 2.0 | 2.1 |
| `ica.dqdv(label_direction=...)` | `the direction column, which the specced frame always carries` | 2.0 | 2.1 |
| `ica.dqdv(split=... / tidy=...)` | `cellpy.ica.dqdv(direction=...) and cellpy.ica.to_wide()` | 2.0 | 2.1 |
| `ica.dqdv_cycle` | `cellpy.ica.dqdv (returns the specced long frame)` | 2.0 | 2.1 |
| `ica.dqdv_cycles` | `cellpy.ica.dqdv (returns the specced long frame)` | 2.0 | 2.1 |
| `ica.dqdv_np` | `cellpy.ica.transform_half_cycle with IcaOptions` | 2.0 | 2.1 |
| `legacy header attribute access (headers_normal / _summary / _step_table)` | `c.schema.raw / c.schema.steps / c.schema.summary` | 2.0 | 2.1 |
| `make_new_cell` | `CellpyCell.vacant` | 2.0 | 2.1 |
| `the 'dq' column of the ica output frame` | `the 'dqdv' column of the same frame` | 2.0 | 2.1 |
