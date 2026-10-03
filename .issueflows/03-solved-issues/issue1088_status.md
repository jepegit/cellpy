# Issue #1088 status

- [x] Done

## What's done

- MCP `load_cell` accepts optional `nominal_capacity` (number or unit string)
  and forwards it to `cellpy.get`. Result includes applied value +
  `nominal_capacity_was_supplied`.
- Tests in `cellpy-mcp` (`test_cell_tools.py`): forward, omit, string-with-unit.
- README tool row updated.

## Remaining work

None.
