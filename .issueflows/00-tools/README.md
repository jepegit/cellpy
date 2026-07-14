# `00-tools/` — shared helper tools

This folder is the project's **durable toolbox** for issue-flow work. Small
scripts and utilities that are useful across more than one issue live here so
agents (and humans) can reuse them instead of re-writing throwaway helpers each
time.

## When working an issue

- **Check here first.** Before writing a new helper script for an issue, skim
  the index below and the files in this folder — a suitable tool may already
  exist.
- **Contribute back.** If you build something during an issue that could help
  again later (a data-munging script, a checker, a one-off that turned out
  reusable), save it here and add a one-line entry to the index so the next
  agent knows what it does and when to reach for it.
- Keep tools small, self-contained, and runnable through the project's
  documented toolchain (e.g. `uv run 00-tools/<script>.py`).

This README is **not** overwritten by `issue-flow update`, so the index is safe
to grow over time.

## Tool index

<!-- Add one row per tool: name | what it does | when to use it -->

| Tool | What it does | When to use |
| --- | --- | --- |
| `scan_member_usage.py` | AST scan for `Data` / `CellpyCell` `.member` access in given package paths | Stage-0/1 consumer inventory reports (e.g. issue #435) |
| `scan_hardcoded_headers.py` | AST scan for canonical header string literals in column-access contexts | Stage-0 header inventory / migration planning |
| `migrate_prms_calls.py` | Bulk replace `prms.<Section>` → `config.<section>` and add imports | Issue #453 M2 mechanical migration (review arbin/SQL/module-level edge cases manually) |
