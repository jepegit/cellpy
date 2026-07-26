# Marimo notebooks in the docs

**Context:** Issue #724 — prove marimo can ship alongside Jupyter tutorials under Zensical.

**Decision:** Keep Jupyter’s committed-markdown pipeline. For marimo, sources live in `docs/examples/marimo/*.py` and are exported with `marimo-md-export` via `dev/render_marimo_notebooks.py`; commit the generated `.md`. No Pyodide / live Python in the site.

**Alternatives considered:** Native Zensical marimo plugin (none yet); generate-at-RTD instead of committing (rejected for this spike — match Jupyter); convert existing `.ipynb` set (out of scope).

**Ops:** `uv run --group docs python dev/render_marimo_notebooks.py` then `zensical build`. Keep figures light (base64 size). Ignore `__marimo__/` session dirs.

**Landing:** Docs-only PRs (including this spike) target the long-lived
`v2-docs-stable` branch; merge that into `master` when ready to publish.
