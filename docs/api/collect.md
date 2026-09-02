# Collect

Turn a batch into one tidy, multi-cell frame: summaries, cycle/capacity curves,
dQ/dV (ICA), or dV/dQ (DVA).

`cellpy.collect` is the 2.1 collectors redesign (it replaced the
`BatchCollector` family). `cellpy.utils.collectors` remains as a thin
re-export. Each collector returns a [`Collection`](#the-collection-product).

## Collectors

::: cellpy.collect

## Summary collection

::: cellpy.collect.summary

## Cycle / capacity curves

::: cellpy.collect.curves

## Incremental capacity (ICA)

::: cellpy.collect.ica

## Differential voltage (DVA)

::: cellpy.collect.dva

## The Collection product

::: cellpy.collect.collection
