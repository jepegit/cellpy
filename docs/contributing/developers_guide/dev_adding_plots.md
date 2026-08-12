# Adding plots

How to add a new plot (or plot family) to cellpy's shared plotting stack.

User-facing drawing helpers (`summary_plot`, `cycles_plot`, `raw_plot`,
`cycle_info_plot`, `ica_plot`, `dva_plot`) still live in
`cellpy.utils.plotutils`. The machinery they call lives in
`cellpy.plotting`. Do **not** add new layout logic in `plotutils` or revive
the old `plotutils` / `collectors` forks — extend the prepare → spec → render
path instead.

API reference: [Plotting](../../api/plotting.md).

## Pipeline

Every public plot entry follows the same shape:

```text
cell / frame
  → context (CellContext / FrameContext)
  → registry (PlotFamily)
  → prepare  →  (tidy DataFrame, FigureSpec)
  → get_backend(name).render(frame, spec)
```

`summary_plot` is the reference orchestration (simplified):

```python
from cellpy.plotting.backends import get_backend
from cellpy.plotting.context import from_source
from cellpy.plotting.prepare.summary import prepare as prepare_summary
import cellpy.plotting.registry as plot_registry

family = plot_registry.get(config.y)
ctx = from_source(c)
frame, spec = prepare_summary(ctx, family, config, plot_info=plot_info)
fig = get_backend(resolved_backend).render(frame, spec)
```

| Piece | Package | Role |
|---|---|---|
| Context | `cellpy.plotting.context` | Thin adapter over a `CellpyCell` or a collected frame |
| Registry | `cellpy.plotting.registry` | Named `PlotFamily` records (`y=` menus and non-summary kinds) |
| Spec | `cellpy.plotting.spec` | Frozen `FigureSpec` / `PanelSpec` / `AxisSpec` |
| Prepare | `cellpy.plotting.prepare.*` | Build tidy frame + `FigureSpec` |
| Backends | `cellpy.plotting.backends` | `plotly` and `matplotlib` renderers |

Multi-cell figures use `cellpy.plotting.collected` (`collected_plot`) and
batch cycle-life plots use `cellpy.plotting.batch_summary` — same backend
render contract, different prepare/entry points.

## Where code lives

```
cellpy/plotting/
├── registry.py          # PlotFamily + _register_family
├── spec.py              # FigureSpec / PanelSpec / AxisSpec
├── context.py           # CellContext / FrameContext
├── prepare/
│   ├── summary.py       # summary_plot families
│   ├── curves.py        # cycles_plot
│   ├── raw.py           # raw_plot
│   ├── steps.py         # cycle_info_plot
│   └── ica.py           # ica_plot / dva_plot
├── backends/
│   ├── base.py          # Backend protocol
│   ├── plotly.py
│   └── mpl.py
├── collected.py
└── batch_summary.py
```

Public entry points in `cellpy.utils.plotutils` should stay thin: parse args,
build a small config object, then run context → registry → prepare → render.

## Choose the right extension point

Pick the smallest change that fits:

1. **New `summary_plot(y=...)` family** — same summary tidy frame and summary
   render path; only register a new `PlotFamily` (and update the oracle menu
   expectations if the built-in list changes).
2. **New public plot function** (like `cycles_plot`) — new family with
   `extras["entry_point"]` / `extras["kind"]`, a prepare module that sets
   `spec.extras["kind"]`, backend branches for that kind, and a thin
   `plotutils` wrapper.
3. **Collected / batch** — extend `collected_plot` or `batch_summary_plot`
   rather than inventing a third layout path.

Unknown `summary_plot` `y=` values fail loudly (`ValueError` listing known
names). There is no raw-column fallthrough.

## Add a summary family

Summary families are the `y=` names `summary_plot` accepts. They are registered
in `cellpy/plotting/registry.py` via `_register_family` (called from
`_register_builtin_families` at import time).

Minimal shape:

```python
from cellpy.plotting.registry import PlotFamily, _register_family

_register_family(
    PlotFamily(
        name="my_family",
        description="Short menu text for apps / docs",
        column_builder=lambda hdr: [
            hdr.charge_capacity + "_gravimetric",
            hdr.discharge_capacity + "_gravimetric",
        ],
        mode="gravimetric",  # optional unit/mode hint used by prepare
        # supports_formation=True,
        # supports_cv_split=False,
        # transforms_builder=...,  # optional derived/normalized columns
    )
)
```

