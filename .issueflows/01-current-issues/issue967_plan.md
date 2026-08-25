# Issue #967 — plan

## Goal

Stop the built Zensical API pages from showing raw Sphinx roles (`:class:`,
`:meth:`, `:func:`, …) as literal text. Those markers should render as ordinary
code spans (the target name, no role prefix).

## Constraints

- Docs live on `master` and are built by Zensical + mkdocstrings/Griffe
  (`docs-on-master.md`, `dev_docs.md`). `docstring_style = "google"` stays.
  Switching to `sphinx` would break Google `Args` / `Returns` sections.
- The docs CI / RTD build is `uvx --with mkdocstrings-python zensical` (no
  cellpy import). Any converter must be a repo-local file the build can load
  from the checkout — no new PyPI dependency.
- Do not rewrite ~300 role occurrences across 69 `cellpy/**/*.py` files. That
  is a noisy library diff and does not stop the next Sphinx-style docstring
  from leaking.
- `show_source` is already `false`, so the HTML leak is from rendered
  docstrings, not from source blocks.
- No roles in `docs/**/*.md` — this is an API-docstring problem only.

### Prior art

- Toolbox: none (no docs-role helper).
- Graph: `graphify-out/` absent.
- Grep: roles `class` / `meth` / `func` / `mod` / `attr` / `data` in 69
  modules. Heaviest: `cellpy/collect/collector.py`, `cellpy/readers/cellreader.py`,
  `cellpy/batch/facade.py`.
- Config: `zensical.toml` `[project.plugins.mkdocstrings.handlers.python.options]`
  already sets `docstring_style = "google"`. Official `griffe-sphinx` is
  unrelated (it only lifts `#:` attribute comments).
- Convention already documented in `docs/contributing/developers_guide/dev_docs.md`:
  Google-style docstrings. It does not mention Sphinx roles or markdown
  cross-refs.

## Approach

Add a tiny Griffe extension (one module under `dev/`) that rewrites Sphinx
interpreted-text roles in each object's docstring **before** mkdocstrings
renders them:

| Source | Becomes |
| --- | --- |
| `:class:`Collection`` | `` `Collection` `` |
| `:class:`~cellpy.collect.collection.Collection`` | `` `Collection` `` |
| `:func:`cellpy.collect.collect_summaries`` | `` `collect_summaries` `` |
| `:meth:`plot`` | `` `plot` `` |

Rules:

1. Match `:role:`target`` for `class|meth|func|mod|attr|data|exc|obj|paramref`.
2. Strip a leading `~` (Sphinx short-name flag).
3. Display the last dotted segment as a markdown code span.
4. Do **not** emit Autorefs links in this issue. A missed inventory path would
   become a broken `[text][id]` leftover, which is worse than a code span.
   Code span is the “nicer” the issue asks for.

Wire it in `zensical.toml` under the python handler `extensions` list
(Zensical’s mkdocstrings plugin accepts the same handler options as MkDocs).
Point at the local module path so `uvx` / RTD still see it from the checkout.

Note in `dev_docs.md` (Doc-strings section): leftover Sphinx roles are stripped
at build time; prefer markdown `` `Name` `` (or ``[`Name`][path]``) in new
docstrings.

Add the new `dev/` path to `.github/workflows/docs.yml` `paths:` filters so a
converter-only change still runs the docs job. `.readthedocs.yaml` needs no
extra install.

## Files to touch

- `dev/sphinx_doc_roles.py` (new) — Griffe extension + the regex helper (kept
  importable so tests can hit it without a docs build).
- `zensical.toml` — register the extension on the python handler.
- `docs/contributing/developers_guide/dev_docs.md` — one short convention note.
- `.github/workflows/docs.yml` — watch the new `dev/` file.
- `tests/test_sphinx_doc_roles.py` (new) — regex cases for the shapes above.

## Test strategy

- New unit tests: `uv run pytest tests/test_sphinx_doc_roles.py` (no
  `@pytest.mark.essential` — this is docs chrome, not a merge-gate oracle).
- Docs build: `uv run --group docs zensical build --clean`, then grep `site/`
  HTML for leftover `:class:`, `:meth:`, `:func:`, `:mod:`, `:attr:`, `:data:`.
  Expect zero hits in rendered pages (especially `site/api/collect/`).
- `uv run pytest -m essential` once at close (no expected change).

## Open questions

None that block coding. Two explicit non-goals (say so if you want them in
scope):

- Rewriting source docstrings to markdown cross-refs.
- Turning roles into Autorefs links (follow-up if code spans are not enough).
