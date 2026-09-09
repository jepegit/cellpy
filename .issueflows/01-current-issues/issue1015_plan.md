# Issue #1015 — plan

## Goal

API reference pages let the reader see the code behind each documented
object. Beyond the ask: iterate on the docs from a user's point of view
(battery scientist with limited Python), one PR per iteration.

## Iteration 1 (this PR): inline source

Set mkdocstrings-python `show_source = true` in `zensical.toml`. Every class
and function gets a collapsible "Source code in `<file>`" block with line
numbers. A GitHub-link variant (template overrides) was prototyped and
dropped: inline source answers the need without custom templates.

## Later iterations (not started)

Candidate topics, each its own branch/PR: troubleshooting page (common
errors), "which loader for my tester" table, units/mass/nominal-capacity
FAQ, glossary of columns (`c.schema`), batch quick-start for non-programmers,
plotting cookbook, saving/exporting to Excel/CSV, configuration walkthrough.
