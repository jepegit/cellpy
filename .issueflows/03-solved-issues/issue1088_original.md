# Issue #1088: Pass nominal_capacity through MCP load_cell

Source: https://github.com/jepegit/cellpy/issues/1088

## Original issue text

## Context

Part of epic #1074 (agent summary-plots SAL cells 10–15 from local files). Stage 3 Scenario 2: after a confirm-gated raw search, the user gives mass ≈ 2.1 mg and nominal capacity ≈ 320 mAh/g. `cellpy.get` already accepts `nominal_capacity`. MCP `load_cell` only forwards `mass_mg`.

## Scope

Add an optional `nominal_capacity` on MCP `load_cell` and pass it through as `nominal_capacity=` with the same units story as `cellpy.get`: a number uses cellpy units, a string may carry a unit. Return the applied value and whether it was supplied (mirror `mass_was_supplied`). Do not default a lab-looking capacity.

Tests in cellpy-mcp. No finder work.

## Acceptance criteria

- `load_cell(..., mass_mg=2.1, nominal_capacity=320)` reaches `cellpy.get`.
- Omitting it leaves cellpy’s default.

Goal: `load_cell(..., mass_mg=2.1, nominal_capacity=320)` reaches `cellpy.get`; omitting it leaves cellpy’s default.

Model: fast

Depends on: none

Part of epic #1074.
