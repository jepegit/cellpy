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
| _(none yet)_ | | |
