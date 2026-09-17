# Issue #1023: further improvements of docs

Source: https://github.com/jepegit/cellpy/issues/1023

## Original issue text

## Context

The cellpy 2.x docs have a solid skeleton (Getting started → Tutorials →
How-to guides → Concepts → Reference), but they are still written mostly from
the *inside out*: they describe what cellpy has, rather than answering the
questions a user actually arrives with.

The typical cellpy user is a **battery scientist with good electrochemistry
knowledge and limited Python experience**. When that person hits trouble —
a file will not load, capacities look wrong, the units are not what they
expected, they do not know which column holds what — there is currently no
page in the docs that meets them there.

Concrete gaps found in a first pass:

- **No troubleshooting / FAQ page at all.** Nothing indexed by error message
  or symptom ("`NotImplementedError`", "no cycles found", "capacity is zero",
  "cannot read `.res` on Linux").
- **No glossary and no units page.** Nothing that maps battery-science
  vocabulary onto cellpy names, and nothing that states plainly what unit a
  mass, capacity, or current is in, or how to change it.
- **No CLI reference.** The `cellpy` command-line tool is used in setup and
  checkup pages, but its subcommands are not documented anywhere.
- **No task index / cookbook.** A user who knows *what* they want ("plot cycle
  life", "export to Excel for Origin", "get areal capacity") has to guess
  which tutorial contains it.
- **Column-level reference is thin.** `fundamentals/data_structure.md`
  explains the shapes but not what each column means or its unit.
- **Discoverability.** Several good answers already exist in the docs but are
  buried inside long tutorials with no entry point from the navigation.

## Goal

Iteratively improve the documentation by repeatedly role-playing a cellpy
user who runs into trouble — mostly the limited-Python / strong-science
persona, but also occasionally a complete newcomer and an experienced
Python developer — and then fixing whatever the docs failed to answer.

## Approach

A series of small, focused pull requests. Each iteration:

1. Adopt a specific user persona and a specific realistic problem.
2. Try to answer it using only the published docs.
3. Write or restructure whatever was missing or unfindable.
4. Wire the new material into `zensical.toml` navigation and cross-link it
   from the pages the user would actually be on.
5. Green CI (`essential`, `full`, and the `Docs` link-check build), then merge.

## Acceptance criteria

- [ ] Each iteration lands as its own merged PR with green CI.
- [ ] The docs build stays link-clean (the `Docs` workflow fails on any
      broken link or missing anchor).
- [ ] New pages are reachable from `zensical.toml` navigation, not orphaned.
- [ ] Content is verified against the actual code, not assumed — every code
      snippet and every option name checked against the source or run.
- [ ] Writing stays at the level of a scientist who is not a programmer:
      concrete, task-first, minimal jargon, no unexplained Python idioms.

## Comments (curated summary)

- **Additional tasks**:
  - Tutorial-notebook pass: `examples/*.ipynb` (rendered into docs; different workflow than the hand-written pages).
  - Glossary of battery-science terms as cellpy spells them.
  - Experienced-Python persona pass (typing, extending, plugin surface) — the first ten iterations under-served this reader.
- **Clarifications / constraints**:
  - Ten iterations already shipped as separate PRs (#1024–#1035). Do not redo `troubleshooting.md`, `guides/units.md`, `guides/plotting.md`, `guides/batch_database.md`, `reference/cli.md`, `guides/exporting.md`, `reference/summary_columns.md`, `guides/step_table.md`, `getting_started/first_hour.md`, or `how_do_i.md`.
  - Issue stays open; this capture is the next pass, not a restart of the first-pass gap list.
  - Code bugs found while writing docs were filed separately (#1026, #1028) — out of scope here.
  - Every snippet must be executed against bundled example data (and the example database for batch pages), not written from source and hoped for.
- **Superseded / retracted**:
  - Original first-pass gaps (no troubleshooting, no units page, no CLI reference, no task index, thin column reference) are already filled by those ten PRs.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-09-09._
