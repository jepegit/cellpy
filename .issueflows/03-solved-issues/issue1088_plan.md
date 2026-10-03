# Issue #1088 plan

## Goal

MCP `load_cell(..., mass_mg=2.1, nominal_capacity=320)` reaches `cellpy.get`;
omitting `nominal_capacity` leaves cellpy’s default. Return the applied value
and a supplied flag (mirror `mass_was_supplied`).

## Constraints

- Two repos: tool + tests in `cellpy-mcp`; tracker / HISTORY on `jepegit/cellpy`.
- Same units story as `cellpy.get`: number → cellpy units; string may carry a unit.
- Do not default a lab-looking capacity.
- No finder work.

### Prior art

- MCP `load_cell` already forwards `mass_mg` → `cellpy.get(mass=)` and returns
  `mass_mg` / `mass_was_supplied` (`cellpy_mcp/cells.py`).
- `cellpy.get(..., nominal_capacity=)` (`cellreader.get`); applied value is
  `cell.nominal_capacity`.
- `tests/test_cell_tools.py` `drive` harness + monkeypatch pattern from #1080.

## Approach

1. Add optional `nominal_capacity: float | str | None = None` on MCP `load_cell`.
2. If set, pass `nominal_capacity=` through to `cellpy.get`.
3. Return `nominal_capacity` (from `cell.nominal_capacity`) and
   `nominal_capacity_was_supplied`.
4. Tests in cellpy-mcp monkeypatch `cellpy.get` so they do not need a live load
   for the forward/omit cases. String-with-unit forwarded as-is.
5. One-line README / cellpy HISTORY; no finder or Scenario 2 dialogue.

## Files to touch

- `cellpy-mcp/src/cellpy_mcp/cells.py` — parameter + kwargs + result keys
- `cellpy-mcp/tests/test_cell_tools.py` — forward / omit / string
- `cellpy-mcp/README.md` — `load_cell` row mentions nom_cap
- `cellpy/HISTORY.md` (close)

## Test strategy

- cellpy-mcp: `uv run pytest`
- cellpy: `uv run pytest -m essential` (no library change)

## Open questions

None.
