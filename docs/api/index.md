---
icon: material/api
---

# API reference

Generated from the docstrings in the source, so it cannot drift from the code.

If you are looking for *how to do something*, start with the
[tutorials](../examples/index.md) or the
[how-to guides](../guides/index.md) — this section is for when
you already know what you want and need the signature.

## Where to look

| You want | Look in |
| --- | --- |
| Load a file, get capacities, save | [cellpy](cellpy.md) — `get`, `CellpyCell` |
| The cell object and its frames | [Readers](readers.md) |
| Instrument loaders and the plugin contract | [Instruments](instruments.md) |
| Run a set of cells as one job | [Batch](batch.md) |
| Collect a batch into one tidy frame | [Collect](collect.md) — summaries, curves, ICA, DVA |
| Incremental capacity / DVA | [ICA and DVA](ica.md) — `dqdv`, `dvdq`, `IcaOptions` |
| Plot a cell or collection | [Plotting](plotting.md); `ica_plot` / `dva_plot` in [Utils](utils.md#plotting) |
| Helpers (OCV, …) | [Utils](utils.md) |
| Configuration and column schemas | [Parameters and config](parameters.md) |

## Stability

The surfaces documented here follow the deprecation cadence in
[Deprecations](../reference/deprecations.md): anything introduced as a shim in
2.0 is removed in 2.1, and anything prefixed with `_` may change without
notice.
