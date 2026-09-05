# Issue #991: Add cli_api.list_templates() returning the batch templates as data

Source: https://github.com/jepegit/cellpy/issues/991

## Original issue text

`cellpy new --list` prints the available templates through the UI and returns
nothing, so any non-CLI caller — a GUI, a script, an MCP tool — has to reach
into `cellpy.utils.template_registry.REGISTERED_TEMPLATES` plus the private
`cli_api._get_default_template()` and `cli_api._read_local_templates()` to
offer the same choice.

Every other `cellpy new` capability already has a library form
(`cli_api.create_project`); listing is the one that does not.

### Acceptance criteria

- Add `cli_api.list_templates()` returning the templates as data, e.g.

  ```python
  {
      "default": "standard",
      "registered": {"standard": "<location>", "ife": "...", "single": "..."},
      "local": {},                       # from config.paths.templatedir
      "templatedir": "/path/to/templates",
  }
  ```

  Exact key names are open to preference; the requirement is that a caller can
  name every template, say which is the default, and distinguish registered
  from local without importing a private helper.
- The `list_` branch of `_new()` renders its output from that return value, so
  the printed listing and the data cannot drift apart.
- `cellpy new --list` output is unchanged.
- A test in `tests/test_cli_api.py` asserting the returned shape and that the
  default appears among the registered templates.

Found while prototyping an MCP server for cellpy (#840), whose `list_templates`
tool currently reads the registry and two private helpers directly. Related:
#990.
