# Issue #651: Complete cli_api extraction for remaining CLI commands (new, serve, setup, â€¦)

Source: https://github.com/jepegit/cellpy/issues/651

## Original issue text

## Goal

Finish the library-first `cli_api` extraction that #568 started. Remaining command logic still lives in `cellpy/cli.py` and is not callable from scripts without shelling out.

Plan of record: [`architecture-plan/cellpy2-cli-redesign-plan.md`](https://github.com/jepegit/cellpy/blob/master/../architecture-plan) Phase 1 (command-by-command). Parent extraction: #568 / PR #586.

## Why

#568 explicitly left these in `cli.py`:

- `setup` (+ `setup migrate`)
- `info`
- `edit`
- `pull`
- `new`
- `serve`

Several are interactive (prompts, cookiecutter, Jupyter). That is fine for a CLI wrapper, but the **core behaviour** should still be reachable as ordinary typed functions with a quiet default â€” same contract as today's `cli_api.convert` / `run_journal`.

## Pattern (especially for `_new`-shaped commands)

Do **not** call `typer.echo` (or `print`) inside the library function. Inject output:

```python
def create_project(..., echo: Echo | None = None) -> Path | None:
    say = _resolve_echo(echo)   # None â†’ silent
    say("Template: â€¦")
```

CLI stays thin:

```python
@cli.command()
def new(...):
    cli_api.create_project(..., echo=typer.echo)
```

When moving a function like `_new`, move its helpers with it (or leave thin CLI-only wrappers):

| Helper | Notes |
|--------|--------|
| `_get_default_template` / `_read_local_templates` | template discovery |
| `_get_author_name` | may echo on failure |
| `_serve` | shared by `serve` and `new --serve` |
| `_run_project` | already delegates to `cli_api.run_project` |

Also align with existing `cli_api` conventions:

- `echo: Optional[Echo] = None` + `_resolve_echo` (quiet by default â€” **not** `echo=print`)
- Prefer returning useful values (`Path` to created project, list of templates, â€¦) instead of only printing
- Interactive pieces (`cookiecutter.prompt.*`, bare `input(...)`, `os.chdir`) either stay documented as interactive-only, get injected (`prompt=` / `confirm=`), or stay in `cli.py` while a non-interactive core moves first

Known footgun while touching `_new`: cookiecutter `ModuleNotFoundError` currently echoes and **continues** (no `return`) â†’ later `NameError`. Fix on the way through.

## Suggested order (from the CLI plan)

1. `info` / `serve` / `edit` â€” small; prove the pattern again
2. `pull` â€” download helpers
3. `new` â€” template registry + cookiecutter (`_new` + helpers)
4. `setup` (+ `migrate`) â€” hardest; coordinate with config Step 5 if still relevant

Each PR: move logic â†’ CLI calls it â†’ tests hit both `cli_api` and the Typer command. No user-visible CLI change.

## Acceptance

- [ ] Each remaining command's logic is importable from `cellpy.cli_api` (or a domain package re-exported there) without a Typer context
- [ ] Library functions are quiet by default; CLI passes `typer.echo` for identical terminal output
- [ ] Helpers needed by moved functions live with them (not stranded as private CLI-only deps)
- [ ] Existing CLI tests still pass; add/extend `tests/test_cli_api.py` for the new surfaces
- [ ] Optional stretch: non-interactive path for `new` when `project` + `experiment` + `no_input` are provided

## Out of scope

- Redesigning templates / replacing cookiecutter
- New CLI flags or UX changes
- Docs "Automating cellpy" recipes (CLI plan Phase 3) â€” follow-up after the moves
