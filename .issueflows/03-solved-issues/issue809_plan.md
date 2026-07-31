# Issue #809 — Plan: add issue-flow as a dev dependency

Status: **confirmed** (yolo consolidated confirm, 2026-07-31).

## Goal

Make the `issue-flow` CLI available after a normal `uv sync` (dev group) so cloud agents and local contributors do not need a separate `uv tool install`.

## Approach

1. Add PyPI package `issue-flow` to `[dependency-groups].dev` in `pyproject.toml` and regenerate `uv.lock`.
2. Document one line in `CONTRIBUTING.md` (Get Started) that `uv run issue-flow …` works after sync.
3. No runtime import of issue-flow from `cellpy` code; CLI-only.

## Files to touch

| Path | Change |
| --- | --- |
| `pyproject.toml` | `issue-flow` in `dependency-groups.dev` |
| `uv.lock` | lock update |
| `CONTRIBUTING.md` | one-line note under Get Started |

## Test strategy

```bash
uv sync
uv run issue-flow --help   # or `issue-flow --version` via uv run
MPLBACKEND=Agg uv run pytest -m essential
```

## Open questions

None — scope is small and yolo-fit.
