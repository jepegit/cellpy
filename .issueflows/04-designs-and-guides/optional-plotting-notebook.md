# Optional matplotlib and notebook extras (#937)

## Context

A headless cellpy consumer (plotly + FastAPI) still pulled `matplotlib` and
`ipykernel` (and thus `debugpy` / `jedi`) because both were hard pip
dependencies. ~90 MB in a slim image, unused on the server path.

## Decision

- Required pip install no longer includes `matplotlib` or `ipykernel`.
- Extras: `cellpy[plotting-mpl]` (`matplotlib`) and `cellpy[notebook]`
  (`ipykernel`, `ipython`). `cellpy[all]` includes both.
- Dev / CI (`uv sync`) still gets matplotlib via the `dev` group so tests
  keep the Agg backend.
- Missing matplotlib on `backend="matplotlib"` raises
  `OptionalDependencyError` naming `cellpy[plotting-mpl]`.
- Conda env files still list both packages (full scientific stack).

## Alternatives

- Put matplotlib on the `batch` extra: rejected — `cellpy[batch]` is how
  plotly/kaleido apps install, and they should not pay for matplotlib.
- Keep matplotlib required, drop only ipykernel: rejected — both were in
  the measured 90 MB.
