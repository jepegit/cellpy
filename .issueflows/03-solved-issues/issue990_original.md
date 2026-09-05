# Issue #990: cellpy new: honour no_input when the project directory does not exist

Source: https://github.com/jepegit/cellpy/issues/990

## Original issue text

`cli_api.create_project(..., no_input=True)` is documented as "accept defaults
if True (only valid when providing project_dir and session_id)", but it still
prompts, so `cellpy new` cannot be driven from a script, a GUI, or an MCP tool.

When the project directory does not exist, `cellpy/cli_api.py:1601` calls:

```python
if cookiecutter.prompt.read_user_yes_no(f"{project_dir} does not exist. Create?", "yes"):
    os.mkdir(selected_project_dir)
```

unconditionally — outside the `no_input` guard. A caller with no stdin does not
get a usable failure either; it raises `ValueError: I/O operation on closed
file`.

Reproduce:

```python
import sys
from cellpy import cli_api
sys.stdin.close()
cli_api.create_project(None, directory="/tmp/x", project="demo",
                       experiment="exp001", no_input=True)
# mcp_demo does not exist. Create? [y/n] (y): ValueError: I/O operation on closed file
```

With the directory pre-created the same call completes with no prompt at all
(six notebooks and a `data/` tree), so this one branch is the only thing
standing between `cellpy new` and being scriptable.

### Acceptance criteria

- When `no_input` is true and the project directory does not exist, create it
  without prompting (the prompt's own default is already `"yes"`, so behaviour
  for interactive users is unchanged).
- `create_project(..., no_input=True)` completes with `sys.stdin` closed and
  creates the project.
- A test in `tests/test_cli_api.py`, following the monkeypatch pattern of
  `test_create_project_returns_when_cookiecutter_missing`, asserts that
  `read_user_yes_no` is not called when `no_input=True`.
- Interactive behaviour (`no_input=False`) unchanged.

Found while prototyping an MCP server for cellpy (#840), which currently works
around it by creating the directory itself.
