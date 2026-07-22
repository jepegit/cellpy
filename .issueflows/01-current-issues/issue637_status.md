# Issue #637 — Status

- [ ] Done

## What's done

- Plan accepted (no-formation stays in builder; layout engine always on; full `render` flag default off; fullcell domains as named helper).

## Remaining work

- Add `cellpy/plotting/backends/{base,plotly}.py` with generic N-row formation layout.
- Thin-wire `PlotlyPlotBuilder._configure_formation_axes`; delete per-N methods.
- Unit tests + design note; keep figure-spec oracle green.
