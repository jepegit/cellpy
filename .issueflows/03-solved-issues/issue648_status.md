# Issue #648 — Status

- [x] Done

## What's done

- Plan confirmed (direction overlay + shared styling + plotly hover).
- `cellpy/plotting/prepare/ica.py` — `dqdv` / `dvdq` prepare + FigureSpec.
- Registry families `"ica"` / `"dva"`.
- Backend `kind` branches (plotly + matplotlib): one series per `(cycle, direction)`,
  cycle colour, shared linestyle, plotly hover includes direction.
- Public `ica_plot` / `dva_plot` in `plotutils` with `backend=` / deprecated `interactive=`.
- Shared cycle legend policy: `cellpy/plotting/cycle_legend.py`
  (legend if ≤8 cycles, else colorbar; overridable). Wired into ICA/DVA backends.
- Oracle cases + regenerated `figure_specs.json`; `tests/test_ica_plot_prepare.py`,
  `tests/test_cycle_legend.py`.
- Design notes + manual `dev/preview_*.py` scripts.
- Related discovery filed separately: #654 (CV-split summary dead `selector_type`).

## Remaining

- None for #648.
