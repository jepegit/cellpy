# Status: #816 — mixed group_it averaging

- [x] Done

## What's done

- Partition multi vs singleton groups in `collect_summaries`; average multis; singletons → long schema with null `std`.
- `grouped=True` when any multi averaged; all-singleton still wide / False.
- Essential test `test_group_it_averages_multi_when_mixed_with_singleton`.
- Stretch (long vs wide facet subplot ids): left out of this pass.

## Remaining work

- None for core acceptance.
