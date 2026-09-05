# Issue #991 — status

- [x] Done

## What's done

- Added public `cli_api.list_templates()` returning
  `{"default", "registered", "local", "templatedir"}` — locations flattened
  through `_template_location()`, no cookiecutter import needed.
- The `list_` branch of `_new()` now renders its output from that dict and
  returns it (so `create_project(list_=True)` hands the data back too);
  `cellpy new --list` output verified unchanged.
- Two essential tests in `tests/test_cli_api.py` (shape contract + the printed
  listing being rendered from the data), registered in
  `04-designs-and-guides/test-registry.md`.

## Remaining work

None.
