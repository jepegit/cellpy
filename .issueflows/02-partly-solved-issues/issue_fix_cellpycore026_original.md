# Iterative fixes: New cellpy-core release

Source: local `/iflow-fix` session (GitHub issue create blocked in this Cloud
Agent environment — `gh` is read-only). Session name: New cellpy-core release.

## Original issue text

Interactive `/iflow-fix` session whose individual fixes are recorded in the
status markdown and landed together via `/iflow-close`.

**First fix (from the invoking message):** Cellpy next: bump the `cellpycore`
pin to the new PyPI release `0.2.6`, and drop the strict xfails on
`test_empty_tail_is_noop` (core#147) and
`test_gap_append_mid_step_equals_full_load` (core#148).
