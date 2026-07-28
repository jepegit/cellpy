# Marimo notebooks in the docs

**Context:** Issue #724 — spike to ship marimo alongside Jupyter tutorials under Zensical.

**Decision (final):** **Do not ship marimo pages in the Zensical docs for now.**
The sample “Hello cellpy (marimo)” page and `dev/render_marimo_notebooks.py`
pipeline were removed. Keep Jupyter’s committed-markdown path.

**Why withdrawn:** `marimo-md-export` flattens `mo.ui.table` to plain Markdown.
Plotly inline scripts break under Material instant navigation. Reactive marimo
islands / Pyodide hang in the docs embed. Client-side stand-ins (Tabulator,
Plotly iframes) work but are no longer “marimo”.

**Revisit when:** Zensical (or a host plugin) supports marimo islands cleanly,
or marimo ships a reliable Python-free static reactive export that fits docs.

**Landing:** docs work continues on **`master`**. The old `v2-docs-stable`
branch is retired — see [`docs-on-master.md`](docs-on-master.md).
