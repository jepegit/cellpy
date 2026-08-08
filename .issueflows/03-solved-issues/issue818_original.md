# Issue #818: In-memory static figure export on the collect/plot path (PNG/SVG/PDF bytes)

Source: https://github.com/jepegit/cellpy/issues/818

## Original issue text

## Problem / context

`collection.plot()` is the right way for an app to get a Plotly figure, but there is no matching collect-level API to turn that figure into PNG / SVG / PDF **bytes**.

`Collection.save(...)` is **data-only** (parquet/csv/json/xlsx). The kaleido helper that exists — `cellpy.utils.plotutils.save_image_files` — lives outside collect, writes to **disk**, spawns a **subprocess** around `fig.write_image`, and prints status to stdout. That fits notebooks/scripts; it does not fit a desktop or FastAPI app that wants `(bytes, media_type)` for a download response (and a clear error when kaleido is missing).

Downstream (cellpy-simple-gui #27) calls `fig.write_image` directly today.

## Spec

Something on the collect / plotting surface, e.g.

```python
collection.to_image(\"svg\")           # -> bytes
# or
fig = collection.plot(...)
cellpy.plotting.write_image(fig, \"pdf\")  # -> bytes, raises if kaleido missing
```

Same formats users expect from kaleido (`png` / `svg` / `pdf`), in-memory, no subprocess or cwd side effects. Optional: `Collection.save(..., formats=(\"svg\",))` that saves the *plot* next to the data — but bytes-first matters more for apps.

## Acceptance criteria

- [ ] Public API returns image bytes (not only a filesystem path).
- [ ] Missing kaleido raises a clear, catchable error (no stdout-only status).
- [ ] Works for figures produced via `collection.plot(...)` / collected families.
- [ ] Docs/example show a minimal download-style usage.


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy ≥2.1.1.post4. Full write-up: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
