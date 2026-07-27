# Issue #724 — status

- [x] Done

## What's done

- Plan accepted; `/iflow-build` started (2026-07-26).
- Merged `origin/master` (was 1 behind).
- Added `marimo` + `marimo-md-export` to the `docs` dependency group.
- Sample notebook `docs/examples/marimo/01_hello_cellpy.py` + committed
  `01_hello_cellpy.md` via `dev/render_marimo_notebooks.py`.
- Wired Tutorials nav, `docs/examples/index.md`, `dev_docs.md`, Docs CI path
  filters.
- Ignored marimo session dirs (`__marimo__/` in `.gitignore`).
- Smoke: render OK (~55 KB); `zensical build --clean` → **No issues found**.
- `uv run pytest -m essential`: 628 passed, 1 skipped.
- HISTORY bullet under `[Unreleased]`; design note `marimo-docs.md`.
- PR base: `v2-docs-stable` (docs integration branch).

## Remaining work

- None for this issue. After merge: `/iflow-cleanup`.
