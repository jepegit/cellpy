# Issue #1193 — status

- [x] Done

## What's done

- Charge and Discharge buttons hide that direction on a summary plot, including spread bands. A second click shows it again. Coulombic efficiency and a lone direction stay out of the buttons.
- Series traces share one legend group, so an experiment click hides charge and discharge together.
- `legend_replacer` stores the direction token on `meta` before it renames the trace.
- Essential suite: 1087 passed. `PLOTLY_RENDERER=json` so `fig.show()` did not wait on a browser.

## Remaining work

- None.
