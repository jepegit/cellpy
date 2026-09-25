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
  - Tutorial-notebook pass: the pages under `docs/examples/` are rendered from `examples/*.ipynb` via `dev/render_example_notebooks.py` — different workflow from the hand-written pages in #1024–#1035.
  - Experienced-Python pass later (typing, extending, plugin surface); those ten iterations deliberately under-served that persona.
- **Clarifications / constraints**:
  - Iterations 1–10 already shipped (#1024–#1035): troubleshooting, units, plotting, batch database, CLI, exporting, summary columns, step table, first hour, how-do-I.
  - Iteration 11 (glossary) also shipped on this open issue (`docs/fundamentals/glossary.md`); do not redo it.
  - Bugs found while writing those pages were fixed in-docs or filed separately (#1026, #1028).
  - Issue stays open; each iteration is its own PR.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-09-09._

## Iteration 13 scope (comment 2026-09-23)

A usability review of the published docs was posted on the issue
(https://github.com/jepegit/cellpy/issues/1023#issuecomment-5802200750) and
committed as
[docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md).
Iteration 13 implements it.
