# Issue #967 — status

- [x] Done

## What's done

- Picked `#967` (`iflow pick 967`). Branch
  `cursor/967-zensical-docs-markers-8d63`.
- Captured original; comments empty (section omitted).
- Plan drafted, then revised: rewrite source docstrings instead of a
  Griffe hook.
- Plan accepted 2026-08-25. `auto_build` started.
- Replaced 317 Sphinx roles in 69 `cellpy/**/*.py` files with markdown
  code spans (last dotted segment).
- Documented the convention in `dev_docs.md`.
- Added `tests/test_no_sphinx_doc_roles.py` (not essential).
- `zensical build --clean`: no leftover `:class:` / `:meth:` / `:func:` in
  `site/` HTML except the convention note in `dev_docs`.
- `uv run pytest -m essential`: 776 passed.

## Remaining work

- None.
