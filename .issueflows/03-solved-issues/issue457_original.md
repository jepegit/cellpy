# Issue #457 — Stage 1.12: Polars Phase A — de-index raw/summary/journal in place

GitHub: https://github.com/jepegit/cellpy/issues/457
Labels: cellpy2-stage1

## Goal

Polars plan Phase A: dissolve the three contract-level index conventions while
still on pandas — raw no longer indexed by data_point, summary no longer indexed
by cycle_index, journal pages keyed by a filename column — plus a warn-only
index lint. Behavior-preserving in the redundant-state sense (keys stay
available; the frames stop carrying them as indexes).

## Acceptance

- De-indexing done; full suite green (characterization updates deliberate and
  documented); benchmarks within band vs the v1.x baselines.
