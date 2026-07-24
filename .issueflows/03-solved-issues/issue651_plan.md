# Plan: Issue #651 — Complete `cli_api` extraction

## Goal

Move the remaining CLI command logic (`info`, `serve`, `edit`, `pull`, `new`,
`setup` + `migrate`) out of [`cellpy/cli.py`](cellpy/cli.py) into
[`cellpy/cli_api.py`](cellpy/cli_api.py) so scripts can call the same behaviour
without a Typer context. CLI stays a thin adapter (`echo=typer.echo`). No
user-visible flag/UX changes.

## Constraints

- Behaviour-preserving move (CLI plan Phase 1). Exception already named in the
  issue: fix `_new`'s cookiecutter `ModuleNotFoundError` path (echo-then-continue
  → `NameError`); early `return` after the install hint.
- Quiet by default: `echo: Optional[Echo] = None` + `_resolve_echo`. Never
  hard-code `typer.echo` / `print` as the library default (clean
  `_create_dir` when setup moves — it still calls `typer.echo` today).
- Keep Typer annotations and command registration in `cli.py`. Do **not** split
  into `cellpy/cli/` package or `cli_api/` package in this issue (that is a
  later layout step in the CLI plan).
- Out of scope: template redesign, new flags, "Automating cellpy" docs (Phase 3).
- Existing CLI smoke in [`tests/test_cellpy_cmd.py`](tests/test_cellpy_cmd.py)
  and surface snapshot in [`tests/test_cli_surface.py`](tests/test_cli_surface.py)
  must stay green.

### Prior art

- [`cellpy/cli_api.py`](cellpy/cli_api.py) — pattern to **mirror**: `Echo`,
  `_resolve_echo`, `convert`, `run_journal` / `run_journals` / `run_from_db` /
  `run_project`, `list_journals`, `open_db_editor` (#568 / PR #586).
- [`tests/test_cli_api.py`](tests/test_cli_api.py) — assert importability,
  quiet-by-default, return values; CliRunner smoke that CLI still speaks.
- [`architecture-plan/cellpy2-cli-redesign-plan.md`](../architecture-plan/cellpy2-cli-redesign-plan.md)
  § Phase 1 order (easy → hard). `run` / `convert` already done.
- Toolbox: nothing CLI-related in `.issueflows/00-tools/`.
- Graph: no `cli_api` hits in `GRAPH_REPORT.md` — grep-only was enough.

## Approach

Extract in this order (same as the issue / CLI plan), committing per command
so review stays readable:

1. **`info`** — move `_version`, `_configloc`, `_envloc`, `_dump_params`,
   `_dump_config_resolved`, and the `_check*` stack used by `--check` into
   `cli_api` (names like `show_version`, `config_path`, `diagnose` / keep
   private helpers with `_` if they are only for info). Public facade returns
   useful values where cheap (e.g. config `Path`); diagnose may keep echo-driven
   reporting like today.
2. **`serve`** — `start_jupyter(lab=…, directory=…, executable=…, echo=…)`.
   Keep `os.chdir` behaviour documented; resolve `home` / `here` / default
   notebookdir in the library function (CLI only passes argv).
3. **`edit`** — resolve target file + launch editor via subprocess; reuse
   `open_db_editor` for `db`. Guard `name is None` before `.lower()` if the
   current path can NPE (fix only if the move would otherwise preserve a
   crash on `cellpy edit` with no args — verify against existing tests first).
4. **`pull`** — move `_pull`, download/clone helpers
   (`_download_g_blob`, `_parse_g_*`, `_pull_tests`, `_pull_examples`, …).
   Stay in `cli_api` for this issue (do not invent `example_data` relocation).
5. **`new`** — move `_new` + `_get_default_template`, `_read_local_templates`,
   `_get_author_name`. Share `_serve` / `run_project` with serve/run. Inject
   `echo=`. Cookiecutter prompts may remain interactive inside the library for
   now (document); stretch: when `project` + `experiment` + `no_input` are set,
   take the non-interactive path without prompts. **Fix** the missing-cookiecutter
   early return.
6. **`setup` (+ `migrate`)** — largest block. Move write/migrate/folder helpers
   and silent/dry-run paths first; interactive `_ask_about_*` either:
   - stay callable from library with injected `prompt=` / `confirm=` defaults
     that use `input`, or
   - remain in `cli.py` while silent `setup_config(...)` / `migrate_config(...)`
     live in `cli_api`.
   Prefer the second only if the first blows the diff; default attempt is
   **full move with `echo` + optional prompt callables**, matching the CLI plan's
   SilentPrompt idea without introducing a new protocol module unless needed.

After each move: Typer command body becomes parse → `cli_api.*(…, echo=typer.echo)`.

Extend `test_every_extracted_command_is_importable` and add focused
`test_cli_api` cases (quiet default + one return-value or spy per command).
Rely on existing `test_cellpy_cmd` for CLI parity.

## Files to touch

| Path | Change |
|------|--------|
| [`cellpy/cli_api.py`](cellpy/cli_api.py) | Add `info` / `serve` / `edit` / `pull` / `new` / `setup` (+ helpers); fix `_create_dir` echo |
| [`cellpy/cli.py`](cellpy/cli.py) | Thin each command to call `cli_api`; drop moved helpers |
| [`tests/test_cli_api.py`](tests/test_cli_api.py) | Importability list + new unit coverage |
| [`tests/test_cellpy_cmd.py`](tests/test_cellpy_cmd.py) | Only if a move breaks an assumption; prefer keep as-is |

No new modules unless a single file becomes unreadable (>~1.5k lines of *new*
logic); prefer one `cli_api.py` growth matching #568.

## Test strategy

```bash
uv run pytest tests/test_cli_api.py tests/test_cli_surface.py tests/test_cellpy_cmd.py -m essential
uv run pytest tests/test_cli_api.py tests/test_cellpy_cmd.py   # broader CLI if needed
```

New tests: quiet-by-default for at least one function per extracted command;
`new` missing-cookiecutter returns without raising; setup silent/dry-run still
creates expected files (existing tests already cover much of this via CLI).

## Open questions

Resolved 2026-07-24 (plan accepted):

1. **PR shape — A.** One PR, ordered commits (info → serve → edit → pull → new → setup).
2. **Interactive prompts — keep in library.** `input` / `cookiecutter.prompt`
   stay inside `cli_api` for parity; inject `echo` only. Injectable
   `prompt=`/`confirm=` only where silent paths or existing tests already need them.
