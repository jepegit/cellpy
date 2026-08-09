# Issue #862: dva_plot(direction='both') does not distinguish the half-cycles visually (ica_plotter does)

Source: https://github.com/jepegit/cellpy/issues/862

## Original issue text

**cellpy version:** 2.1.2a3

## Summary

`ica_plotter` gained a visual distinction for `direction="both"` in #821 — the charge lobe is dashed (`line_dash`), so the two half-cycles are separable at a glance. `dva_plot(direction="both")` overlays both half-cycles too, but draws them **identically**: same colour, same trace name, no dash.

Only the hover tells them apart. On a static export (PNG/SVG/PDF for a report) that information is gone entirely.

## Reproduction

```python
import json, plotly.io as pio
from cellpy.utils.plotutils import dva_plot
from cellpy.utils import example_data

cell = example_data.cellpy_file()
fig = json.loads(pio.to_json(dva_plot(cell, cycles=[1], direction="both", backend="plotly")))
for t in fig["data"]:
    print(t["name"], t["line"], t.get("showlegend"))
```

```
1 {'color': 'rgb(68, 1, 84)', 'width': 1.5} True
1 {'color': 'rgb(68, 1, 84)', 'width': 1.5} False
```

Both traces: same `name`, same `legendgroup`, same colour, `dash` unset. Compare `ica_plotter(..., direction="both")`, which yields `1, charge` / `1, discharge` with `dash='dot'` on one of them.

The hover *is* correct — `customdata[1]` carries `charge`/`discharge` and the template shows it — so this is purely about the visual encoding.

## Why it matters for apps

We're adding a DVA view to [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) next to the existing ICA view. Same "Both" control, same user expectation, but two different behaviours: ICA is readable, DVA looks like a single doubled-back curve. We'll dash the discharge half app-side for now, which is exactly the kind of divergence #821 removed for ICA.

## Suggested fix

Apply the #821 treatment in `dva_plot`: `line_dash` per direction (and ideally `"<cycle>, charge"` / `"<cycle>, discharge"` names, matching `ica_plotter`), so the two families stay consistent with each other.

Happy to send a PR if you'd like.
