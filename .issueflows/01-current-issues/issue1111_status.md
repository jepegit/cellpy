# Status: #1111 Fails on check

- [ ] Done

## What's done

- Soft `required` on `_CheckOutcome`; `_check` warns on soft miss, exit
  follows hard failures only.
- `_check_import_pyodbc` miss paths → `required=False`.
- `tests/test_cli_info.py`: hard-fail fixture retargeted; soft-arbin exit-0 test.
- Design note: `.issueflows/04-designs-and-guides/cli-check-soft-arbin.md`.
- `uv run pytest tests/test_cli_info.py -m essential` — 12 passed.

## Remaining work

- Close: HISTORY, commit remaining docs if needed, PR, mark Done.
