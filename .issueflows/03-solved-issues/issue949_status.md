# Issue #949 — status

- [x] Done

Re-opened 2026-09-23 and closed. First pass (2.1.4) only picked IR *if* the
summary had columns. A normal `cellpy.get` / `batch.load` used
`make_summary()` with `find_ir=False`, so `b.plot(ir=True)` skipped the panel.

## What's done

- First pass: `_select_ir_column` pick/fallback + plotter tests (2.1.4).
- This pass: `cellpy.get(..., auto_summary=True)` defaults `find_ir=True`;
  batch recalc uses `make_summary(find_ir=True)`. Skip warning names the remake.
- Tests: get includes IR; `summary_kwargs={"find_ir": False}` still skips;
  `Batch.plot` after get shows IR (charge and discharge). Incremental oracle
  aligned (`find_ir=True`). Runner stub accepts `**kwargs`.
- Docs: `agents.md`, `AGENTS.md`, `plotting-batch-summary.md`, HISTORY.

## Remaining work

None.
