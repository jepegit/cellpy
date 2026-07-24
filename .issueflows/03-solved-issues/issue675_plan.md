# Issue #675 plan

## Goal

Pin `cellpycore` to the new PyPI release `0.2.4`.

## Approach

1. Bump `"cellpycore==0.2.3"` → `"cellpycore==0.2.4"` in `pyproject.toml`.
2. Regenerate lock with `UV_NO_SOURCES=1 uv lock` (no path override).
3. Smoke with `uv sync --no-sources` + `pytest -m essential`.

## Files to touch

- `pyproject.toml`
- `uv.lock`
- `HISTORY.md` (close step)

## Test strategy

`uv run pytest -m essential` (PR merge gate).
