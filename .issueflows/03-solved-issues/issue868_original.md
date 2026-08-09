# Issue #868 — fullcell_standard_* families can't be collected

**Source:** https://github.com/jepegit/cellpy/issues/868
**Labels:** yolo · **Milestone:** v.2.1.2 · **cellpy version:** 2.1.2a4

## Summary

Seven of the registered plot families — every `fullcell_standard_*` — cannot be
plotted through the public collect path. The family declares the transform it
needs, but the object `PlotFamily.transforms()` returns is not the shape
`SummaryOptions.transforms` consumes, so feeding one to the other raises
`TypeError: 'dict' object is not callable`.

`summary.py` applies `transforms` as `frame = transform(frame)` — callables.
`transforms_builder` yields a nested mapping
`{output_column: {(cycle, source_column): fn}}`. There is no documented adapter
between the two, so the family's `mod_01_*` column can never be produced and
`fam.columns(hdr)` can never be satisfied.

## Secondary: a family doesn't declare the options it needs

The two `capacities_*_split_constant_voltage` families work, but only if the
caller happens to pass `SummaryOptions(partition_by_cv=True)` — which nothing in
the family says. Measured on the demo cell: 8/25 families satisfied with
defaults, 12/25 with `partition_by_cv=True`.

An app enumerating `registry.families()` to build a plot menu therefore gets a
list where a third of the entries are unreachable without out-of-band knowledge,
and seven are unreachable at all.

## Wish

1. Have `PlotFamily` expose what a family needs in a form the collector accepts
   — e.g. `family.summary_options()` returning a ready `SummaryOptions`, so
   `collect_summaries(batch, options=family.summary_options(hdr))` just works.
2. Or make `SummaryOptions.transforms` accept the mapping shape
   `transforms_builder` already produces, and document that
   `*_split_constant_voltage` implies `partition_by_cv=True`.

Option 1 would also make the registry genuinely self-describing.
