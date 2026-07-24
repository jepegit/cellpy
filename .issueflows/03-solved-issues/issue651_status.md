# Status: Issue #651 — Complete cli_api extraction

- [x] Done

## What's done

- Plan accepted (one PR; prompts stay in library; inject `echo` only).
- Branch `651-complete-cli-api-extraction`.
- Moved remaining command logic into `cellpy/cli_api.py`:
  `setup_config`, `migrate_config`, `show_info`, `start_jupyter`, `edit_file`,
  `pull_resources`, `create_project` (+ helpers).
- `cellpy/cli.py` is thin Typer adapters (`echo=typer.echo`).
- Echo binder (`_using_echo` / `_say`) documented in
  `.issueflows/04-designs-and-guides/cli-api-echo-binder.md`.
- Fixed cookiecutter `ModuleNotFoundError` early `return` in `_new`.
- Guarded `edit` against `name is None` before `.lower()`.
- Ruff clean; CLI suites green (`test_cli_api` + `test_cli_surface` +
  `test_cellpy_cmd` → 69 passed).

## Remaining work

- None.
