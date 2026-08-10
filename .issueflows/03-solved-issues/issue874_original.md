# Issue #874: resolve_collected_layout_kind accepts any layout string silently — layout='film' draws a line plot

Source: https://github.com/jepegit/cellpy/issues/874

## Original issue text

Found while adding dQ/dV and dV/dQ to a multi-cell "Cycles" pane in [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) (against **cellpy 2.1.2**).

## What happens

`Collection.plot(layout=...)` accepts *any* string. Unknown values fall through `_LAYOUT_TO_METHOD.get(layout, "fig_pr_cell")` to the line renderer, with no error and no warning:

```python
>>> from cellpy.plotting.collected import resolve_collected_layout_kind as r
>>> r(layout="film")
('film', 'line', 'fig_pr_cell')
>>> r(layout="totally_bogus")
('totally_bogus', 'line', 'fig_pr_cell')
>>> r(kind="film")
('per_cell', 'film', 'film')
```

## Why it bit

`film` is a **kind**, not a layout — but it reads like one, it sits in `_METHOD_TO_LAYOUT` alongside `fig_pr_cell` / `fig_pr_cycle`, and `Collection.plot`'s docstring mentions only `layout=` for cycles/ICA. Passing `layout="film"` produced a perfectly plausible figure — same six `scattergl` traces as `per_cell` — so nothing indicated it was wrong. The correct spelling (`kind="film"`) gives `histogram2d`, which is the intended plot.

A silently-wrong figure is worse than a traceback here: the chart looks right, so it ships.

## Suggestions

Any one of these would have caught it:

1. **Validate** — raise on an unrecognised `layout` (and `kind`), listing the accepted values. `totally_bogus` reaching the renderer is a bug regardless of the film question.
2. **Accept `layout="film"`** as an alias for `kind="film"`, since `_METHOD_TO_LAYOUT["film"] = "per_cell"` already implies the mapping exists.
3. **Document `kind=`** in `Collection.plot`'s docstring — it currently names only `layout=` for the cycles/ICA path, so `kind` is easy to miss entirely.

## Environment

cellpy 2.1.2, Python 3.13, Windows.

*(Filed from cellpy-simple-gui, which is built partly to surface this kind of app-facing rough edge. The app now translates `film` → `kind="film"` itself.)*
