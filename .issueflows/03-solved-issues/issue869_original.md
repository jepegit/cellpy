# Issue #869 — Top-level examples/ notebooks still use removed 1.x API

**Source:** https://github.com/jepegit/cellpy/issues/869
**Labels:** yolo · **Milestone:** v.2.1.2 · Refs #866

## Context

`docs/examples/index.md` points readers at the top-level `examples/` folder as
the place to download the tutorial notebooks. That tree is a **second, older
copy** of the tutorials, separate from the `docs/examples/` copies that are
rendered into the documentation site.

While doing the #866 release-prep docs sweep, the two `docs/examples/` tutorials
were brought up to the 2.1 API, executed, and re-rendered. The top-level
`examples/` copies were not touched and still use API removed in 2.1. They had
already diverged before that work.

## Findings

Grepping the top-level copies for removed API (`dqdv_cycle`, `dqdv_np`,
`prms.Paths`, `Batch*Collector`): `examples/04_incremental_capacity_analysis.ipynb`
9 hits, `examples/cellpy batch utility/cellpy_batch_processing.ipynb` 11 hits.
There are 11 notebooks in that tree, so others may be affected too.

## Decision needed

The duplication is the underlying problem. Options, roughly in order of
preference in the issue text: deduplicate onto the `docs/examples/` copies, fix
the top-level copies in place, or deprecate them with a 1.x banner.

## Acceptance criteria

- No notebook that the docs link to as a download uses removed API.
- Only one maintained copy of each tutorial, or an explicit, documented reason
  for two.
- `docs/examples/index.md` links to whatever the maintained location ends up
  being.

## Refinement from the maintainer (during this cycle)

Deduplicate **the other way round** from the issue's first option: keep the
notebooks in the top-level `examples/` folder as the single maintained copy, and
let `docs/examples/` hold only the generated markdown and figures.
