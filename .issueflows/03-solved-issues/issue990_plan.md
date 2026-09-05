# Issue #990 — plan

## Goal

`cli_api.create_project(..., no_input=True)` must not prompt when the project
directory does not exist, so `cellpy new` is scriptable (GUI / MCP / script).

## Approach

In `_new()` (`cellpy/cli_api.py`, the `if project_dir:` branch), guard the
`cookiecutter.prompt.read_user_yes_no("… does not exist. Create?")` call with
`no_input`:

```python
if no_input or cookiecutter.prompt.read_user_yes_no(...):
```

Short-circuit means `read_user_yes_no` is never called when `no_input` is true.
The prompt default is already `"yes"`, so interactive behaviour is unchanged.

## Files to touch

- `cellpy/cli_api.py` — one condition in `_new()`.
- `tests/test_cli_api.py` — one new essential test.

## Test strategy

New test following the monkeypatch pattern of
`test_create_project_returns_when_cookiecutter_missing`: replace
`cookiecutter.prompt.read_user_yes_no` (and the other prompt helpers) with a
function that raises, stub `cookiecutter.main.cookiecutter`, call
`create_project(..., no_input=True)` with a missing project dir, and assert the
directory was created and `no_input=True` reached cookiecutter.

## Constraints

Interactive (`no_input=False`) path untouched.
