# Plan: #818 — in-memory figure bytes (yolo)

## Goal

Public API returns PNG/SVG/PDF **bytes** from a Plotly figure (and from
`Collection.plot`), with a clear `OptionalDependencyError` when kaleido is missing.

## Approach

1. `cellpy.plotting.write_image(fig, fmt, **kwargs) -> bytes` via `fig.to_image`
   (in-process; no subprocess / disk).
2. `Collection.to_image(fmt, **plot_kwargs)` → `plot()` then `write_image`.
3. Raise `OptionalDependencyError` naming `cellpy[batch]` when plotly/kaleido absent.
4. Docs: agents.md download-style snippet. Stretch: plot formats on `save()` — skip.

## Files

- `cellpy/plotting/figures.py` + `__init__.py`
- `cellpy/collect/collection.py`
- `tests/test_plot_image_bytes.py` (monkeypatch; essential)
- `docs/getting_started/agents.md`

## Test strategy

`uv run pytest tests/test_plot_image_bytes.py tests/test_collect.py -q` then essential.