Notes:

- Prefer **header-bound** column names through `column_builder(hdr)`
  (`c.schema.summary` / `get_headers_summary()`), not hard-coded 1.x strings.
- `mod_01_<column>` marks a derived series (see `PlotFamily.summary_options`
  and existing full-cell families).
- `_register_family` is provisional for in-tree use in 2.0; apps should not
  rely on it as a stable public plugin API yet.
- Default `entry_point` is `"summary_plot"`. Omit `extras` for summary
  families so they stay on the summary oracle menu.

After adding a built-in summary family, update
`EXPECTED_SUMMARY_FAMILIES` in `tests/test_plotting_registry.py` so the
registry/oracle contract stays explicit. The runtime oracle menu in
`tests/figure_spec_support.py` (`SUMMARY_FAMILIES`) is derived from
`families(entry_point="summary_plot")` and must not be hand-edited.

## Add a non-summary plot (new kind)

Families that are **not** `summary_plot(y=...)` names register with scoped
extras, for example:

```python
PlotFamily(
    name="cycles",
    description="Voltage vs capacity by cycle",
    column_builder=lambda hdr: ["capacity", "potential", "cycle_num"],
    extras={"entry_point": "cycles_plot", "kind": "cycles"},
)
```

Then:

1. **Prepare** — add `cellpy/plotting/prepare/<name>.py` with
   `prepare(ctx, ...) -> (frame, FigureSpec)`. Set
   `spec.extras["kind"]` to the same kind string backends will switch on.
   Export it from `cellpy/plotting/prepare/__init__.py` when it is part of
   the public prepare surface.
2. **Backends** — teach both `PlotlyBackend` and `MatplotlibBackend` to
   handle that `kind` (see the existing `cycles` / `raw` / `cycle_info` /
   `ica` / `dva` branches). Keep layout decisions in the backends (or in
   prepare-produced `FigureSpec` / `extras`), not in `plotutils`.
3. **Public wrapper** — add or extend a function in `cellpy.utils.plotutils`
   that mirrors the `summary_plot` orchestration above.
4. **Registry filter** — keep non-summary families out of the summary menu by
   setting `extras["entry_point"]` to the owning public function name.

## Labels, units, and themes

Reuse shared helpers instead of hard-coding axis text:

- `cellpy.plotting.labels` — `quantity_label` / `units_quantity_label`
- `cellpy.plotting.theme` — plotly templates and colour cycles
- `cellpy.plotting.cycle_legend` — legend vs colorbar policy for cycle colouring
- `cellpy.plotting.figures` — load/save / `write_image` (kaleido / batch extra)

Prefer schema-resolved header names and unit helpers from `cellpy.units`
over literal column strings.

## Tests and the figure oracle

Minimum expectations when you add a plot path:

| Layer | What to cover |
|---|---|
| Registry | Family name, description, `entry_point`, resolved columns |
| Prepare | Returns a tidy frame + `FigureSpec` with the right `kind` / panels |
| Backend | Both `plotly` and `matplotlib` render without raising (mark deps as needed) |
| Public API | Thin wrapper accepts the documented kwargs and returns a figure |

Useful anchors:

- `tests/test_plotting_registry.py` — built-in menu + `_register_family` round-trip
- `tests/figure_spec_support.py` — figure oracle menu (`SUMMARY_FAMILIES`,
  `FigureCase` builders)
- Existing prepare/backend tests under `tests/` for the plot family you are
  mirroring (search for the `kind` or public function name)

Run a focused slice while iterating, for example:

```bash
uv run pytest tests/test_plotting_registry.py -m essential
```

Plotting tests that draw figures should run under `MPLBACKEND=Agg` (CI already
sets this where needed). Prefer extending the oracle/menu helpers over
one-off snapshot tests when the change is “another family on the same path”.

## Checklist

- [ ] Chose summary family vs new `kind` / entry point
- [ ] Registered `PlotFamily` (header-bound columns; correct `extras`)
- [ ] Prepare returns `(frame, FigureSpec)` and sets `spec.extras["kind"]` when needed
- [ ] Both backends handle the path (or clearly share the summary branch)
- [ ] Public `plotutils` (or collected/batch) wrapper stays orchestration-only
- [ ] Registry/oracle expectations updated for new built-in summary names
- [ ] Tests cover registry + prepare/render smoke for the new path
- [ ] User docs / API notes updated if the public surface changed
