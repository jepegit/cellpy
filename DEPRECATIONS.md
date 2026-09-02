# Deprecations

Auto-generated table of registered deprecations. Regenerate with:

```shell
uv run python -m cellpy._deprecation
```

| Name | Replacement | Introduced | Removal |
| --- | --- | --- | --- |
| `MultiCycleOcvFit.data` | `MultiCycleOcvFit.cell` | 2.1 | 2.2 |
| `MultiCycleOcvFit.set_data` | `MultiCycleOcvFit.set_cell` | 2.1 | 2.2 |
| `cellpy.collect.IcaOptions` | `cellpy.ica.IcaOptions plus cycles= / transforms=` | 2.1 | 2.3 |
