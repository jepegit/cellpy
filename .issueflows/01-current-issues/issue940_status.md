# Issue #940 — status

- [ ] Done

## What's done

- Picked #940. Branch `cursor/940-update-example-notebooks-0ec2`. Plan accepted.
- Notebook source updates: `01`, `02`, `03`, `05`, `06`, `08`, `09`.
  `07` left unchanged (no 1.x leftovers).
- `cellpy.get` docstring examples: `.clp` → `.cellpy`, `nom_cap=` →
  `nominal_capacity=`.
- `docs/examples/index.md` 1.x caveat updated.

## Remaining work

- Re-render `docs/examples/` after notebook edits.
- Execute runnable notebooks (`03`, `06`, `07`, `08`, `09`; `02` via
  `example_data` fallback). `01` / `05` need local `20210210_FC.h5`.
- `uv run pytest -m essential`.

