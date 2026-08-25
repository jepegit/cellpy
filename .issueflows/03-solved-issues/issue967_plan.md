# Issue #967 — plan

## Goal

Stop the built Zensical API pages from showing raw Sphinx roles (`:class:`,
`:meth:`, `:func:`, …) as literal text. Those markers should render as ordinary
code spans (the target name, no role prefix).

## Constraints

- Docs live on `master` and are built by Zensical + mkdocstrings/Griffe
  (`docs-on-master.md`, `dev_docs.md`). `docstring_style = "google"` stays.
  Switching to `sphinx` would break Google `Args` / `Returns` sections.
- Source of truth is the docstring text. Rewrite it; do not add a build-time
  Griffe/markdown hook that leaves Sphinx markup in the library.
- Same replacement rule as the discarded hook: role → markdown code span of
  the last dotted segment (strip a leading `~`). No Autorefs links in this
  issue (a missed inventory path would become a leftover `[text][id]`).
- No new dependency. No new durable converter module. A one-shot rewrite in
  the PR is enough; a small grep test prevents recurrence.
- No roles in `docs/**/*.md` — this is an API-docstring problem only.

### Prior art

- Toolbox: none (no docs-role helper).
- Graph: `graphify-out/` absent.
- Grep: roles `class` / `meth` / `func` / `mod` / `attr` / `data` in 69
  modules (~300 hits). Heaviest: `cellpy/collect/collector.py`,
  `cellpy/readers/cellreader.py`, `cellpy/batch/facade.py`.
- Config: `zensical.toml` already sets `docstring_style = "google"`. Official
  `griffe-sphinx` is unrelated (`#:` attribute comments only).
- `dev_docs.md` already says Google-style; it does not yet ban Sphinx roles.

### Why rewrite (not a Griffe hook)

The first draft avoided touching 69 library files. That was the wrong
trade-off: a hook is permanent machinery for a one-time markup cleanup,
`help()` / source still show `:class:`, and the project already documents
Google + markdown. A mechanical source rewrite matches the stack and needs
no `zensical.toml` / CI path-filter wiring.

## Approach

1. Replace Sphinx interpreted-text roles in `cellpy/**/*.py` (docstrings and
   module docs; the pattern does not appear in `docs/`):

   | Source | Becomes |
   | --- | --- |
   | `:class:`Collection`` | `` `Collection` `` |
   | `:class:`~cellpy.collect.collection.Collection`` | `` `Collection` `` |
   | `:func:`cellpy.collect.collect_summaries`` | `` `collect_summaries` `` |
   | `:meth:`plot`` | `` `plot` `` |

   Roles: `class|meth|func|mod|attr|data|exc|obj|paramref`.

2. Run the replace from a short-lived script (stdlib `re` over the 69 files).
   Do not commit the script unless it earns a `00-tools/` row; prefer deleting
   it after the rewrite.

3. Spot-check a few dense files (`collector.py`, `cellreader.py`, `facade.py`)
   so we did not turn an already-backticked example or a non-docstring string.

4. Note in `dev_docs.md` (Doc-strings): do not use Sphinx roles; write
   markdown `` `Name` `` (or ``[`Name`][path]`` if you want a cross-ref).

5. Add `tests/test_no_sphinx_doc_roles.py`: walk `cellpy/**/*.py` and fail on
   leftover `:role:`…`` markers. Not `@pytest.mark.essential`.

## Files to touch

- `cellpy/**/*.py` — mechanical docstring rewrite (69 files today).
- `docs/contributing/developers_guide/dev_docs.md` — convention note.
- `tests/test_no_sphinx_doc_roles.py` (new) — recurrence guard.

## Test strategy

- `uv run pytest tests/test_no_sphinx_doc_roles.py`
- Docs build: `uv run --group docs zensical build --clean`, then grep `site/`
  HTML for leftover `:class:` / `:meth:` / `:func:` / `:mod:` / `:attr:` /
  `:data:`. Expect zero on rendered API pages (especially `site/api/collect/`).
- `uv run pytest -m essential` at close (no expected change).

## Open questions

None that block coding. Still out of scope: Autorefs links.
