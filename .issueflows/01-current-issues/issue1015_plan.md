# Issue #1015 — plan

## Goal

API reference pages link every documented object to its source on GitHub.
Beyond the ask: iterate on the docs from a user's point of view (battery
scientist with limited Python), one PR per iteration.

## Iteration 1 (this PR): source links

mkdocstrings-python has no built-in GitHub link, only inline `show_source`.
Override the `source` block (functions, classes) and append to the `docstring`
block (modules) with a `docs/.templates/python/material/` template set that
renders `View source on GitHub` → `<repo>/blob/master/<path>#L<start>-L<end>`
from Griffe's `relative_filepath` / `lineno` / `endlineno`. Base URL comes from
`extra.source_url_base` in `zensical.toml`; templates wired via
`custom_templates`. Dot-prefixed folder so zensical does not copy it into
`site/` (`exclude_docs` is not honoured).

## Later iterations (not started)

Candidate topics, each its own branch/PR: troubleshooting page (common
errors), "which loader for my tester" table, units/mass/nominal-capacity
FAQ, glossary of columns (`c.schema`), batch quick-start for non-programmers,
plotting cookbook, saving/exporting to Excel/CSV, configuration walkthrough.
