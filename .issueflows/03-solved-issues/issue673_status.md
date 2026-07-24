# Issue #673: Iterative fixes: docs cleanup

Interactive `/iflow-fix` session. Fixes recorded below; landed together via `/iflow-close`.

- [x] Done

## Iterative fixes log

- 2026-07-24: Fill `docs/getting_started/index.md` with short intro + links
  matching Getting started `nav` (installation → setup → checkup → basic
  usage → migration). Left `remote_paths.md` / `configuration_reference.md`
  out (other nav sections). Kept existing WIP edits in `docs/index.md`.
- 2026-07-24: Replace Sphinx `{toctree}` + `.ipynb` list in
  `docs/examples/index.md` with markdown links to the rendered `.md`
  tutorial pages (match Tutorials `nav`).
- 2026-07-24: Fill empty Development landing pages —
  `docs/contributing/index.md` and
  `docs/contributing/developers_guide/index.md` — with intro + links
  matching Development / Developer guide `nav`.
- 2026-07-24: Quote Mermaid node labels with parentheses in
  `docs/contributing/developers_guide/dev_cellpy_data_structure.md` so
  the second flowchart renders.
- 2026-07-24: Same Mermaid label quoting in
  `docs/fundamentals/data_structure.md`.
- 2026-07-24: Fill `docs/fundamentals/index.md` with intro + links matching
  Concepts `nav`.
- 2026-07-24: Replace Sphinx MyST `(label)=` anchors with MkDocs
  `{#id}` / HTML `id` in `dev_cellpy_data_structure.md`,
  `installation.md`, and `configuration.md` (stops stray visible text).
- 2026-07-24: Tag untagged Python fences as `python` in
  `dev_loaders_and_instruments.md` and `dev_cellpy_data_structure.md`
  so syntax highlighting applies.
- 2026-07-24: Rewrite outdated
  `docs/contributing/developers_guide/dev_cellpy_packaging_pypi.md` —
  tag-based versioning, GitHub release → CI → trusted publishing,
  `uv build` / build_test; drop broken twine + API-token copy.
- 2026-07-24: Rewrite
  `docs/contributing/developers_guide/dev_conda_package.md` — bot/automerge
  happy path, PyPI-first, pin note, fix `feedstok` typos; manual fork flow
  as fallback.
- 2026-07-24: Expand `docs/contributing/developers_guide/dev_various.md` —
  `uv run pytest` / `-m essential`, when to mark essential, GitHub workflow
  table (`ci.yml`, scheduled, release, benchmarks, docs); fix `unixodbc` typo.
- 2026-07-24: Replace outdated "Adding another config parameter" in
  `dev_various.md` — `cellpy/config/models.py` + regenerate reference;
  `prms` / default conf are not the source of truth.
- 2026-07-24: Strip ANSI from notebook text outputs in
  `dev/render_example_notebooks.py` and re-render Tutorials markdown
  (removed thousands of escape codes from 01/02/06/07/batch pages).
- 2026-07-24: Unblock docs build — convert MyST `:::{note}` in
  `01_loading_data` (+ render-script safety net); keep auto heading
  slugs via `<a id>` instead of `{#id}`; fix broken
  `/docs/getting_started/configuration.md` link in batch tutorial.
- 2026-07-24: Fix sparse `head()` tutorial output — print one joined
  block in notebooks 06/07; coalesce consecutive text `display_data`
  in render script; re-render examples.

## Close

- 2026-07-24: `uv run pytest -m essential` green; `zensical build` reports
  no issues. Moved to solved via `/iflow-close`.
