# CLI API echo binder (`_using_echo` / `_say`)

**Issue:** #651  
**Context:** Finishing the Phase-1 move of remaining CLI command bodies into
`cellpy.cli_api` without threading an `echo` callable through every private
helper (`_check_import_pyodbc`, `_update_paths`, `_new`, …).

**Decision:** Public facades still take `echo: Optional[Echo] = None` and are
quiet by default (same as `convert` / `run_journal`). Inside a call they bind
the resolved echo on a `contextvars.ContextVar` via `_using_echo`; private
helpers report with `_say(...)`.

**Alternatives considered:**

- Thread `echo=` / `say=` through every helper — correct but a huge, noisy
  mechanical diff for setup/pull/new.
- Keep `typer.echo` in library code — breaks the quiet-by-default contract.

**Note:** Colour kwargs formerly passed to `typer.echo(..., color="red")` are
ignored by `_say` (Typer colour was already optional decoration).
