# Test registry

Living index of notable tests for the optional **essential tests** paradigm
(see [essential-tests.md](./essential-tests.md)). Seeded once by issue-flow;
**never overwritten** on `issue-flow update` — agents and humans grow the table.

When `[issueflow].essential_tests` is true, `/iflow-close` / `/iflow-build`
(per `essential_review`) should add or update rows for tests **touched by the
current issue**. `/iflow-doctor` may audit the whole suite against this table.

| Test (node id or path::name) | Essential? | Always? | Code under test | Issue | Notes / demote? |
| --- | --- | --- | --- | --- | --- |
| tests/test_batch_v3_runner.py::test_auto_uses_existing_cellpy_without_raw | yes | yes | batch.runner._get_kwargs AUTO | #825 | prefer local .cellpy |
| tests/test_batch_v3_runner.py::test_auto_falls_back_to_raw_when_cellpy_missing | yes | yes | batch.runner._get_kwargs AUTO | #825 | |
| tests/test_batch_v3_runner.py::test_newest_passes_both_paths | yes | yes | batch.runner._get_kwargs NEWEST | #825 | freshness check |
| tests/test_batch_v3_runner.py::test_recalc_remakes_steps_and_summary | yes | yes | batch.runner.load_cell recalc | #825 | force_recalc |
| tests/test_batch_v3_runner.py::test_no_recalc_skips_remake | yes | yes | batch.runner.load_cell | #825 | |
| tests/test_batch.py::test_persist_skips_rewrite_when_loaded_from_cellpy | yes | yes | batch.facade._persist_cells | #825 | skip redundant save |
| tests/test_batch.py::test_persist_rewrites_when_loaded_from_raw | yes | yes | batch.facade._persist_cells | #825 | |

**Columns**

- **Essential?** — currently marked with the configured pytest marker.
- **Always?** — should stay essential even after the originating issue closes.
- **Code under test** — modules/symbols (graphify can help).
- **Issue** — GitHub number that introduced or last reviewed the test.
- **Notes / demote?** — why essential, or candidate for demotion.
