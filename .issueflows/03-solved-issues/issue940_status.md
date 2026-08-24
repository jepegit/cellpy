# Issue #940 — status

- [x] Done

## What's done

- Picked #940. Branch `cursor/940-update-example-notebooks-0ec2`. Plan accepted.
- Notebook source updates: `01`, `02`, `03`, `05`, `06`, `08`, `09`.
  `07` unchanged (no 1.x leftovers).
- `cellpy.get` docstring examples: `.clp` → `.cellpy`, `nom_cap=` →
  `nominal_capacity=`.
- `docs/examples/` re-rendered; index 1.x caveat updated.
- In-process execute (cwd `examples/`, `MPLBACKEND=Agg`, `--extra batch`):
  `02`, `03`, `05`, `06`, `07`, `08`, `09` all OK. `01` not executed
  (needs local Arbin `.res` files).
- `uv run pytest -m essential`: 830 passed, 1 skipped, 2 xfailed, 1 xpassed.
- No new tests (notebooks + docstring). Essential-review: nothing to mark.
- HISTORY `[Unreleased]` bullet added.

## Remaining work

- None.
