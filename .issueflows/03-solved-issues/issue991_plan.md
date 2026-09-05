# Issue #991 — plan

## Goal

Give `cellpy new --list` a library form: `cli_api.list_templates()` returning
the templates as data, so a GUI / script / MCP tool does not have to import
`REGISTERED_TEMPLATES` plus the private `_get_default_template()` and
`_read_local_templates()`.

## Approach

- New public `cli_api.list_templates()` returning
  `{"default": str, "registered": {name: location}, "local": {name: location},
  "templatedir": str}`, with locations flattened through the existing
  `_template_location()` helper. No cookiecutter import needed.
- The `list_` branch of `_new()` renders its `ui` output **from that return
  value** and returns it, so printed listing and data cannot drift.
  `cellpy new --list` output stays byte-identical (same labels, same
  `local (<templatedir>)` line); the CLI ignores the return value.

## Files to touch

- `cellpy/cli_api.py` — new `list_templates()` (public section, next to
  `create_project`) plus the rewritten `list_` branch of `_new()`.
- `tests/test_cli_api.py` — one new essential test.

## Test strategy

Test asserts the returned shape (four keys, dict types), that `default` names a
template present in `registered`, and that `create_project(list_=True)` renders
the same data (default label appears in the echoed output).

## Constraints

`_new()`'s list branch previously returned `None`; it now returns the dict.
Update its docstring `Returns:` accordingly.
