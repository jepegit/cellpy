# Status: #1111 Fails on check

- [x] Done

## What's done

- Soft `required` on `_CheckOutcome`; `_check` warns on soft miss, exit
  follows hard failures only.
- `_check_import_pyodbc` miss paths → `required=False`.
- `tests/test_cli_info.py`: hard-fail fixture retargeted; soft-arbin exit-0 test.
- Design note: `.issueflows/04-designs-and-guides/cli-check-soft-arbin.md`.
- `HISTORY.md` Unreleased bullet.
- `uv run pytest tests/test_cli_info.py -m essential` — 12 passed.
- Essential suite: 947 passed with `--ignore=tests/test_filefinder.py`;
  2 pre-existing `test_filefinder` essential failures (search `*.h5` vs
  `.cellpy` fixtures) unrelated to this change — not fixed here.

## Remaining work

- None for #1111.
