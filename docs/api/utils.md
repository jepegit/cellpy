# Utils

Plotting and the analysis helpers. Batch and collection moved to their own
packages in 2.1 — see [Batch](batch.md) and [Collect](collect.md);
`cellpy.utils.batch` / `cellpy.utils.collectors` are thin re-export shims of
those.

## Batch (shim)

Re-exports [`cellpy.batch`](batch.md).

::: cellpy.utils.batch

## Plotting

::: cellpy.utils.plotutils

## Analysis

Incremental capacity analysis lives at [`cellpy.ica`](ica.md) since 2.0;
`cellpy.utils.ica` re-exports it.

::: cellpy.utils.ocv_rlx

::: cellpy.utils.helpers

## Collectors (shim)

Re-exports [`cellpy.collect`](collect.md).

::: cellpy.utils.collectors
